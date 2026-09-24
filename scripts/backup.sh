#!/usr/bin/env bash
# BikerZone - Backup de PostgreSQL con validacion de datos
#
# Uso:
#   ./scripts/backup.sh                  # dev (docker-compose.yml)
#   COMPOSE_FILE=docker-compose.prod.yml ./scripts/backup.sh   # produccion
#
# Opciones:
#   --no-restore-verify   Omite restaurar el dump en una BD temporal (mas rapido)
#   --force               Crea el backup aunque falle la validacion del origen
#
# Salida:
#   0 = backup creado y validaciones OK
#   1 = error (dump falllo o verificacion de restauracion fallida; el archivo
#       fallido se renombra a *.failed)
#   2 = datos invalidos en el origen (sin --force no se crea el dump;
#       con --force se crea y se reporta este codigo)
#
# Archivo: backups/bikerzone_YYYYMMDD_HHMMSS.sql.gz (+ .sha256)

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
KEEP_BACKUPS="${KEEP_BACKUPS:-7}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/bikerzone_${TIMESTAMP}.sql.gz"
SHA256_FILE="${BACKUP_FILE}.sha256"
VERIFY_DB="bikerzone_verify_${TIMESTAMP}"

RESTORE_VERIFY=1
FORCE=0

for arg in "$@"; do
    case "$arg" in
        --no-restore-verify) RESTORE_VERIFY=0 ;;
        --force) FORCE=1 ;;
        -h|--help)
            sed -n '2,16p' "$0"
            exit 0
            ;;
        *)
            echo "Opcion desconocida: $arg" >&2
            exit 1
            ;;
    esac
done

# --- Compose / credenciales -------------------------------------------------
if docker compose version >/dev/null 2>&1; then
    COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE=(docker-compose)
else
    echo "Error: Docker Compose no esta instalado" >&2
    exit 1
fi

env_get() {
    local key="$1" default="$2" val=""
    if [ -f .env ]; then
        val="$(grep -E "^${key}=" .env | tail -1 | cut -d= -f2- | sed -e "s/^['\"]//" -e "s/['\"]$//")"
    fi
    echo "${val:-$default}"
}

DB_NAME="$(env_get DB_NAME bikerzone)"
DB_USER="$(env_get DB_USER bikerzone_user)"

db_psql() {
    # $1 = database, resto = args de psql
    local db="$1"
    shift
    "${COMPOSE[@]}" -f "$COMPOSE_FILE" exec -T db \
        psql -U "$DB_USER" -d "$db" -v ON_ERROR_STOP=1 "$@"
}

db_sql() {
    local db="$1" sql="$2"
    db_psql "$db" -t -A -F$'\t' -c "$sql"
}

# --- Validacion de datos ----------------------------------------------------
# Imprime una linea por chequeo: OK <detalle> | FAIL <detalle>
# Devuelve el numero de fallos por stdout via variable global.
VALIDATION_SQL="$(cat <<'SQL'
-- 1) Tablas requeridas presentes
SELECT CASE WHEN t IS NULL THEN 'OK tablas_requeridas: 13/13'
            ELSE 'FAIL tabla_faltante: ' || t END
FROM (
    SELECT string_agg(x, ', ' ORDER BY x) AS t
    FROM unnest(ARRAY[
        'alembic_version','users','clients','motorcycles','service_orders',
        'order_parts','status_history','parts','suppliers','purchase_orders',
        'purchase_order_items','notifications','site_config'
    ]) AS x
    WHERE NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = x
    )
) s;

-- 2) Filas criticas
SELECT CASE WHEN n = 0 THEN 'FAIL users: 0 filas (debe existir al menos el admin)'
            ELSE 'OK users: ' || n || ' filas' END
FROM (SELECT count(*)::int AS n FROM users) u;

SELECT CASE WHEN n = 1 THEN 'OK alembic_version: 1 revision'
            ELSE 'FAIL alembic_version: ' || n || ' filas (esperado 1)' END
