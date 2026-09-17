#!/bin/bash

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bikerzone_$TIMESTAMP.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Load env vars
source .env 2>/dev/null || true

DB_NAME="${DB_NAME:-bikerzone}"
DB_USER="${DB_USER:-bikerzone_user}"
DB_PASSWORD="${DB_PASSWORD:-bikerzone}"

echo "=== BikerZone Backup ==="
echo "Database: $DB_NAME"
echo ""

# Backup
echo "Creating backup..."
docker-compose exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"

# Show result
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "Backup created: $BACKUP_FILE ($SIZE)"
else
    echo "Error: Backup failed"
    exit 1
fi

# Cleanup old backups (keep last 7)
echo "Cleaning old backups..."
ls -t "$BACKUP_DIR"/bikerzone_*.sql.gz | tail -n +8 | xargs -r rm --

echo "=== Backup Complete ==="
