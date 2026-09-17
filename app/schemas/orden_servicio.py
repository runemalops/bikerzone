from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class OrdenServicioBase(BaseModel):
    client_id: int
    motorcycle_id: int
    falla_reportada: str
    kilometraje_entrada: Optional[int] = None


class OrdenServicioCreate(OrdenServicioBase):
    technician_id: Optional[int] = None


class OrdenServicioUpdate(BaseModel):
    diagnostico: Optional[str] = None
    presupuesto: Optional[float] = None
    precio_final: Optional[float] = None
    kilometraje_salida: Optional[int] = None


class EstadoUpdate(BaseModel):
    nuevo_estado: str
    observaciones: Optional[str] = None


class HistorialEstadoResponse(BaseModel):
    id: int
    estado: str
    observaciones: Optional[str] = None
    fecha: datetime
    usuario_nombre: str = ""

    model_config = {"from_attributes": True}


class OrdenRepuestoResponse(BaseModel):
    id: int
    repuesto_nombre: str
    cantidad: int
    precio_unitario: float
    subtotal: float

    model_config = {"from_attributes": True}


class OrdenServicioResponse(OrdenServicioBase):
    id: int
    codigo: str
    estado: str
    diagnostico: Optional[str] = None
    presupuesto: Optional[float] = None
    precio_final: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrdenServicioListResponse(BaseModel):
    id: int
    codigo: str
    cliente_nombre: str
    moto_info: str
    estado: str
    falla_reportada: str
    presupuesto: Optional[float] = None
    precio_final: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Estados validos del flujo
ESTADOS_VALIDOS = [
    "received",
    "diagnosed",
    "quote_sent",
    "quote_approved",
    "quote_rejected",
    "in_progress",
    "repairing",
    "awaiting_part",
    "ready",
    "delivered",
    "cancelled",
]

FLUJO_ESTADOS = {
    "received": ["diagnosed", "cancelled"],
    "diagnosed": ["quote_sent", "cancelled"],
    "quote_sent": ["quote_approved", "quote_rejected"],
    "quote_approved": ["in_progress"],
    "quote_rejected": ["cancelled"],
    "in_progress": ["repairing", "awaiting_part"],
    "repairing": ["ready", "awaiting_part"],
    "awaiting_part": ["repairing"],
    "ready": ["delivered"],
    "delivered": [],
    "cancelled": [],
}

ESTADO_LABELS = {
    "received": "Recibido",
    "diagnosed": "Diagnosticado",
    "quote_sent": "Presupuesto Enviado",
    "quote_approved": "Presupuesto Aprobado",
    "quote_rejected": "Presupuesto Rechazado",
    "in_progress": "En Proceso",
    "repairing": "Reparando",
    "awaiting_part": "Esperando Pieza",
    "ready": "Listo",
    "delivered": "Entregado",
    "cancelled": "Cancelado",
}