FROM (SELECT count(*)::int AS n FROM alembic_version) a;

SELECT CASE WHEN n <= 1 THEN 'OK site_config: ' || n || ' fila(s)'
            ELSE 'FAIL site_config: ' || n || ' filas (esperado 0 o 1)' END
FROM (SELECT count(*)::int AS n FROM site_config) c;

-- 3) Campos NOT NULL criticos
SELECT CASE WHEN n = 0 THEN 'OK users.not_null: email/password_hash completos'
            ELSE 'FAIL users.not_null: ' || n || ' fila(s) sin email o password_hash' END
FROM (SELECT count(*)::int AS n FROM users
      WHERE email IS NULL OR email = '' OR password_hash IS NULL OR password_hash = '') u;

SELECT CASE WHEN n = 0 THEN 'OK clients.not_null: nombre completo'
            ELSE 'FAIL clients.not_null: ' || n || ' fila(s) sin nombre' END
FROM (SELECT count(*)::int AS n FROM clients WHERE nombre IS NULL OR nombre = '') c;

SELECT CASE WHEN n = 0 THEN 'OK service_orders.not_null: codigo/cliente/moto/falla'
            ELSE 'FAIL service_orders.not_null: ' || n || ' fila(s) incompletas' END
FROM (SELECT count(*)::int AS n FROM service_orders
      WHERE codigo IS NULL OR codigo = ''
         OR client_id IS NULL OR motorcycle_id IS NULL
         OR falla_reportada IS NULL OR falla_reportada = '') s;

SELECT CASE WHEN n = 0 THEN 'OK parts.not_null: codigo/nombre'
            ELSE 'FAIL parts.not_null: ' || n || ' fila(s) incompletas' END
FROM (SELECT count(*)::int AS n FROM parts
      WHERE codigo IS NULL OR codigo = '' OR nombre IS NULL OR nombre = '') p;

SELECT CASE WHEN n = 0 THEN 'OK suppliers.not_null: nombre'
            ELSE 'FAIL suppliers.not_null: ' || n || ' fila(s) sin nombre' END
FROM (SELECT count(*)::int AS n FROM suppliers WHERE nombre IS NULL OR nombre = '') s;

SELECT CASE WHEN n = 0 THEN 'OK motorcycles.not_null: cliente/marca/modelo'
            ELSE 'FAIL motorcycles.not_null: ' || n || ' fila(s) incompletas' END
FROM (SELECT count(*)::int AS n FROM motorcycles
      WHERE client_id IS NULL OR marca IS NULL OR marca = ''
         OR modelo IS NULL OR modelo = '') m;

-- 4) Integridad referencial (huerfanos)
SELECT CASE WHEN n = 0 THEN 'OK fk_motorcycles.client_id'
            ELSE 'FAIL fk_motorcycles.client_id: ' || n || ' moto(s) sin cliente' END
FROM (SELECT count(*)::int AS n FROM motorcycles m
      LEFT JOIN clients c ON c.id = m.client_id WHERE c.id IS NULL) m;

SELECT CASE WHEN n = 0 THEN 'OK fk_service_orders.client_id'
            ELSE 'FAIL fk_service_orders.client_id: ' || n || ' orden(es) sin cliente' END
FROM (SELECT count(*)::int AS n FROM service_orders s
      LEFT JOIN clients c ON c.id = s.client_id WHERE c.id IS NULL) s;

SELECT CASE WHEN n = 0 THEN 'OK fk_service_orders.motorcycle_id'
            ELSE 'FAIL fk_service_orders.motorcycle_id: ' || n || ' orden(es) sin moto' END
FROM (SELECT count(*)::int AS n FROM service_orders s
      LEFT JOIN motorcycles m ON m.id = s.motorcycle_id WHERE m.id IS NULL) s;

SELECT CASE WHEN n = 0 THEN 'OK fk_service_orders.technician_id'
            ELSE 'FAIL fk_service_orders.technician_id: ' || n || ' orden(es) con tecnico inexistente' END
