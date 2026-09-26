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

## Credenciales

| Usuario | Email | Contrasena | Rol |
|---------|-------|------------|-----|
| Admin | admin@bikerzone.com | `Biker_2026` (demo actual) | admin |
| Tecnico 1 | tecnico1@bikerzone.com | tecnico123 | tecnico |
| Tecnico 2 | tecnico2@bikerzone.com | tecnico123 | tecnico |

Los tecnicos los crea `services.seed`; el admin usa `ADMIN_EMAIL` /
`ADMIN_PASSWORD` del `.env`.

> **Ojo con `ADMIN_PASSWORD`:** `app/config.py` descarta los valores inseguros.
> Si `.env` tiene `ADMIN_PASSWORD=admin123` o **vacio**, `settings.ADMIN_PASSWORD`
> queda en `""` y el admin se crea **sin contrasena** (cualquiera entra dejando
> el campo en blanco). Pon siempre un valor propio distinto de `admin123` y
> recrea el contenedor: `docker compose -f docker-compose.prod.yml up -d`
> (un `restart` **no** recarga las variables de entorno).

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
| nginx | `0.0.0.0:80` y `0.0.0.0:443` | Reverse proxy, estaticos, TLS |
| web | `127.0.0.1:8000` (interno) | FastAPI + Uvicorn (4 workers) |
| db | `127.0.0.1:5432` (interno) | PostgreSQL 16 con volumen persistente |

Esta es la configuracion **original** y es la que usa `docker-compose.prod.yml`
por si solo: sirve para desplegar en cualquier servidor limpio.

> Si el servidor ya tiene otro proxy dueño del puerto 80 (traefik,
> nginx-proxy-manager, apache...), **no edites** `docker-compose.prod.yml`:
> usa la variante de la seccion **10. Variante con traefik (opcional)**, al
> final de esta guia. En ese servidor los puertos propios pasan a ser
> `8088` (nginx), `8000` (web) y `5434` (db).

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

#### 4.0 Verificar puertos libres (obligatorio)

La configuracion original necesita `80`, `443`, `8000` y `5432`. Antes de
levantar, confirma que esten libres:

```bash
# Puertos que BikerZone necesita
ss -ltn | grep -E ':(80|443|8000|5432)[[:space:]]' || echo "puertos libres"

# Que contenedores los estan usando
docker ps --filter publish=80 --filter publish=443 \
  --filter publish=8000 --filter publish=5432 --format 'table {{.Names}}\t{{.Ports}}'
```

- **Todo libre** → continua con `4.1` (configuracion original).
- **Alguien ocupa el 80/443** (traefik, nginx-proxy-manager, apache2, nginx del
  homelab...) → **no fuerces** el puerto: usa la variante de la seccion **10**
  con `docker-compose.traefik.yml`.
- Si aparece un contenedor `bikerzone-nginx-1` o `bikerzone-db-1` en estado
  `Created` (intento fallido), limpialo:

```bash
docker compose -f docker-compose.prod.yml down
```

#### 4.1 Build e inicio

```bash
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

#### 4.2 Preparar la base de datos para la demo

**Opcion A (la actual): BD limpia, flujo completo desde cero**

Solo quedan los **usuarios de acceso** (admin + 2 tecnicos), la configuracion
del sitio y la version de alembic. Clientes, motos, ordenes, repuestos,
proveedores y compras quedan en **0**, con los IDs reiniciados: es la ideal para
mostrar el flujo completo en vivo (cliente -> moto -> orden -> repuestos ->
cotizacion -> orden de compra).

```bash
# Backup previo (obligatorio si hay datos reales)
COMPOSE_FILE=docker-compose.prod.yml ./scripts/backup.sh

# Limpiar todo menos usuarios / site_config / alembic_version
docker compose -f docker-compose.prod.yml exec -T db psql -U bikerzone_user -d bikerzone <<'SQL'
TRUNCATE TABLE
  order_parts, purchase_order_items, status_history, notifications,
  service_orders, purchase_orders, parts, suppliers, motorcycles, clients
