from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MotoBase(BaseModel):
    client_id: int
    marca: str
    modelo: str
    anio: Optional[int] = None
    placa: Optional[str] = None
    color: Optional[str] = None
    vin: Optional[str] = None
    kilometraje: int = 0
    notas: Optional[str] = None


class MotoCreate(MotoBase):
    pass


class MotoUpdate(BaseModel):
    marca: Optional[str] = None
    modelo: Optional[str] = None
    anio: Optional[int] = None
    placa: Optional[str] = None
    color: Optional[str] = None
    vin: Optional[str] = None
    kilometraje: Optional[int] = None
    notas: Optional[str] = None


class MotoResponse(MotoBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class MotoListResponse(BaseModel):
    id: int
    marca: str
    modelo: str
    anio: Optional[int] = None
    placa: Optional[str] = None
    color: Optional[str] = None
    kilometraje: int = 0
    cliente_nombre: str = ""
    total_ordenes: int = 0

    model_config = {"from_attributes": True}