FROM (SELECT count(*)::int AS n FROM service_orders s
      LEFT JOIN users u ON u.id = s.technician_id
      WHERE s.technician_id IS NOT NULL AND u.id IS NULL) s;

SELECT CASE WHEN n = 0 THEN 'OK fk_order_parts'
            ELSE 'FAIL fk_order_parts: ' || n || ' detalle(s) huerfano(s)' END
FROM (SELECT count(*)::int AS n FROM order_parts op
      LEFT JOIN service_orders s ON s.id = op.service_order_id
      LEFT JOIN parts p ON p.id = op.part_id
      WHERE s.id IS NULL OR p.id IS NULL) o;

SELECT CASE WHEN n = 0 THEN 'OK fk_status_history'
            ELSE 'FAIL fk_status_history: ' || n || ' entrada(s) huerfana(s)' END
FROM (SELECT count(*)::int AS n FROM status_history h
      LEFT JOIN service_orders s ON s.id = h.service_order_id
      LEFT JOIN users u ON u.id = h.user_id
      WHERE s.id IS NULL OR (h.user_id IS NOT NULL AND u.id IS NULL)) h;

SELECT CASE WHEN n = 0 THEN 'OK fk_purchase_orders.supplier_id'
            ELSE 'FAIL fk_purchase_orders.supplier_id: ' || n || ' OC sin proveedor' END
FROM (SELECT count(*)::int AS n FROM purchase_orders po
      LEFT JOIN suppliers sp ON sp.id = po.supplier_id WHERE sp.id IS NULL) p;

SELECT CASE WHEN n = 0 THEN 'OK fk_purchase_order_items'
            ELSE 'FAIL fk_purchase_order_items: ' || n || ' detalle(s) huerfano(s)' END
FROM (SELECT count(*)::int AS n FROM purchase_order_items i
      LEFT JOIN purchase_orders po ON po.id = i.purchase_order_id
      LEFT JOIN parts p ON p.id = i.part_id
      WHERE po.id IS NULL OR p.id IS NULL) i;

SELECT CASE WHEN n = 0 THEN 'OK fk_notifications'
            ELSE 'FAIL fk_notifications: ' || n || ' notificacion(es) con referencia rota' END
FROM (SELECT count(*)::int AS n FROM notifications n
      LEFT JOIN service_orders s ON s.id = n.service_order_id
      LEFT JOIN motorcycles m ON m.id = n.motorcycle_id
      LEFT JOIN clients c ON c.id = n.cliente_id
      WHERE (n.service_order_id IS NOT NULL AND s.id IS NULL)
         OR (n.motorcycle_id IS NOT NULL AND m.id IS NULL)
         OR (n.cliente_id IS NOT NULL AND c.id IS NULL)) n;

-- 5) Reglas de negocio basicas
SELECT CASE WHEN n = 0 THEN 'OK motorcycles.kilometraje: sin negativos'
            ELSE 'FAIL motorcycles.kilometraje: ' || n || ' valor(es) negativo(s)' END
FROM (SELECT count(*)::int AS n FROM motorcycles WHERE kilometraje < 0) m;

SELECT CASE WHEN n = 0 THEN 'OK order_parts.cantidad: > 0'
            ELSE 'FAIL order_parts.cantidad: ' || n || ' cantidad(es) <= 0' END
FROM (SELECT count(*)::int AS n FROM order_parts WHERE cantidad <= 0) o;

SELECT CASE WHEN n = 0 THEN 'OK parts.stocks: sin negativos'
            ELSE 'FAIL parts.stocks: ' || n || ' stock(s) negativo(s)' END
FROM (SELECT count(*)::int AS n FROM parts
      WHERE stock_actual < 0 OR stock_reservado < 0) p;

