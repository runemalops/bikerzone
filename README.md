# BikerZone

Sistema de gestion para taller de motocicletas.

## Caracteristicas

- Gestion de clientes y motocicletas
- Ordenes de servicio con flujo de estados
- Inventario de repuestos con alertas de stock minimo
- Ordenes de compra a proveedores
- Reportes de ventas, inventario, compras y productividad
- API REST completa
- Dashboard interactivo con Chart.js
- Diseno responsive para movil
- Dark/Light mode
- Notificaciones automaticas (email SMTP y Telegram)
- Panel de servicio preventivo con reprogramacion por kilometraje

## Requisitos

- [Docker](https://www.docker.com/products/docker-desktop/) instalado
- Docker Compose v2 (`docker compose`)

## Inicio rapido (desarrollo)

```bash
# Clonar y entrar al directorio
cd bikerzone
# Levantar servicios
docker compose up -d

# Poblar datos demo (opcional)
docker compose exec web python -m services.seed

# Acceder
# Web: http://localhost:8001
# API Docs: http://localhost:8001/docs (solo desarrollo)
```

## Credenciales por defecto (solo desarrollo)

| Usuario | Email | Contrasena | Rol |
|---------|-------|------------|-----|
| Admin | admin@bikerzone.com | admin123 | admin |

> En produccion **debes** cambiar `ADMIN_PASSWORD` y no usar el valor por defecto.

## Testing

```bash
# Dentro del contenedor (recomendado)
docker compose exec web python -m pytest tests/ -q

# O en el host si tienes las dependencias instaladas
python -m pytest tests/ -q
```

Asegurese de que la base de datos de prueba este limpia si hay errores de SQLite (`rm -f test.db`).

## Desarrollo

```bash
# Ver logs
docker compose logs -f web

# Parar servicios
docker compose down

# Parar y borrar base de datos
docker compose down -v
```

---

## Implementacion en produccion

Guia paso a paso para desplegar BikerZone en un servidor con Docker Compose (perfil `docker-compose.prod.yml`).

### Arquitectura

| Servicio | Expuesto | Descripcion |
|----------|----------|-------------|
| nginx | `:80` y `:443` | Reverse proxy, estaticos, TLS |
| web | `127.0.0.1:8000` (interno) | FastAPI + Uvicorn (4 workers) |
| db | `127.0.0.1:5432` (interno) | PostgreSQL 16 con volumen persistente |

### 1. Preparar el servidor

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 git

# Clonar el repositorio
git clone https://github.com/runemalops/bikerzone.git
cd bikerzone
```

### 2. Generar tokens y secretos

#### SECRET_KEY (obligatorio)

Firma los tokens JWT de sesion. Si no se configura, cada reinicio invalida todas las sesiones.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# Ejemplo de salida:
# 9f2c8a1e4b7d6f0a3c5e8b1d4f7a0c2e5b8d1f4a7c0e3b6d9f2a5c8e1b4d7f0a
```

#### ADMIN_PASSWORD (obligatorio)

Contrasena del admin inicial (se crea solo la primera vez):

```bash
# Generar una contrasena fuerte (min 8, mayuscula, minuscula, digito)
python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16)))"
```

#### TELEGRAM_BOT_TOKEN (opcional, para notificaciones Telegram)

1. En Telegram, habla con **@BotFather**.
2. Envia `/newbot`.
3. Elige nombre y username (debe terminar en `bot`, ej. `bikerzone_taller_bot`).
4. BotFather responde con el token:

```
123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
```

5. Copia ese valor a `TELEGRAM_BOT_TOKEN` en `.env`.
6. El cliente (o tu) debe **iniciar chat** con el bot y enviar `/start`. El `chat_id` se obtiene con:

```bash
curl -s "https://api.telegram.org/bot<TU_TOKEN>/getUpdates" | python3 -m json.tool
# Busca result[0].message.chat.id
```

Ese `chat_id` se guarda en el perfil del cliente en la app (campo Telegram del cliente).

#### SMTP con Gmail (runemalops@gmail.com)

Gmail **no** acepta la contrasena normal de Google. Debes crear una **App Password**:

1. Activa **Verificacion en 2 pasos** en la cuenta Google:
   https://myaccount.google.com/security
2. Genera una contrasena de aplicacion:
   https://myaccount.google.com/apppasswords
   - Nombre: `bikerzone-smtp`
   - Google devuelve una contrasena de **16 caracteres** (ej. `abcd efgh ijkl mnop`).
3. Usa esos 16 caracteres **sin espacios** como `SMTP_PASSWORD`.

Valores para `runemalops@gmail.com`:

| Variable | Valor |
|----------|-------|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | `runemalops@gmail.com` |
| `SMTP_PASSWORD` | `<app-password-de-16-digitos>` |
| `SMTP_FROM` | `BikerZone <runemalops@gmail.com>` |
| `SMTP_USE_TLS` | `true` |

### 3. Crear el archivo `.env`

```bash
cp .env.example .env
chmod 600 .env   # solo el dueño puede leerlo
nano .env        # o vim .env
```

Ejemplo completo de `.env` de produccion:

```bash
# --- Base de datos ---
DB_NAME=bikerzone
DB_USER=bikerzone_user
DB_PASSWORD=<genera-una-password-larga-y-unica>
DB_HOST=db          # nombre del servicio en compose, NO localhost
DB_PORT=5432

# --- Seguridad ---
# python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<64-hex-digitos-generados-arriba>
ADMIN_EMAIL=admin@bikerzone.com
ADMIN_PASSWORD=<contrasena-fuerte-generada-arriba>
ENVIRONMENT=production

# --- Moneda / impuestos ---
CURRENCY_SYMBOL=Q
CURRENCY_CODE=GTQ
CURRENCY_DECIMALS=2
IVA_RATE=0.12

# --- SMTP Gmail (runemalops@gmail.com) ---
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=runemalops@gmail.com
SMTP_PASSWORD=<app-password-16-digitos-sin-espacios>
SMTP_FROM=BikerZone <runemalops@gmail.com>
SMTP_USE_TLS=true

# --- Telegram (opcional) ---
TELEGRAM_BOT_TOKEN=<token-de-BotFather>
```

> **Nunca** comitees `.env` al repositorio. Ya esta en `.gitignore`.

### 4. Desplegar

```bash
# Build e inicio
docker compose -f docker-compose.prod.yml up -d --build

# Esperar a que la DB este healthy
docker compose -f docker-compose.prod.yml ps

# Migraciones (si usas Alembic)
docker compose -f docker-compose.prod.yml exec web python -m alembic upgrade head

# Verificar salud
curl -s http://127.0.0.1:8000/health
# {"status":"ok","version":"2.0.0"}
```

O usa el script:

```bash
./scripts/deploy.sh
```

### 5. HTTPS con certbot (recomendado)

```bash
# Certificado wildcard o por dominio
sudo apt-get install -y certbot
sudo certbot certonly --standalone -d taller.ejemplo.com

# Copiar certificados al volumen de nginx
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/taller.ejemplo.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/taller.ejemplo.com/privkey.pem nginx/ssl/
```

Agrega un bloque `server` de `:443` en `nginx/default.conf` (o usa un archivo aparte) y reinicia:

```bash
docker compose -f docker-compose.prod.yml restart nginx
```

### 6. Verificar notificaciones

1. Entra a **Configuracion** en la app.
2. En *Notificaciones y Preventivo* debe decir:
   - SMTP: **configurado** (verde)
   - Bot: **configurado** (verde)
3. Activa *Enviar Email automatico* / *Enviar Telegram automatico* y guarda.
4. Prueba manualmente desde el panel **Preventivo** (boton Email/Telegram en una fila) o marcando una orden como **Lista**.

Si SMTP falla, revisa:

```bash
docker compose -f docker-compose.prod.yml logs web | grep -i smtp
```

### 7. Copias de seguridad

`scripts/backup.sh` genera un dump de PostgreSQL **con validacion de datos** y verifica que el archivo sea restaurable antes de dar por bueno el backup.

#### Qué valida

| Fase | Chequeo |
|------|---------|
| Origen | Las 13 tablas requeridas existen |
| Origen | `users` tiene filas (admin presente), `alembic_version` = 1 revision |
| Origen | Campos NOT NULL criticos (emails, codigos de orden, nombres, etc.) |
| Origen | Integridad referencial: sin huerfanos en FKs de motos, ordenes, repuestos, OC, notificaciones |
| Origen | Reglas basicas: kilometraje/stock/cantidades no negativos |
| Archivo | Dump no vacio, `gzip -t` integro, checksum SHA-256 |
| Restauracion | Restaura en una BD temporal `bikerzone_verify_<fecha>` |
| Restauracion | Re-ejecuta todas las validaciones sobre el restaurado |
| Restauracion | Compara recuentos de filas: origen == restaurado |

Si el origen tiene datos invalidos, el script **no** crea el dump y sale con codigo 2 (usa `--force` para respaldar de todos modos). Si la verificacion de restauracion falla, el archivo se renombra a `*.failed` y sale con codigo 1.

#### Uso

```bash
# Desarrollo (docker-compose.yml)
./scripts/backup.sh

# Produccion (docker-compose.prod.yml)
COMPOSE_FILE=docker-compose.prod.yml ./scripts/backup.sh

# Mas rapido: omite restaurar en BD temporal
./scripts/backup.sh --no-restore-verify

# Respaldar aunque el origen tenga fallos de validacion
./scripts/backup.sh --force
```

#### Nombre del backup (fecha y hora)

```
backups/bikerzone_AAAAMMDD_HHMMSS.sql.gz
backups/bikerzone_AAAAMMDD_HHMMSS.sql.gz.sha256
```

Ejemplo: `backups/bikerzone_20260923_225516.sql.gz` (23 sep 2026, 22:55:16).

#### Codigo de salida

| Codigo | Significado |
|--------|-------------|
| `0` | Backup creado y todas las validaciones OK |
| `1` | Error de dump, o verificacion de restauracion fallida (`*.failed`) |
| `2` | Datos invalidos en el origen (sin `--force` no hay dump; con `--force` si) |

#### Restaurar

```bash
COMPOSE_FILE=docker-compose.prod.yml ./scripts/restore.sh backups/bikerzone_AAAAMMDD_HHMMSS.sql.gz
```

#### Programar con cron (diario 03:00)

```bash
crontab -e
```

```cron
0 3 * * * cd /ruta/a/bikerzone && COMPOSE_FILE=docker-compose.prod.yml ./scripts/backup.sh >> backups/backup.log 2>&1
```

Los backups se conservan automaticamente (ultimos 7 por defecto; cambia `KEEP_BACKUPS=14`). El directorio `backups/` esta en `.gitignore`.

### 8. Actualizaciones

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python -m alembic upgrade head
```

### Checklist de produccion

- [ ] `SECRET_KEY` generado (no el valor por defecto)
- [ ] `ADMIN_PASSWORD` fuerte y distinto de `admin123`
- [ ] `DB_PASSWORD` unica
- [ ] `.env` con permisos `600` y **no** en git
- [ ] `ENVIRONMENT=production` (desactiva `/docs`)
- [ ] SMTP configurado y probado (o desactivado a proposito)
- [ ] Certificado TLS activo en nginx
- [ ] Backup programado y probado (cron con `scripts/backup.sh`, exit 0)
- [ ] Puerto 5432 y 8000 **no** expuestos a Internet (solo `127.0.0.1`)

---

## Stack

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy
- **DB:** PostgreSQL 16
- **Frontend:** Jinja2 + HTML/CSS/JS + Chart.js
- **Infra:** Docker + Docker Compose + nginx

## Licencia

MIT