RESTART IDENTITY CASCADE;
SQL

# Verificar: users 3, site_config 1, resto 0
docker compose -f docker-compose.prod.yml exec db psql -U bikerzone_user -d bikerzone -c "
select 'users' t, count(*) from users union all
select 'clients', count(*) from clients union all
select 'service_orders', count(*) from service_orders union all
select 'parts', count(*) from parts union all
select 'suppliers', count(*) from suppliers union all
select 'purchase_orders', count(*) from purchase_orders;"
```

**Opcion B: datos de ejemplo**

`services.seed` **borra y recrea** todas las tablas con datos de ejemplo:
3 usuarios (admin + 2 tecnicos), 10 clientes con motos, 20 ordenes de servicio,
30 repuestos, 5 proveedores y 5 ordenes de compra.

```bash
docker compose -f docker-compose.prod.yml exec web python -m services.seed

# Verificar
docker compose -f docker-compose.prod.yml exec web python -m alembic current   # 003 (head)
curl -s http://127.0.0.1:8000/health
```

Los correos de los clientes demo son ficticios (`*@email.com`) y no tienen
`telegram_chat_id`; si `notif_email_auto` esta activo, al cambiar el estado de
una orden se intentara enviar un email real. Para una presentacion, desactivalo
en **Configuracion** si no quieres que se dispare.

### 5. HTTPS con certbot

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

> En la **variante con traefik** (seccion 10) el 443 lo maneja el proxy frontal
> o Cloudflare, y este paso no aplica.

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

> Los backups/restauraciones usan `docker compose exec db`, asi que sirven tal
> cual con la variante traefik: no hacen falta mas `-f`.

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

> Si despliegas con la **variante traefik**, agrega el segundo `-f` en todos los
> comandos:
> `docker compose -f docker-compose.prod.yml -f docker-compose.traefik.yml up -d --build`

### 9. Problemas conocidos

#### Problema: `Bind for 0.0.0.0:80 failed: port is already allocated`

**Sintoma completo**

```
Error response from daemon: failed to set up container networking:
driver failed programming external connectivity on endpoint bikerzone-nginx-1:
Bind for 0.0.0.0:80 failed: port is already allocated
```

**Causa**: el puerto 80 del host ya esta ocupado por otro contenedor (p. ej.
`traefik` o `nginx-proxy-manager` de otro stack) o por un servicio del host
(`apache2`, `nginx`, `caddy`). El servicio `nginx` de BikerZone no puede
publicarlo, el `up` aborta y el contenedor queda en estado `Created`.

**Diagnostico**

```bash
docker ps --filter publish=80 --filter publish=443 --format 'table {{.Names}}\t{{.Ports}}'
sudo ss -ltnp | grep -E ':(80|443)[[:space:]]'
docker ps -a --filter name=bikerzone   # busca contenedores en Created/Exited
```

**Soluciones (elige solo una)**

| # | Cuando aplicarla | Accion |
|---|------------------|--------|
| A | BikerZone debe ser el sitio principal del puerto 80 | Mover el servicio que lo ocupa a otro puerto |
| B | Ya existe un proxy frontal y BikerZone va detras | Usar `docker-compose.traefik.yml` (variante, seccion 10) |
| C | Quieres reusar traefik / nginx-proxy-manager ya desplegados | No publicar puertos; que el proxy apunte a `web:8000` |

**Opcion A: liberar el puerto 80**

En el compose del servicio conflictivo cambia el mapeo (ej. `"80:80"` ->
`"8081:80"`) y recrealo:

```bash
docker compose -p <proyecto-conflictivo> up -d
# verifica
docker ps --filter publish=80 --format 'table {{.Names}}\t{{.Ports}}'
```

**Opcion B (la de este servidor): variante `docker-compose.traefik.yml`**

No se toca `docker-compose.prod.yml`; el override sobreescribe solo lo
necesario:

```yaml
services:
  db:
    ports: !override
      - "127.0.0.1:5434:5432"    # 5432 lo usa el postgres del homelab

  nginx:
    ports: !override
      - "8088:80"                # 80 y 443 quedan para traefik
    networks: !override
      default:
      web:
        aliases:
          - bikerzone            # traefik resuelve http://bikerzone:80

