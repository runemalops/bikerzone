from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.orden_compra import OrdenCompra
from app.models.orden_compra_detalle import OrdenCompraDetalle
from app.models.repuesto import Repuesto
from app.models.proveedor import Proveedor
from app.schemas.orden_compra import (
    OrdenCompraCreate,
    OrdenCompraDetalleCreate,
    FLUJO_ESTADOS_COMPRA,
    ESTADOS_COMPRA,
)


def generate_codigo(db: Session) -> str:
    year = datetime.now().year
    last = db.query(OrdenCompra).filter(
        OrdenCompra.codigo.like(f"OC-{year}-%")
    ).order_by(OrdenCompra.id.desc()).first()

    if last:
        last_num = int(last.codigo.split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1

    return f"OC-{year}-{new_num:05d}"


def get_ordenes_compra(
    db: Session,
    search: Optional[str] = None,
    estado: Optional[str] = None,
    proveedor_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[dict], int]:
    query = db.query(OrdenCompra).join(Proveedor)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (OrdenCompra.codigo.ilike(search_filter)) |
            (Proveedor.nombre.ilike(search_filter))
        )

    if estado:
        query = query.filter(OrdenCompra.estado == estado)

    if proveedor_id:
        query = query.filter(OrdenCompra.supplier_id == proveedor_id)

    total = query.count()
    ordenes = query.order_by(OrdenCompra.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    result = []
    for o in ordenes:
        result.append({
            "id": o.id,
            "codigo": o.codigo,
            "proveedor_nombre": o.proveedor.nombre,
            "estado": o.estado,
            "estado_label": ESTADOS_COMPRA.get(o.estado, o.estado),
            "total": float(o.total) if o.total else 0,
            "created_at": o.created_at,
        })

    return result, total


def get_orden_compra(db: Session, codigo: str) -> Optional[OrdenCompra]:
    return db.query(OrdenCompra).filter(OrdenCompra.codigo == codigo).first()


def create_orden_compra(
    db: Session,
    data: OrdenCompraCreate,
    user_id: int,
) -> OrdenCompra:
    codigo = generate_codigo(db)

    subtotal = 0
    for det in data.detalles:
        subtotal += det.precio_unitario * det.cantidad

    iva = subtotal * 0.12
    total = subtotal + iva

    orden = OrdenCompra(
        codigo=codigo,
        supplier_id=data.supplier_id,
        user_id=user_id,
        estado="pending",
        subtotal=subtotal,
        iva=iva,
        total=total,
        notas=data.notas,
    )
    db.add(orden)
    db.flush()

    for det in data.detalles:
        detalle = OrdenCompraDetalle(
            purchase_order_id=orden.id,
            part_id=det.part_id,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario,
            subtotal=det.precio_unitario * det.cantidad,
        )
        db.add(detalle)

    db.commit()
    db.refresh(orden)
    return orden


def cambiar_estado_orden_compra(
    db: Session,
    orden_id: int,
    nuevo_estado: str,
) -> Tuple[bool, str]:
    orden = db.query(OrdenCompra).filter(OrdenCompra.id == orden_id).first()
    if not orden:
        return False, "Orden no encontrada"

    estados_permitidos = FLUJO_ESTADOS_COMPRA.get(orden.estado, [])
    if nuevo_estado not in estados_permitidos:
        return False, f"Transicion no valida: {orden.estado} -> {nuevo_estado}"

    orden.estado = nuevo_estado
    db.commit()

    return True, f"Estado cambiado a {ESTADOS_COMPRA.get(nuevo_estado, nuevo_estado)}"


def recibir_mercancia(db: Session, orden_id: int) -> Tuple[bool, str]:
    orden = db.query(OrdenCompra).filter(OrdenCompra.id == orden_id).first()
    if not orden:
        return False, "Orden no encontrada"

    if orden.estado not in ["sent", "partial"]:
        return False, "Solo se puede recibir mercancia en ordenes enviadas o parciales"

    detalles = db.query(OrdenCompraDetalle).filter(
        OrdenCompraDetalle.purchase_order_id == orden_id
    ).all()

    for detalle in detalles:
        repuesto = db.query(Repuesto).filter(Repuesto.id == detalle.part_id).first()
        if repuesto:
            repuesto.stock_actual += detalle.cantidad

    orden.estado = "received"
    db.commit()

    return True, "Mercancia recibida y stock actualizado"


def get_detalles_orden(db: Session, orden_id: int) -> list:
    detalles = db.query(OrdenCompraDetalle).filter(
        OrdenCompraDetalle.purchase_order_id == orden_id
    ).all()

    result = []
    for d in detalles:
        repuesto = db.query(Repuesto).filter(Repuesto.id == d.part_id).first()
        result.append({
            "id": d.id,
            "repuesto_nombre": repuesto.nombre if repuesto else "N/A",
            "repuesto_codigo": repuesto.codigo if repuesto else "N/A",
            "cantidad": d.cantidad,
            "precio_unitario": float(d.precio_unitario) if d.precio_unitario else 0,
            "subtotal": float(d.subtotal) if d.subtotal else 0,
        })

    return result


def getProveedoresList(db: Session) -> list:
    return db.query(Proveedor).filter(Proveedor.activo == True).order_by(Proveedor.nombre).all()


def getRepuestosList(db: Session) -> list:
    return db.query(Repuesto).filter(Repuesto.activo == True).order_by(Repuesto.nombre).all()
