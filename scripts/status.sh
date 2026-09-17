#!/bin/bash

set -e

echo "=== BikerZone Status ==="
echo ""

# Docker status
echo "Docker Containers:"
docker-compose ps

echo ""

# DB status
echo "Database:"
docker-compose exec -T db pg_isready -U bikerzone_user -d bikerzone 2>/dev/null && echo "  Connected" || echo "  Disconnected"

echo ""

# App health
echo "App Health:"
curl -s http://localhost/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  App not responding"

echo ""

# Disk usage
echo "Disk Usage:"
docker system df

echo "=== End Status ==="