networks:
  web:
    external: true
    name: web_network
```

Se levanta con los dos archivos:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.traefik.yml up -d --build
```

`8443` se dejo fuera a proposito: lo usa nginx-proxy-manager. Detalle completo
en la **seccion 10. Variante con traefik**.

**Opcion C: entrar por el proxy existente**

Elimina el bloque `ports:` del servicio `nginx` en `docker-compose.prod.yml`
(queda solo en la red interna del compose) y configura el proxy del host para
que haga reverse proxy a `web:8000` (servicio `web`, puerto `8000`). Si no
necesitas el nginx interno, puedes omitirlo y apuntar el proxy directo a
`web:8000`.

**Recrear el stack despues de cualquier cambio**

```bash
docker compose -f docker-compose.prod.yml down      # limpia el contenedor Created
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

#### Problema: el stack de desarrollo y el de produccion se pisan

`docker-compose.yml` y `docker-compose.prod.yml` usan el mismo nombre de
proyecto (`bikerzone`), por lo que los contenedores comparten nombre. Usa
nombres distintos si necesitas ambos a la vez:

```bash
docker compose -p bikerzone-dev        -f docker-compose.yml        up -d
docker compose -p bikerzone-prod       -f docker-compose.prod.yml   up -d --build
```

#### Problema: `password authentication failed for user "bikerzone_user"`

**Sintoma**: `web` entra en loop y los logs terminan con

```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at "db" (...)
FATAL:  password authentication failed for user "bikerzone_user"
ERROR:    Application startup failed. Exiting.
```

**Causa**: `POSTGRES_PASSWORD` solo se aplica la **primera vez** que se crea el
volumen `db_data`. Si cambiaste `DB_PASSWORD` despues (o el volumen lo creo
otra password), el rol en la BD queda con la contraseña vieja y `web` no entra.

**Solucion** (no borra datos; alinea el rol con el `.env` actual):

```bash
PW=$(grep -E '^DB_PASSWORD=' .env | cut -d= -f2-)
docker exec -i bikerzone-db-1 psql -U bikerzone_user -d postgres \
  -c "ALTER USER bikerzone_user PASSWORD '$PW';"
docker compose -f docker-compose.prod.yml restart web
docker compose -f docker-compose.prod.yml logs --tail=5 web
```

Si preferis arrancar de cero (borra **todos** los datos): `docker compose -f
docker-compose.prod.yml down -v && docker compose -f docker-compose.prod.yml up -d --build`.

### 10. Variante con traefik (opcional)

Solo para servidores donde **ya existe** un proxy (traefik, nginx-proxy-manager)
dueño del puerto 80: es el caso de mi servidor personal / homelab, no de un
deploy de produccion limpio. La configuracion original (`docker-compose.prod.yml`
con 80/443 y 5432) **no se modifica**: se agrega un override.

#### 10.1 `docker-compose.traefik.yml`

```yaml
services:
  db:
    ports: !override
      - "127.0.0.1:5434:5432"

  nginx:
    ports: !override
      - "8088:80"
    networks: !override
      default:
      web:
        aliases:
          - bikerzone

networks:
  default:
  web:
    external: true
    name: web_network
```

- `!override` **reemplaza** la lista de puertos en vez de sumarla (si no,
  quedarian `80:80` y `8088:80` juntos y volviera el error de puertos).
- El alias `bikerzone` sobre la red externa `web_network` es lo que permite que
  traefik resuelva `http://bikerzone:80`.

