from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.orden_servicio import OrdenServicio
from app.models.repuesto import Repuesto
from app.models.orden_compra import OrdenCompra
from app.models.usuario import Usuario
from app.models.cliente import Cliente


def get_dashboard_stats(db: Session) -> dict:
    ordenes_activas = db.query(func.count(OrdenServicio.id)).filter(
        OrdenServicio.estado.notin_(["delivered", "cancelled"])
    ).scalar() or 0

    mes_actual = datetime.now().month
    anio_actual = datetime.now().year

    completadas_mes = db.query(func.count(OrdenServicio.id)).filter(
        OrdenServicio.estado == "delivered",
        extract("month", OrdenServicio.updated_at) == mes_actual,
        extract("year", OrdenServicio.updated_at) == anio_actual,
    ).scalar() or 0

    ingresos_mes = db.query(func.coalesce(func.sum(OrdenServicio.precio_final), 0)).filter(
        OrdenServicio.estado == "delivered",
        extract("month", OrdenServicio.updated_at) == mes_actual,
        extract("year", OrdenServicio.updated_at) == anio_actual,
    ).scalar() or 0

    stock_bajo = db.query(func.count(Repuesto.id)).filter(
        Repuesto.activo == True,
        Repuesto.stock_actual <= Repuesto.stock_minimo,
    ).scalar() or 0

    return {
        "ordenes_activas": ordenes_activas,
        "completadas_mes": completadas_mes,
        "ingresos_mes": float(ingresos_mes),
        "stock_bajo": stock_bajo,
    }


def get_ordenes_por_estado(db: Session) -> List[dict]:
    result = db.query(
        OrdenServicio.estado,
        func.count(OrdenServicio.id)
    ).group_by(OrdenServicio.estado).all()

    labels = {
        "received": "Recibido",
        "diagnosed": "Diagnosticado",
        "quote_sent": "Presupuesto",
        "quote_approved": "Aprobado",
        "quote_rejected": "Presupuesto Rechazado",
        "in_progress": "En Proceso",
        "repairing": "Reparando",
        "awaiting_part": "Esperando Pieza",
        "ready": "Listo",
        "delivered": "Entregado",
        "cancelled": "Cancelado",
    }

    return [{"estado": labels.get(r[0], r[0]), "cantidad": r[1]} for r in result]


def get_ordenes_por_mes(db: Session, meses: int = 6) -> List[dict]:
    result = []
    for i in range(meses - 1, -1, -1):
        fecha = datetime.now() - timedelta(days=30 * i)
        mes = fecha.month
        anio = fecha.year

        count = db.query(func.count(OrdenServicio.id)).filter(
            extract("month", OrdenServicio.created_at) == mes,
            extract("year", OrdenServicio.created_at) == anio,
        ).scalar() or 0

        ingresos = db.query(func.coalesce(func.sum(OrdenServicio.precio_final), 0)).filter(
            OrdenServicio.estado == "delivered",
            extract("month", OrdenServicio.updated_at) == mes,
            extract("year", OrdenServicio.updated_at) == anio,
        ).scalar() or 0

        result.append({
            "mes": fecha.strftime("%b %Y"),
            "ordenes": count,
            "ingresos": float(ingresos),
        })

    return result


def get_top_clientes(db: Session, limit: int = 10) -> List[dict]:
    result = db.query(
        Cliente.nombre,
        func.count(OrdenServicio.id).label("total_ordenes"),
        func.coalesce(func.sum(OrdenServicio.precio_final), 0).label("total_gastado"),
    ).join(OrdenServicio, Cliente.id == OrdenServicio.client_id).group_by(
        Cliente.id
    ).order_by(func.sum(OrdenServicio.precio_final).desc()).limit(limit).all()

    return [{"nombre": r[0], "ordenes": r[1], "gastado": float(r[2])} for r in result]


def get_ventas_por_tecnico(db: Session) -> List[dict]:
    result = db.query(
        Usuario.nombre,
        func.count(OrdenServicio.id).label("total_ordenes"),
        func.coalesce(func.sum(OrdenServicio.precio_final), 0).label("total_ventas"),
    ).join(OrdenServicio, Usuario.id == OrdenServicio.technician_id).filter(
        OrdenServicio.estado == "delivered"
    ).group_by(Usuario.id).all()

    return [{"tecnico": r[0], "ordenes": r[1], "ventas": float(r[2])} for r in result]


def get_inventario_stats(db: Session) -> dict:
    total_repuestos = db.query(func.count(Repuesto.id)).filter(Repuesto.activo == True).scalar() or 0

    valor_compra = db.query(
        func.coalesce(func.sum(Repuesto.precio_compra * Repuesto.stock_actual), 0)
    ).filter(Repuesto.activo == True).scalar() or 0

    valor_venta = db.query(
        func.coalesce(func.sum(Repuesto.precio_venta * Repuesto.stock_actual), 0)
    ).filter(Repuesto.activo == True).scalar() or 0

    bajo_stock = db.query(func.count(Repuesto.id)).filter(
        Repuesto.activo == True,
        Repuesto.stock_actual <= Repuesto.stock_minimo,
    ).scalar() or 0

    sin_stock = db.query(func.count(Repuesto.id)).filter(
        Repuesto.activo == True,
        Repuesto.stock_actual == 0,
    ).scalar() or 0

    return {
        "total_repuestos": total_repuestos,
        "valor_compra": float(valor_compra),
        "valor_venta": float(valor_venta),
        "bajo_stock": bajo_stock,
        "sin_stock": sin_stock,
    }


