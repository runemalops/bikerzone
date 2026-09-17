from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.cliente import Cliente
from app.models.moto import Moto
from app.models.orden_servicio import OrdenServicio
from app.schemas.cliente import ClienteCreate, ClienteUpdate


def get_clientes(
    db: Session,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
) -> Tuple[List[dict], int]:
    query = db.query(Cliente)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Cliente.nombre.ilike(search_filter)) |
            (Cliente.telefono.ilike(search_filter)) |
            (Cliente.email.ilike(search_filter))
        )

    total = query.count()
    clientes = query.offset((page - 1) * per_page).limit(per_page).all()

    result = []
    for c in clientes:
        motos_count = db.query(func.count(Moto.id)).filter(Moto.client_id == c.id).scalar() or 0
        ordenes_count = db.query(func.count(OrdenServicio.id)).filter(OrdenServicio.client_id == c.id).scalar() or 0
        result.append({
            "id": c.id,
            "nombre": c.nombre,
            "telefono": c.telefono,
            "email": c.email,
            "total_motos": motos_count,
            "total_ordenes": ordenes_count,
        })

    return result, total


def get_cliente(db: Session, cliente_id: int) -> Optional[Cliente]:
    return db.query(Cliente).filter(Cliente.id == cliente_id).first()


def create_cliente(db: Session, data: ClienteCreate) -> Cliente:
    data_dict = data.model_dump()
    if "nit" in data_dict:
        data_dict["rfc"] = data_dict.pop("nit")
    cliente = Cliente(**data_dict)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def update_cliente(db: Session, cliente_id: int, data: ClienteUpdate) -> Optional[Cliente]:
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if "nit" in update_data:
        update_data["rfc"] = update_data.pop("nit")
    for key, value in update_data.items():
        setattr(cliente, key, value)

    db.commit()
    db.refresh(cliente)
    return cliente


def delete_cliente(db: Session, cliente_id: int) -> bool:
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        return False

    db.delete(cliente)
    db.commit()
    return True


def get_cliente_ordenes(db: Session, cliente_id: int) -> list:
    from app.models.historial_estado import HistorialEstado

    ordenes = db.query(OrdenServicio).filter(
        OrdenServicio.client_id == cliente_id
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


def get_cliente_motos(db: Session, cliente_id: int) -> list:
    motos = db.query(Moto).filter(Moto.client_id == cliente_id).all()
    return motos
