from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class ClienteBase(BaseModel):
    nombre: str
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    nit: Optional[str] = None
    notas: Optional[str] = None


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    nit: Optional[str] = None
    notas: Optional[str] = None


class MotoResumen(BaseModel):
    id: int
    marca: str
    modelo: str
    placa: Optional[str] = None

    model_config = {"from_attributes": True}


class ClienteResponse(ClienteBase):
    id: int
    created_at: datetime
    motos: List[MotoResumen] = []

    model_config = {"from_attributes": True}


class ClienteListResponse(BaseModel):
    id: int
    nombre: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    total_motos: int = 0
    total_ordenes: int = 0

    model_config = {"from_attributes": True}