def get_stock_por_categoria(db: Session) -> List[dict]:
    result = db.query(
        Repuesto.categoria,
        func.count(Repuesto.id),
        func.sum(Repuesto.stock_actual),
    ).filter(Repuesto.activo == True).group_by(Repuesto.categoria).all()

    return [{"categoria": r[0] or "Sin Categoria", "cantidad": r[1], "stock": r[2] or 0} for r in result]


def get_compras_por_proveedor(db: Session) -> List[dict]:
    result = db.query(
        func.count(OrdenCompra.id).label("ordenes"),
        func.coalesce(func.sum(OrdenCompra.total), 0).label("total"),
    ).filter(
        OrdenCompra.estado == "received"
    ).all()

    return [{"ordenes": r[0], "total": float(r[1])} for r in result]


def get_compras_por_mes(db: Session, meses: int = 6) -> List[dict]:
    result = []
    for i in range(meses - 1, -1, -1):
        fecha = datetime.now() - timedelta(days=30 * i)
        mes = fecha.month
        anio = fecha.year

        total = db.query(func.coalesce(func.sum(OrdenCompra.total), 0)).filter(
            extract("month", OrdenCompra.created_at) == mes,
            extract("year", OrdenCompra.created_at) == anio,
        ).scalar() or 0

        count = db.query(func.count(OrdenCompra.id)).filter(
            extract("month", OrdenCompra.created_at) == mes,
            extract("year", OrdenCompra.created_at) == anio,
        ).scalar() or 0

        result.append({
            "mes": fecha.strftime("%b %Y"),
            "ordenes": count,
            "total": float(total),
        })

    return result


def get_tiempos_reparacion(db: Session) -> dict:
    from sqlalchemy import func as sqlfunc

    result = db.query(
        sqlfunc.avg(
            sqlfunc.extract("epoch", OrdenServicio.updated_at - OrdenServicio.created_at) / 86400
        )
    ).filter(OrdenServicio.estado == "delivered").scalar()

    return {
        "dias_promedio": round(float(result), 1) if result else 0,
    }


def get_ordenes_por_tecnico(db: Session) -> List[dict]:
    result = db.query(
        Usuario.nombre,
        func.count(OrdenServicio.id),
    ).join(OrdenServicio, Usuario.id == OrdenServicio.technician_id).group_by(
        Usuario.id
    ).all()

    return [{"tecnico": r[0], "ordenes": r[1]} for r in result]


def get_stock_bajo_list(db: Session) -> list:
    return db.query(Repuesto).filter(
        Repuesto.activo == True,
        Repuesto.stock_actual <= Repuesto.stock_minimo,
    ).order_by(Repuesto.stock_actual).limit(10).all()


def get_tecnico_stats(db: Session, technician_id: int) -> dict:
    """Get dashboard stats filtered for a specific technician."""
    ordenes_activas = db.query(func.count(OrdenServicio.id)).filter(
        OrdenServicio.technician_id == technician_id,
        OrdenServicio.estado.notin_(["delivered", "cancelled"])
    ).scalar() or 0

    mes_actual = datetime.now().month
    anio_actual = datetime.now().year

    completadas_mes = db.query(func.count(OrdenServicio.id)).filter(
        OrdenServicio.technician_id == technician_id,
        OrdenServicio.estado == "delivered",
        extract("month", OrdenServicio.updated_at) == mes_actual,
        extract("year", OrdenServicio.updated_at) == anio_actual,
    ).scalar() or 0

    return {
        "ordenes_activas": ordenes_activas,
        "completadas_mes": completadas_mes,
    }


def get_ordenes_tecnico_por_estado(db: Session, technician_id: int) -> List[dict]:
    """Get orders by status for a specific technician."""
    result = db.query(
        OrdenServicio.estado,
        func.count(OrdenServicio.id)
    ).filter(
        OrdenServicio.technician_id == technician_id
    ).group_by(OrdenServicio.estado).all()

    labels = {
        "received": "Recibido",
        "diagnosed": "Diagnosticado",
        "quote_sent": "Presupuesto",
        "quote_approved": "Aprobado",
        "quote_rejected": "Presupuesto Rechazado",
        "in_progress": "En Proceso",
        "repairing": "Reparando",
        "awaiting_part": "Esperando Pieza",
        "ready": "Listo",
        "delivered": "Entregado",
        "cancelled": "Cancelado",
    }

    return [{"estado": labels.get(r[0], r[0]), "cantidad": r[1]} for r in result]


def get_ordenes_tecnico_recientes(db: Session, technician_id: int, limit: int = 10) -> List[dict]:
    """Get recent orders for a specific technician."""
    ordenes = db.query(OrdenServicio).filter(
        OrdenServicio.technician_id == technician_id,
        OrdenServicio.estado.notin_(["delivered", "cancelled"])
    ).order_by(OrdenServicio.created_at.desc()).limit(limit).all()

    result = []
    for o in ordenes:
        result.append({
            "id": o.id,
            "codigo": o.codigo,
            "cliente_nombre": o.cliente.nombre if o.cliente else "N/A",
            "moto_info": f"{o.moto.marca} {o.moto.modelo}" if o.moto else "N/A",
            "estado": o.estado,
            "estado_label": {
                "received": "Recibido",
                "diagnosed": "Diagnosticado",
                "quote_sent": "Presupuesto",
                "quote_approved": "Aprobado",
                "in_progress": "En Proceso",
                "repairing": "Reparando",
                "ready": "Listo",
            }.get(o.estado, o.estado),
            "created_at": o.created_at,
        })

    return result
