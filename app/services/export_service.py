import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session

from app.config import settings
from app.models.orden_servicio import OrdenServicio
from app.models.repuesto import Repuesto
from app.models.orden_compra import OrdenCompra
from app.models.cliente import Cliente
from app.models.moto import Moto
from app.models.usuario import Usuario


def export_ordenes_csv(
    db: Session,
    estado: str = None,
    fecha_desde: str = None,
    fecha_hasta: str = None,
) -> str:
    from sqlalchemy import func
    from app.models.historial_estado import HistorialEstado

    currency = settings.CURRENCY_SYMBOL

    query = db.query(OrdenServicio).join(Cliente).join(Moto)

    if estado:
        query = query.filter(OrdenServicio.estado == estado)
    if fecha_desde:
        try:
            fecha = datetime.strptime(fecha_desde, "%Y-%m-%d")
            query = query.filter(OrdenServicio.created_at >= fecha)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fecha = datetime.strptime(fecha_hasta, "%Y-%m-%d")
            query = query.filter(OrdenServicio.created_at < fecha + timedelta(days=1))
        except ValueError:
            pass

    ordenes = query.order_by(OrdenServicio.created_at.desc()).all()

    output = io.StringIO()
    output.write('\ufeff')  # BOM para UTF-8
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'Codigo', 'Cliente', 'Telefono', 'Moto', 'Falla',
        'Estado', f'Presupuesto ({currency})', f'Precio Final ({currency})', 'Fecha Entrada', 'Fecha Salida'
    ])

    for o in ordenes:
        writer.writerow([
            o.codigo,
            o.cliente.nombre,
            o.cliente.telefono or '',
            f"{o.moto.marca} {o.moto.modelo}",
            o.falla_reportada,
            o.estado,
            float(o.presupuesto) if o.presupuesto else '',
            float(o.precio_final) if o.precio_final else '',
            o.created_at.strftime('%d/%m/%Y %H:%M') if o.created_at else '',
            o.updated_at.strftime('%d/%m/%Y %H:%M') if o.updated_at else '',
        ])

    return output.getvalue()


def export_inventario_csv(db: Session) -> str:
    currency = settings.CURRENCY_SYMBOL
    repuestos = db.query(Repuesto).filter(Repuesto.activo == True).order_by(Repuesto.nombre).all()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'Codigo', 'Nombre', 'Categoria', 'Marca', 'Stock Actual',
        'Stock Minimo', f'Precio Compra ({currency})', f'Precio Venta ({currency})', 'Ubicacion', 'Estado'
    ])

    for r in repuestos:
        if r.stock_actual == 0:
            estado = 'Sin Stock'
        elif r.stock_actual <= r.stock_minimo:
            estado = 'Bajo'
        else:
            estado = 'OK'

        writer.writerow([
            r.codigo,
            r.nombre,
            r.categoria or '',
            r.marca or '',
            r.stock_actual,
            r.stock_minimo,
            float(r.precio_compra) if r.precio_compra else '',
            float(r.precio_venta) if r.precio_venta else '',
            r.ubicacion or '',
            estado,
        ])

    return output.getvalue()


def export_clientes_csv(db: Session) -> str:
    from sqlalchemy import func

    clientes = db.query(Cliente).order_by(Cliente.nombre).all()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'ID', 'Nombre', 'Telefono', 'Email', 'Direccion', 'NIT',
        'Total Motos', 'Total Ordenes'
    ])

    for c in clientes:
        motos_count = db.query(func.count(Moto.id)).filter(Moto.client_id == c.id).scalar() or 0
        ordenes_count = db.query(func.count(OrdenServicio.id)).filter(OrdenServicio.client_id == c.id).scalar() or 0

        writer.writerow([
            c.id,
            c.nombre,
            c.telefono or '',
            c.email or '',
            c.direccion or '',
            c.nit or '',
            motos_count,
            ordenes_count,
        ])

    return output.getvalue()


def generate_orden_pdf_data(db: Session, codigo: str) -> dict:
    orden = db.query(OrdenServicio).filter(OrdenServicio.codigo == codigo).first()
    if not orden:
        return None

    from app.models.orden_repuesto import OrdenRepuesto
    repuestos_items = db.query(OrdenRepuesto).filter(
        OrdenRepuesto.service_order_id == orden.id
    ).all()

    repuestos_list = []
    for item in repuestos_items:
        repuesto = db.query(Repuesto).filter(Repuesto.id == item.part_id).first()
        repuestos_list.append({
            'nombre': repuesto.nombre if repuesto else 'N/A',
            'cantidad': item.cantidad,
            'precio_unitario': float(item.precio_unitario) if item.precio_unitario else 0,
            'subtotal': float(item.subtotal) if item.subtotal else 0,
        })

    subtotal_repuestos = sum(r['subtotal'] for r in repuestos_list)

    return {
        'codigo': orden.codigo,
        'cliente': {
            'nombre': orden.cliente.nombre,
            'telefono': orden.cliente.telefono or '',
            'email': orden.cliente.email or '',
            'direccion': orden.cliente.direccion or '',
        },
        'moto': {
            'marca': orden.moto.marca,
            'modelo': orden.moto.modelo,
            'placa': orden.moto.placa or '',
            'anio': orden.moto.anio or '',
            'kilometraje': orden.moto.kilometraje or 0,
        },
        'falla_reportada': orden.falla_reportada,
        'diagnostico': orden.diagnostico or '',
        'estado': orden.estado,
        'presupuesto': float(orden.presupuesto) if orden.presupuesto else 0,
        'precio_final': float(orden.precio_final) if orden.precio_final else 0,
        'repuestos': repuestos_list,
        'subtotal_repuestos': subtotal_repuestos,
        'fecha_entrada': orden.created_at.strftime('%d/%m/%Y %H:%M') if orden.created_at else '',
        'fecha_salida': orden.updated_at.strftime('%d/%m/%Y %H:%M') if orden.updated_at else '',
    }