-- 6) Recuento de filas (para comparar origen vs restaurado)
SELECT 'COUNT ' || t || ' ' || n FROM (
    SELECT 'users' AS t, count(*)::bigint AS n FROM users
    UNION ALL SELECT 'clients', count(*) FROM clients
    UNION ALL SELECT 'motorcycles', count(*) FROM motorcycles
    UNION ALL SELECT 'service_orders', count(*) FROM service_orders
    UNION ALL SELECT 'order_parts', count(*) FROM order_parts
    UNION ALL SELECT 'status_history', count(*) FROM status_history
    UNION ALL SELECT 'parts', count(*) FROM parts
    UNION ALL SELECT 'suppliers', count(*) FROM suppliers
    UNION ALL SELECT 'purchase_orders', count(*) FROM purchase_orders
    UNION ALL SELECT 'purchase_order_items', count(*) FROM purchase_order_items
    UNION ALL SELECT 'notifications', count(*) FROM notifications
    UNION ALL SELECT 'site_config', count(*) FROM site_config
    UNION ALL SELECT 'alembic_version', count(*) FROM alembic_version
) counts;
SQL
)"

run_validation() {
    local db="$1"
    local out fails=0
    out="$(db_sql "$db" "$VALIDATION_SQL")" || {
        echo "FAIL conexion/consulta en base $db" >&2
        return 1
    }
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        case "$line" in
            COUNT*) continue ;;
            FAIL*)  fails=$((fails + 1)); echo "  $line" ;;
            OK*)    echo "  $line" ;;
            *)      echo "  $line" ;;
        esac
    done <<< "$out"
    return "$fails"
}

get_counts() {
    db_sql "$1" \
        "SELECT t || ' ' || n FROM (
            SELECT 'users' AS t, count(*)::text AS n FROM users
            UNION ALL SELECT 'clients', count(*)::text FROM clients
            UNION ALL SELECT 'motorcycles', count(*)::text FROM motorcycles
            UNION ALL SELECT 'service_orders', count(*)::text FROM service_orders
            UNION ALL SELECT 'order_parts', count(*)::text FROM order_parts
            UNION ALL SELECT 'status_history', count(*)::text FROM status_history
            UNION ALL SELECT 'parts', count(*)::text FROM parts
            UNION ALL SELECT 'suppliers', count(*)::text FROM suppliers
            UNION ALL SELECT 'purchase_orders', count(*)::text FROM purchase_orders
            UNION ALL SELECT 'purchase_order_items', count(*)::text FROM purchase_order_items
            UNION ALL SELECT 'notifications', count(*)::text FROM notifications
            UNION ALL SELECT 'site_config', count(*)::text FROM site_config
            UNION ALL SELECT 'alembic_version', count(*)::text FROM alembic_version
        ) c ORDER BY t"
}

# --- Ejecucion --------------------------------------------------------------
echo "=== BikerZone Backup ==="
echo "Fecha/hora:  $(date '+%Y-%m-%d %H:%M:%S')"
echo "Compose:     $COMPOSE_FILE"
echo "Base:        $DB_NAME"
echo "Archivo:     $BACKUP_FILE"
echo ""

if ! "${COMPOSE[@]}" -f "$COMPOSE_FILE" exec -T db \
        pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
    echo "Error: PostgreSQL no responde en el servicio 'db'" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"

echo "[1/4] Validando datos en el origen..."
ORIGIN_FAILS=0
if run_validation "$DB_NAME"; then
    echo "  -> origen OK"
else
    ORIGIN_FAILS=$?
    echo "  -> origen con $ORIGIN_FAILS fallo(s)" >&2
    if [ "$FORCE" -eq 0 ]; then
        echo "Abortado (usa --force para respaldar de todos modos)." >&2
        exit 2
    fi
    echo "  -> continuando por --force" >&2
fi

ORIGIN_COUNTS="$(get_counts "$DB_NAME")"

