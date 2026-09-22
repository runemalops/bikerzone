from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import exc as sa_exc

from app.models.orden_servicio import OrdenServicio
from app.models.historial_estado import HistorialEstado
from app.models.orden_repuesto import OrdenRepuesto
from app.models.repuesto import Repuesto
from app.models.cliente import Cliente
from app.models.moto import Moto
from app.models.usuario import Usuario
from app.schemas.orden_servicio import (
    OrdenServicioCreate,
    OrdenServicioUpdate,
    FLUJO_ESTADOS,
    ESTADO_LABELS,
)


def generate_codigo(db: Session) -> str:
    year = datetime.now().year
    last = db.query(OrdenServicio).filter(
        OrdenServicio.codigo.like(f"BZ-{year}-%")
    ).order_by(OrdenServicio.id.desc()).first()

    if last:
        last_num = int(last.codigo.split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1

    return f"BZ-{year}-{new_num:05d}"


def get_ordenes(
    db: Session,
    search: Optional[str] = None,
    estado: Optional[str] = None,
    technician_id: Optional[int] = None,
    client_id: Optional[int] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[dict], int]:
    query = db.query(OrdenServicio).join(Cliente).join(Moto)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (OrdenServicio.codigo.ilike(search_filter)) |
            (Cliente.nombre.ilike(search_filter)) |
            (Moto.marca.ilike(search_filter)) |
            (Moto.modelo.ilike(search_filter))
        )

    if estado:
        query = query.filter(OrdenServicio.estado == estado)

    if technician_id:
        query = query.filter(OrdenServicio.technician_id == technician_id)

    if client_id:
        query = query.filter(OrdenServicio.client_id == client_id)

    if fecha_desde:
        try:
            fecha = datetime.strptime(fecha_desde, "%Y-%m-%d")
            query = query.filter(OrdenServicio.created_at >= fecha)
        except ValueError:
            pass

    if fecha_hasta:
        try:
            fecha = datetime.strptime(fecha_hasta, "%Y-%m-%d")
            query = query.filter(OrdenServicio.created_at <= fecha.replace(hour=23, minute=59, second=59))
        except ValueError:
            pass

    total = query.count()
    ordenes = query.order_by(OrdenServicio.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    result = []
    for o in ordenes:
        result.append({
            "id": o.id,
            "codigo": o.codigo,
            "cliente_nombre": o.cliente.nombre,
            "moto_info": f"{o.moto.marca} {o.moto.modelo}",
            "estado": o.estado,
            "estado_label": ESTADO_LABELS.get(o.estado, o.estado),
            "falla_reportada": o.falla_reportada,
            "presupuesto": float(o.presupuesto) if o.presupuesto else None,
            "precio_final": float(o.precio_final) if o.precio_final else None,
            "created_at": o.created_at,
        })

    return result, total


def get_orden(db: Session, codigo: str) -> Optional[OrdenServicio]:
    return db.query(OrdenServicio).filter(OrdenServicio.codigo == codigo).first()


def get_orden_by_id(db: Session, orden_id: int) -> Optional[OrdenServicio]:
    return db.query(OrdenServicio).filter(OrdenServicio.id == orden_id).first()


def create_orden(db: Session, data: OrdenServicioCreate, user_id: int) -> OrdenServicio:
    for attempt in range(5):
        codigo = generate_codigo(db)

        orden = OrdenServicio(
            codigo=codigo,
            client_id=data.client_id,
            motorcycle_id=data.motorcycle_id,
            technician_id=data.technician_id,
            falla_reportada=data.falla_reportada,
            kilometraje_entrada=data.kilometraje_entrada,
            estado="received",
        )
        db.add(orden)
        try:
            db.flush()

            historial = HistorialEstado(
                service_order_id=orden.id,
                estado="received",
                user_id=user_id,
                observaciones="Orden creada",
            )
            db.add(historial)
            db.commit()
            db.refresh(orden)
            return orden
        except sa_exc.IntegrityError:
            db.rollback()
            continue
    raise ValueError("No se pudo generar un codigo unico tras varios intentos")


def update_orden(db: Session, orden_id: int, data: OrdenServicioUpdate) -> Optional[OrdenServicio]:
    orden = db.query(OrdenServicio).filter(OrdenServicio.id == orden_id).first()
    if not orden:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(orden, key, value)

    recalcular_precio_final(db, orden_id)
    db.commit()
    db.refresh(orden)
    return orden


def cambiar_estado(
    db: Session,
    orden_id: int,
    nuevo_estado: str,
    user_id: int,
    observaciones: Optional[str] = None,
) -> Tuple[bool, str]:
    orden = db.query(OrdenServicio).filter(OrdenServicio.id == orden_id).first()
    if not orden:
        return False, "Orden no encontrada"

    estados_permitidos = FLUJO_ESTADOS.get(orden.estado, [])
    if nuevo_estado not in estados_permitidos:
        return False, f"Transicion no valida: {orden.estado} -> {nuevo_estado}"

    orden.estado = nuevo_estado

    if nuevo_estado == "cancelled":
        items = db.query(OrdenRepuesto).filter(
            OrdenRepuesto.service_order_id == orden.id
        ).all()
        for item in items:
            repuesto = db.query(Repuesto).filter(Repuesto.id == item.part_id).first()
            if repuesto:
                repuesto.stock_reservado = max(0, repuesto.stock_reservado - item.cantidad)

    historial = HistorialEstado(
        service_order_id=orden.id,
        estado=nuevo_estado,
        user_id=user_id,
        observaciones=observaciones,
    )
    db.add(historial)
    db.commit()
    return True, f"Estado cambiado a {ESTADO_LABELS.get(nuevo_estado, nuevo_estado)}"


def get_historial(db: Session, orden_id: int) -> list:
    historial = db.query(HistorialEstado).filter(
        HistorialEstado.service_order_id == orden_id
    ).order_by(HistorialEstado.fecha.desc()).all()

    result = []
    for h in historial:
        user = db.query(Usuario).filter(Usuario.id == h.user_id).first()
        result.append({
            "id": h.id,
            "estado": h.estado,
            "estado_label": ESTADO_LABELS.get(h.estado, h.estado),
            "observaciones": h.observaciones,
            "fecha": h.fecha,
            "usuario_nombre": user.nombre if user else "Sistema",
        })

    return result


def get_repuestos_orden(db: Session, orden_id: int) -> list:
    items = db.query(OrdenRepuesto).filter(
        OrdenRepuesto.service_order_id == orden_id
    ).all()

    result = []
    for item in items:
        repuesto = db.query(Repuesto).filter(Repuesto.id == item.part_id).first()
        result.append({
            "id": item.id,
            "repuesto_nombre": repuesto.nombre if repuesto else "N/A",
            "repuesto_codigo": repuesto.codigo if repuesto else "N/A",
            "cantidad": item.cantidad,
            "precio_unitario": float(item.precio_unitario) if item.precio_unitario else 0,
            "subtotal": float(item.subtotal) if item.subtotal else 0,
        })

    return result


def recalcular_precio_final(db: Session, orden_id: int) -> None:
    """Recalcula el precio_final = suma_subtotales_repuestos + mano_obra."""
    from decimal import Decimal

    items = db.query(OrdenRepuesto).filter(
        OrdenRepuesto.service_order_id == orden_id
    ).all()
    subtotal_repuestos = sum(float(item.subtotal or 0) for item in items)

    orden = db.query(OrdenServicio).filter(OrdenServicio.id == orden_id).first()
    if orden:
        mano_obra = float(orden.mano_obra or 0)
        orden.precio_final = Decimal(str(subtotal_repuestos + mano_obra))


def add_repuesto_orden(
    db: Session,
    orden_id: int,
    repuesto_id: int,
    cantidad: int,
) -> Tuple[bool, str]:
    orden = db.query(OrdenServicio).filter(OrdenServicio.id == orden_id).first()
    if not orden:
        return False, "Orden no encontrada"

    repuesto = db.query(Repuesto).filter(Repuesto.id == repuesto_id).first()
    if not repuesto:
        return False, "Repuesto no encontrado"

    disponible = repuesto.stock_actual - repuesto.stock_reservado
    if disponible < cantidad:
        return False, f"Stock insuficiente. Disponible: {disponible}"

    repuesto.stock_reservado += cantidad

    precio = repuesto.precio_venta or repuesto.precio_compra or 0
    subtotal = float(precio) * cantidad

    item = OrdenRepuesto(
        service_order_id=orden_id,
        part_id=repuesto_id,
        cantidad=cantidad,
        precio_unitario=precio,
        subtotal=subtotal,
    )
    db.add(item)
    recalcular_precio_final(db, orden_id)
    db.commit()

    return True, f"Repuesto {repuesto.nombre} agregado (stock reservado)"


def remove_repuesto_orden(
    db: Session,
    orden_id: int,
    item_id: int,
) -> Tuple[bool, str]:
    item = db.query(OrdenRepuesto).filter(
        OrdenRepuesto.id == item_id,
        OrdenRepuesto.service_order_id == orden_id,
    ).first()
    if not item:
        return False, "Item no encontrado"

    repuesto = db.query(Repuesto).filter(Repuesto.id == item.part_id).first()
    if repuesto:
        if repuesto.stock_reservado >= item.cantidad:
            repuesto.stock_reservado -= item.cantidad
        else:
            repuesto.stock_reservado = 0

    db.delete(item)
    recalcular_precio_final(db, orden_id)
    db.commit()

    return True, "Repuesto eliminado"


def confirmar_orden(
    db: Session,
    orden_id: int,
    user_id: int,
    observaciones: Optional[str] = None,
) -> Tuple[bool, str]:
    orden = db.query(OrdenServicio).filter(OrdenServicio.id == orden_id).first()
    if not orden:
        return False, "Orden no encontrada"

    if orden.estado == "received":
        items = db.query(OrdenRepuesto).filter(
            OrdenRepuesto.service_order_id == orden_id
        ).all()

        for item in items:
            repuesto = db.query(Repuesto).filter(Repuesto.id == item.part_id).first()
            if repuesto:
                if repuesto.stock_actual < item.cantidad:
                    return False, f"Stock insuficiente para {repuesto.nombre}: disponible {repuesto.stock_actual}, necesario {item.cantidad}"
                repuesto.stock_reservado = max(0, repuesto.stock_reservado - item.cantidad)
                repuesto.stock_actual -= item.cantidad

        recalcular_precio_final(db, orden_id)
        db.commit()

        nuevo_estado = "in_progress"
    elif orden.estado == "in_progress":
        recalcular_precio_final(db, orden_id)
        db.commit()

        nuevo_estado = "repairing"
    else:
        return False, f"Estado no valido para confirmar: {orden.estado}"

    return cambiar_estado(db, orden_id, nuevo_estado, user_id, observaciones)


def liberar_reservas_orden(
    db: Session,
    orden_id: int,
) -> Tuple[bool, str]:
    items = db.query(OrdenRepuesto).filter(
        OrdenRepuesto.service_order_id == orden_id
    ).all()

    for item in items:
        repuesto = db.query(Repuesto).filter(Repuesto.id == item.part_id).with_for_update().first()
        if repuesto:
            if repuesto.stock_reservado >= item.cantidad:
                repuesto.stock_reservado -= item.cantidad
            else:
                repuesto.stock_reservado = 0

    return True, "Reservas liberadas"


def delete_orden(db: Session, orden_id: int) -> bool:
    orden = db.query(OrdenServicio).filter(OrdenServicio.id == orden_id).first()
    if not orden:
        return False

    if orden.estado in ("in_progress", "repairing", "quote_approved"):
        return False

    liberar_reservas_orden(db, orden_id)

    db.query(HistorialEstado).filter(HistorialEstado.service_order_id == orden_id).delete()
    db.query(OrdenRepuesto).filter(OrdenRepuesto.service_order_id == orden_id).delete()
    db.delete(orden)
    db.commit()
    return True


def getClientesList(db: Session) -> list:
    return db.query(Cliente).order_by(Cliente.nombre).all()


def getMotosList(db: Session, client_id: Optional[int] = None) -> list:
    query = db.query(Moto)
    if client_id:
        query = query.filter(Moto.client_id == client_id)
    return query.all()


def getTecnicosList(db: Session) -> list:
    return db.query(Usuario).filter(Usuario.rol == "tecnico", Usuario.activo == True).order_by(Usuario.nombre).all()


def getRepuestosList(db: Session) -> list:
    repuestos = db.query(Repuesto).filter(
        Repuesto.activo == True
    ).order_by(Repuesto.nombre).all()

    result = []
    for r in repuestos:
        disponible = r.stock_actual - r.stock_reservado
        result.append({
            "id": r.id,
            "nombre": r.nombre,
            "codigo": r.codigo,
            "precio_compra": r.precio_compra,
            "precio_venta": r.precio_venta,
            "stock_actual": r.stock_actual,
            "stock_reservado": r.stock_reservado,
            "stock_disponible": disponible,
        })
    return result
