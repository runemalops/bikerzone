from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class OrdenCompraDetalleBase(BaseModel):
    part_id: int
    cantidad: int
    precio_unitario: float


class OrdenCompraDetalleCreate(OrdenCompraDetalleBase):
    pass


class OrdenCompraDetalleResponse(OrdenCompraDetalleBase):
    id: int
    repuesto_nombre: str = ""
    subtotal: float

    model_config = {"from_attributes": True}


class OrdenCompraBase(BaseModel):
    supplier_id: int
    notas: Optional[str] = None


class OrdenCompraCreate(OrdenCompraBase):
    detalles: List[OrdenCompraDetalleCreate] = []


class EstadoCompraUpdate(BaseModel):
    nuevo_estado: str
    observaciones: Optional[str] = None


class OrdenCompraResponse(OrdenCompraBase):
    id: int
    codigo: str
    estado: str
    subtotal: Optional[float] = None
    iva: Optional[float] = None
    total: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrdenCompraListResponse(BaseModel):
    id: int
    codigo: str
    proveedor_nombre: str
    estado: str
    total: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


ESTADOS_COMPRA = {
    "pending": "Pendiente",
    "sent": "Enviada",
    "partial": "Parcialmente Recibida",
    "received": "Recibida",
    "cancelled": "Cancelada",
}

FLUJO_ESTADOS_COMPRA = {
    "pending": ["sent", "cancelled"],
    "sent": ["partial", "received", "cancelled"],
    "partial": ["received", "cancelled"],
    "received": [],
    "cancelled": [],
}
