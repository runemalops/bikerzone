from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.proveedor import Proveedor
from app.models.orden_compra import OrdenCompra
from app.schemas.proveedor import ProveedorCreate, ProveedorUpdate


def get_proveedores(
    db: Session,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[dict], int]:
    query = db.query(Proveedor).filter(Proveedor.activo == True)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Proveedor.nombre.ilike(search_filter)) |
            (Proveedor.contacto.ilike(search_filter)) |
            (Proveedor.telefono.ilike(search_filter)) |
            (Proveedor.email.ilike(search_filter))
        )

    total = query.count()
    proveedores = query.order_by(Proveedor.nombre).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    result = []
    for p in proveedores:
        ordenes_count = db.query(func.count(OrdenCompra.id)).filter(
            OrdenCompra.supplier_id == p.id
        ).scalar() or 0
        result.append({
            "id": p.id,
            "nombre": p.nombre,
            "contacto": p.contacto,
            "telefono": p.telefono,
            "email": p.email,
            "total_ordenes": ordenes_count,
        })

    return result, total


def get_proveedor(db: Session, proveedor_id: int) -> Optional[Proveedor]:
    return db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()


def create_proveedor(db: Session, data: ProveedorCreate) -> Proveedor:
    proveedor = Proveedor(**data.model_dump())
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


def update_proveedor(db: Session, proveedor_id: int, data: ProveedorUpdate) -> Optional[Proveedor]:
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(proveedor, key, value)

    db.commit()
    db.refresh(proveedor)
    return proveedor


def delete_proveedor(db: Session, proveedor_id: int) -> bool:
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        return False

    proveedor.activo = False
    db.commit()
    return True


def get_proveedor_ordenes(db: Session, proveedor_id: int) -> list:
    ordenes = db.query(OrdenCompra).filter(
        OrdenCompra.supplier_id == proveedor_id
    ).order_by(OrdenCompra.created_at.desc()).all()

    result = []
    for o in ordenes:
        result.append({
            "id": o.id,
            "codigo": o.codigo,
            "estado": o.estado,
            "total": float(o.total) if o.total else 0,
            "created_at": o.created_at,
        })

    return result
