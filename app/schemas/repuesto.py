from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class RepuestoBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    marca: Optional[str] = None
    compatible_models: Optional[str] = None
    stock_minimo: int = 3
    stock_actual: int = 0
    precio_compra: Optional[float] = None
    precio_venta: Optional[float] = None
    ubicacion: Optional[str] = None


class RepuestoCreate(RepuestoBase):
    pass


class RepuestoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    marca: Optional[str] = None
    compatible_models: Optional[str] = None
    stock_minimo: Optional[int] = None
    stock_actual: Optional[int] = None
    precio_compra: Optional[float] = None
    precio_venta: Optional[float] = None
    ubicacion: Optional[str] = None
    activo: Optional[bool] = None


class StockUpdate(BaseModel):
    cantidad: int
    tipo: str  # "entrada" o "salida"


class RepuestoResponse(RepuestoBase):
    id: int
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RepuestoListResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    categoria: Optional[str] = None
    marca: Optional[str] = None
    stock_actual: int
    stock_minimo: int
    precio_venta: Optional[float] = None
    estado_stock: str  # "ok", "low", "out"

    model_config = {"from_attributes": True}


CATEGORIAS_REPUESTOS = [
    "Frenos",
    "Motor",
    "Suspension",
    "Transmision",
    "Electrico",
    "Carroceria",
    "Llantas",
    "Aceites",
    "Varios",
]
