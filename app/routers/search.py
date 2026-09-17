from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.cliente import Cliente
from app.models.moto import Moto
from app.models.orden_servicio import OrdenServicio
from app.models.repuesto import Repuesto

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
def search(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    results = []

    clientes = (
        db.query(Cliente)
        .filter(
            or_(
                Cliente.nombre.ilike(f"%{q}%"),
                Cliente.email.ilike(f"%{q}%"),
                Cliente.telefono.ilike(f"%{q}%"),
            )
        )
        .limit(5)
        .all()
    )

    for c in clientes:
        results.append(
            {
                "type": "cliente",
                "title": c.nombre,
                "subtitle": c.email or c.telefono or "Sin contacto",
                "url": f"/clientes/{c.id}",
            }
        )

    motos = (
        db.query(Moto)
        .filter(
            or_(
                Moto.marca.ilike(f"%{q}%"),
                Moto.modelo.ilike(f"%{q}%"),
                Moto.placa.ilike(f"%{q}%"),
                Moto.vin.ilike(f"%{q}%"),
            )
        )
        .limit(5)
        .all()
    )

    for m in motos:
        results.append(
            {
                "type": "moto",
                "title": f"{m.marca} {m.modelo}",
                "subtitle": f"Placa: {m.placa or 'N/A'}",
                "url": f"/motos/{m.id}",
            }
        )

    ordenes = (
        db.query(OrdenServicio)
        .filter(
            or_(
                OrdenServicio.codigo.ilike(f"%{q}%"),
                OrdenServicio.falla_reportada.ilike(f"%{q}%"),
            )
        )
        .limit(5)
        .all()
    )

    for o in ordenes:
        results.append(
            {
                "type": "orden",
                "title": f"Orden #{o.codigo}",
                "subtitle": o.falla_reportada[:50] if o.falla_reportada else o.estado,
                "url": f"/ordenes/{o.id}",
            }
        )

    repuestos = (
        db.query(Repuesto)
        .filter(
            or_(
                Repuesto.nombre.ilike(f"%{q}%"),
                Repuesto.codigo.ilike(f"%{q}%"),
            )
        )
        .limit(5)
        .all()
    )

    for r in repuestos:
        results.append(
            {
                "type": "repuesto",
                "title": r.nombre,
                "subtitle": f"Código: {r.codigo}",
                "url": f"/repuestos/{r.id}",
            }
        )

    return {"results": results[:10]}
