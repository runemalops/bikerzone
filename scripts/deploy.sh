#!/bin/bash

set -e

echo "=== BikerZone Deployment ==="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ".env created. Please update with your settings."
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down

# Build and start
echo "Building and starting containers..."
docker-compose up -d --build

# Wait for DB
echo "Waiting for database..."
sleep 10

# Run migrations
echo "Running migrations..."
docker-compose exec web python -m alembic upgrade head

# Seed data (optional)
read -p "Load demo data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Seeding demo data..."
    docker-compose exec web python services/seed.py
fi

echo ""
echo "=== Deployment Complete ==="
echo "App: http://localhost"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Default credentials:"
echo "Email: admin@bikerzone.com"
echo "Password: admin123"