echo "[2/4] Creando dump (pg_dump | gzip)..."
if ! "${COMPOSE[@]}" -f "$COMPOSE_FILE" exec -T db \
        pg_dump -U "$DB_USER" -d "$DB_NAME" --no-owner --no-privileges \
        | gzip -c > "$BACKUP_FILE"; then
    rm -f "$BACKUP_FILE"
    echo "Error: pg_dump fallo" >&2
    exit 1
fi

if [ ! -s "$BACKUP_FILE" ]; then
    rm -f "$BACKUP_FILE"
    echo "Error: el dump esta vacio" >&2
    exit 1
fi

SIZE="$(du -h "$BACKUP_FILE" | cut -f1)"
if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$BACKUP_FILE" > "$SHA256_FILE"
else
    shasum -a 256 "$BACKUP_FILE" > "$SHA256_FILE"
fi
echo "  -> $BACKUP_FILE ($SIZE)"
echo "  -> $SHA256_FILE"

echo "[3/4] Verificando integridad del archivo (gzip)..."
if ! gzip -t "$BACKUP_FILE"; then
    echo "Error: el dump gzip esta corrupto" >&2
    exit 1
fi
echo "  -> gzip OK"

VERIFY_FAILS=0
if [ "$RESTORE_VERIFY" -eq 1 ]; then
    echo "[4/4] Verificando restauracion en BD temporal ($VERIFY_DB)..."
    cleanup_verify() {
        "${COMPOSE[@]}" -f "$COMPOSE_FILE" exec -T db \
            psql -U "$DB_USER" -d postgres -c \
            "DROP DATABASE IF EXISTS $VERIFY_DB WITH (FORCE);" >/dev/null 2>&1 || true
    }
    trap cleanup_verify EXIT

    db_psql postgres -c "CREATE DATABASE $VERIFY_DB OWNER $DB_USER;" >/dev/null

    if ! gunzip -c "$BACKUP_FILE" | db_psql "$VERIFY_DB" -q >/dev/null; then
        echo "  -> FAIL restore: el dump no se puede restaurar" >&2
        VERIFY_FAILS=1
    else
        if run_validation "$VERIFY_DB"; then
            echo "  -> validacion del restaurado OK"
        else
            VERIFY_FAILS=$?
            echo "  -> validacion del restaurado: $VERIFY_FAILS fallo(s)" >&2
        fi

        RESTORED_COUNTS="$(get_counts "$VERIFY_DB")"
        if [ "$ORIGIN_COUNTS" = "$RESTORED_COUNTS" ]; then
            echo "  -> recuentos origen == restaurado"
        else
            echo "  -> FAIL recuentos no coinciden:" >&2
            diff <(echo "$ORIGIN_COUNTS") <(echo "$RESTORED_COUNTS") >&2 || true
            VERIFY_FAILS=$((VERIFY_FAILS + 1))
        fi
    fi

    cleanup_verify
    trap - EXIT
else
    echo "[4/4] Verificacion de restauracion omitida (--no-restore-verify)"
fi

echo "[bonus] Rotando backups (conservar ultimos $KEEP_BACKUPS)..."
ls -t "$BACKUP_DIR"/bikerzone_*.sql.gz 2>/dev/null | tail -n +$((KEEP_BACKUPS + 1)) | xargs -r rm -f
ls -t "$BACKUP_DIR"/bikerzone_*.sql.gz.sha256 2>/dev/null | tail -n +$((KEEP_BACKUPS + 1)) | xargs -r rm -f

echo ""
if [ "$VERIFY_FAILS" -gt 0 ]; then
    FAILED_FILE="${BACKUP_FILE}.failed"
    mv -f "$BACKUP_FILE" "$FAILED_FILE"
    rm -f "$SHA256_FILE"
    echo "=== VERIFICACION FALLIDA: dump renombrado a $FAILED_FILE ==="
    exit 1
fi
if [ "$ORIGIN_FAILS" -gt 0 ]; then
    echo "=== Backup creado con --force; origen tenia $ORIGIN_FAILS fallo(s) ==="
    exit 2
fi
echo "=== Backup OK: $BACKUP_FILE ==="
