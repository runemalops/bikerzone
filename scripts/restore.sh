#!/bin/bash

set -e

echo "=== BikerZone Restore ==="

if [ -z "$1" ]; then
    echo "Usage: ./scripts/restore.sh <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh backups/*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Load env vars
source .env 2>/dev/null || true

DB_NAME="${DB_NAME:-bikerzone}"
DB_USER="${DB_USER:-bikerzone_user}"

echo "Database: $DB_NAME"
echo "Backup: $BACKUP_FILE"
echo ""
read -p "Are you sure? This will overwrite current data (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

# Drop and recreate database
echo "Dropping database..."
docker-compose exec -T db dropdb -U "$DB_USER" "$DB_NAME" --if-exists
echo "Creating database..."
docker-compose exec -T db createdb -U "$DB_USER" "$DB_NAME"

# Restore
echo "Restoring backup..."
gunzip -c "$BACKUP_FILE" | docker-compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -q

echo "=== Restore Complete ==="
