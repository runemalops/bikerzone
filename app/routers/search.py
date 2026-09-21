from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.database import get_db
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.moto import Moto
from app.models.orden_servicio import OrdenServicio
from app.models.repuesto import Repuesto
from app.models.proveedor import Proveedor
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api", tags=["search"])

TYPE_LIMIT = 5
TOTAL_LIMIT = 12


@router.get("/search")
def search(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    results = []

    # --- Clientes ---
    clientes = (
        db.query(Cliente)
        .filter(
            or_(
                Cliente.nombre.ilike(f"%{q}%"),
                Cliente.email.ilike(f"%{q}%"),
                Cliente.telefono.ilike(f"%{q}%"),
            )
        )
        .limit(TYPE_LIMIT)
        .all()
    )

    for c in clientes:
        subtitle_parts = []
        if c.email:
            subtitle_parts.append(c.email)
        if c.telefono:
            subtitle_parts.append(c.telefono)
        results.append(
            {
                "type": "cliente",
                "title": c.nombre,
                "subtitle": " | ".join(subtitle_parts) if subtitle_parts else "Sin contacto",
                "url": f"/clientes/{c.id}",
            }
        )

    # --- Motos (with client name) ---
    motos = (
        db.query(Moto)
        .options(joinedload(Moto.cliente))
        .filter(
            or_(
                Moto.marca.ilike(f"%{q}%"),
                Moto.modelo.ilike(f"%{q}%"),
                Moto.placa.ilike(f"%{q}%"),
                Moto.vin.ilike(f"%{q}%"),
            )
        )
        .limit(TYPE_LIMIT)
        .all()
    )

    for m in motos:
        client_name = m.cliente.nombre if m.cliente else "Sin cliente"
        subtitle = f"{m.placa or 'S/N'} — {client_name}"
        results.append(
            {
                "type": "moto",
                "title": f"{m.marca} {m.modelo}",
                "subtitle": subtitle,
                "url": f"/motos/{m.id}",
            }
        )

    # --- Ordenes de Servicio (with client name) ---
    ordenes = (
        db.query(OrdenServicio)
        .options(joinedload(OrdenServicio.cliente))
        .filter(
            or_(
                OrdenServicio.codigo.ilike(f"%{q}%"),
                OrdenServicio.falla_reportada.ilike(f"%{q}%"),
            )
        )
        .limit(TYPE_LIMIT)
        .all()
    )

    for o in ordenes:
        client_name = o.cliente.nombre if o.cliente else ""
        subtitle = o.falla_reportada[:50] if o.falla_reportada else o.estado
        if client_name:
            subtitle = f"{client_name} — {subtitle}"
        results.append(
            {
                "type": "orden",
                "title": f"Orden #{o.codigo}",
                "subtitle": subtitle,
                "url": f"/ordenes/{o.codigo}",
            }
        )

    # --- Repuestos ---
    repuestos = (
        db.query(Repuesto)
        .filter(
            or_(
                Repuesto.nombre.ilike(f"%{q}%"),
                Repuesto.codigo.ilike(f"%{q}%"),
                Repuesto.marca.ilike(f"%{q}%"),
            )
        )
        .limit(TYPE_LIMIT)
        .all()
    )

    for r in repuestos:
        stock_info = f"Stock: {r.stock_actual}"
        results.append(
            {
                "type": "repuesto",
                "title": r.nombre,
                "subtitle": f"{r.codigo} — {stock_info}",
                "url": f"/repuestos/{r.id}",
            }
        )

    # --- Proveedores ---
    proveedores = (
        db.query(Proveedor)
        .filter(
            or_(
                Proveedor.nombre.ilike(f"%{q}%"),
                Proveedor.contacto.ilike(f"%{q}%"),
                Proveedor.email.ilike(f"%{q}%"),
                Proveedor.telefono.ilike(f"%{q}%"),
            )
        )
        .limit(TYPE_LIMIT)
        .all()
    )

    for p in proveedores:
        subtitle_parts = []
        if p.contacto:
            subtitle_parts.append(p.contacto)
        if p.telefono:
            subtitle_parts.append(p.telefono)
        results.append(
            {
                "type": "proveedor",
                "title": p.nombre,
                "subtitle": " | ".join(subtitle_parts) if subtitle_parts else p.email or "Sin contacto",
                "url": f"/proveedores/{p.id}",
            }
        )

    return {"results": results[:TOTAL_LIMIT]}