#### 10.2 Desplegar con la variante

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.traefik.yml up -d --build
docker compose -f docker-compose.prod.yml -f docker-compose.traefik.yml ps

# Migraciones y salud (mismos comandos que la seccion 4.1)
docker compose -f docker-compose.prod.yml -f docker-compose.traefik.yml exec web python -m alembic upgrade head
curl -s http://127.0.0.1:8000/health
```

Puertos propios de esta variante: `8088` (nginx), `8000` (web), `5434` (db).

#### 10.3 Router en traefik

traefik del homelab usa **file provider** (no labels) y tiene `watch: true`,
asi que basta con crear el archivo (no hay que reiniciar traefik):

`docker_homelab/configs/traefik/dynamic/bikerzone.yml`

```yaml
http:
  routers:
    bikerzone:
      rule: "Host(`bikerzone.runemal.cloud`) || Host(`bikerzone.localhost`)"
      service: bikerzone
      entryPoints:
        - web

  services:
    bikerzone:
      loadBalancer:
        servers:
          - url: "http://bikerzone:80"
```

- **Interno:** `bikerzone.localhost` (y `http://127.0.0.1:8088` directo).
- **Externo:** `bikerzone.runemal.cloud` (registro DNS en Cloudflare, igual que
  `portainer.runemal.cloud` / `navidrome.runemal.cloud`; sin el registro solo
  funciona el acceso interno).

#### 10.4 Puertos ya ocupados en ese servidor

No reutilizar: `80`, `8080` (traefik), `81`, `8084`, `8443`
(nginx-proxy-manager), `8081` (nginx), `8082` (wordpress), `8083` (pihole),
`8085` (qbittorrent), `8086` (cadvisor), `5432` (postgres del homelab),
`8087` (nginx del stack de desarrollo), `9000` (portainer).

#### 10.5 Verificacion

```bash
curl -s http://127.0.0.1:8000/health                              # {"status":"ok",...}
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8088/login   # 200
curl -s -L -o /dev/null -w '%{http_code}\n' -H 'Host: bikerzone.localhost' http://127.0.0.1/   # 200
curl -s http://127.0.0.1:8080/api/http/routers | python3 -m json.tool   # bikerzone@file enabled
```

### Checklist de produccion

- [ ] Puertos `80`, `443`, `8000` y `5432` libres antes del `up -d --build`
- [ ] `SECRET_KEY` generado (no el valor por defecto)
- [ ] `ADMIN_PASSWORD` fuerte y distinto de `admin123` (si esta vacio, el admin
      se crea sin contrasena)
- [ ] `DB_PASSWORD` unica y **coincide** con el rol de la BD existente
- [ ] `.env` con permisos `600` y **no** en git
- [ ] `ENVIRONMENT=production` (desactiva `/docs`)
- [ ] SMTP configurado y probado (o desactivado a proposito)
- [ ] Certificado TLS activo en nginx (seccion 5)
- [ ] Backup programado y probado (cron con `scripts/backup.sh`, exit 0)
- [ ] `5432` y `8000` **no** expuestos a Internet (solo `127.0.0.1`)

Solo si usas la **variante traefik** (seccion 10):

- [ ] Despliegue con `-f docker-compose.prod.yml -f docker-compose.traefik.yml`
- [ ] Puertos `8088`, `8000` y `5434` libres (80/443 los usa traefik)
- [ ] Red externa `web_network` disponible y alias `bikerzone` en nginx
- [ ] `bikerzone.yml` en `configs/traefik/dynamic/` del homelab (router)
- [ ] Registro DNS `bikerzone.runemal.cloud` creado en Cloudflare


---

## Stack

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy
- **DB:** PostgreSQL 16
- **Frontend:** Jinja2 + HTML/CSS/JS + Chart.js
- **Infra:** Docker + Docker Compose + nginx

## Licencia

MIT
