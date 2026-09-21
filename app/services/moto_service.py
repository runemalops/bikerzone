from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.moto import Moto
from app.models.cliente import Cliente
from app.models.orden_servicio import OrdenServicio
from app.schemas.moto import MotoCreate, MotoUpdate


def get_motos(
    db: Session,
    search: Optional[str] = None,
    client_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 20
) -> Tuple[List[dict], int]:
    query = db.query(Moto).join(Cliente)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Moto.marca.ilike(search_filter)) |
            (Moto.modelo.ilike(search_filter)) |
            (Moto.placa.ilike(search_filter)) |
            (Cliente.nombre.ilike(search_filter))
        )

    if client_id:
        query = query.filter(Moto.client_id == client_id)

    total = query.count()
    motos = query.offset((page - 1) * per_page).limit(per_page).all()

    result = []
    for m in motos:
        ordenes_count = db.query(func.count(OrdenServicio.id)).filter(
            OrdenServicio.motorcycle_id == m.id
        ).scalar() or 0
        result.append({
            "id": m.id,
            "marca": m.marca,
            "modelo": m.modelo,
            "anio": m.anio,
            "placa": m.placa,
            "color": m.color,
            "kilometraje": m.kilometraje,
            "cliente_nombre": m.cliente.nombre if m.cliente else "Sin cliente",
            "total_ordenes": ordenes_count,
        })

    return result, total


def get_moto(db: Session, moto_id: int) -> Optional[Moto]:
    return db.query(Moto).filter(Moto.id == moto_id).first()


def create_moto(db: Session, data: MotoCreate) -> Moto:
    moto = Moto(**data.model_dump())
    db.add(moto)
    db.commit()
    db.refresh(moto)
    return moto


def update_moto(db: Session, moto_id: int, data: MotoUpdate) -> Optional[Moto]:
    moto = db.query(Moto).filter(Moto.id == moto_id).first()
    if not moto:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(moto, key, value)

    db.commit()
    db.refresh(moto)
    return moto


def delete_moto(db: Session, moto_id: int) -> bool:
    moto = db.query(Moto).filter(Moto.id == moto_id).first()
    if not moto:
        return False

    any_orders = db.query(func.count(OrdenServicio.id)).filter(
        OrdenServicio.motorcycle_id == moto_id,
    ).scalar() or 0
    if any_orders > 0:
        return False

    db.delete(moto)
    db.commit()
    return True


def get_moto_ordenes(db: Session, moto_id: int) -> list:
    ordenes = db.query(OrdenServicio).filter(
        OrdenServicio.motorcycle_id == moto_id
    ).order_by(OrdenServicio.created_at.desc()).all()

    result = []
    for o in ordenes:
        result.append({
            "id": o.id,
            "codigo": o.codigo,
            "estado": o.estado,
            "falla_reportada": o.falla_reportada,
            "presupuesto": float(o.presupuesto) if o.presupuesto else None,
            "precio_final": float(o.precio_final) if o.precio_final else None,
            "created_at": o.created_at,
        })

    return result


def get_clientes_list(db: Session) -> list:
    return db.query(Cliente).order_by(Cliente.nombre).all()
