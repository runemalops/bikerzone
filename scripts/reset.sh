#!/bin/bash

set -e

echo "=== BikerZone - Full Reset ==="
echo ""
read -p "This will DELETE ALL DATA. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

# Stop containers
echo "Stopping containers..."
docker-compose down -v

# Remove volumes
echo "Removing volumes..."
docker volume rm bikerzone_db_data 2>/dev/null || true

# Start fresh
echo "Starting fresh deployment..."
docker-compose up -d --build

# Wait for DB
echo "Waiting for database..."
sleep 10

# Seed data
echo "Seeding demo data..."
docker-compose exec web python services/seed.py

echo ""
echo "=== Reset Complete ==="
echo "App: http://localhost"
echo ""
echo "Credentials:"
echo "Admin: admin@bikerzone.com / admin123"
echo "Tecnico: tecnico@bikerzone.com / tecnico123"
