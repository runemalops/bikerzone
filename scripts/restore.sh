#!/usr/bin/env bash
# BikerZone - Restaurar un backup creado con scripts/backup.sh
#
# Uso:
#   ./scripts/restore.sh backups/bikerzone_AAAAMMDD_HHMMSS.sql.gz
#   COMPOSE_FILE=docker-compose.prod.yml ./scripts/restore.sh <archivo>

set -euo pipefail

echo "=== BikerZone Restore ==="

if [ -z "${1:-}" ]; then
    echo "Usage: ./scripts/restore.sh <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh backups/*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

if ! gzip -t "$BACKUP_FILE" 2>/dev/null; then
    echo "Error: El archivo no es un gzip valido (corrupto?)" >&2
    exit 1
fi

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

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

echo "Compose: $COMPOSE_FILE"
echo "Database: $DB_NAME"
echo "Backup: $BACKUP_FILE"
echo ""
read -p "Are you sure? This will overwrite current data (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

echo "Dropping database..."
"${COMPOSE[@]}" -f "$COMPOSE_FILE" exec -T db \
    dropdb -U "$DB_USER" "$DB_NAME" --if-exists --force
echo "Creating database..."
"${COMPOSE[@]}" -f "$COMPOSE_FILE" exec -T db \
    createdb -U "$DB_USER" "$DB_NAME"

echo "Restoring backup..."
gunzip -c "$BACKUP_FILE" | "${COMPOSE[@]}" -f "$COMPOSE_FILE" exec -T db \
    psql -U "$DB_USER" -d "$DB_NAME" -q -v ON_ERROR_STOP=1

echo "=== Restore Complete ==="
