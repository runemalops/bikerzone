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

## Requisitos

- [Docker](https://www.docker.com/products/docker-desktop/) instalado

## Inicio rapido

```bash
# Clonar y entrar al directorio
cd bikerzone_dev/bikerzone

# Levantar servicios
docker compose up -d

# Poblar datos demo (opcional)
docker compose exec web python -m services.seed

# Acceder
# Web: http://localhost
# API Docs: http://localhost:8000/docs (solo desarrollo)
```

## Credenciales por defecto

| Usuario | Email | Contrasena | Rol |
|---------|-------|------------|-----|
| Admin | admin@bikerzone.com | admin123 | admin |

## Desarrollo

```bash
# Ver logs
docker compose logs -f web

# Parar servicios
docker compose down

# Parar y borrar base de datos
docker compose down -v
```

## Stack

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy
- **DB:** PostgreSQL 16
- **Frontend:** Jinja2 + HTML/CSS/JS + Chart.js
- **Infra:** Docker + Docker Compose + nginx

## Licencia

MIT
