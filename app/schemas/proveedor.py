from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class ProveedorBase(BaseModel):
    nombre: str
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    rfc: Optional[str] = None
    notas: Optional[str] = None


class ProveedorCreate(ProveedorBase):
    pass


class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    rfc: Optional[str] = None
    notas: Optional[str] = None
    activo: Optional[bool] = None


class ProveedorResponse(ProveedorBase):
    id: int
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProveedorListResponse(BaseModel):
    id: int
    nombre: str
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    total_ordenes: int = 0

    model_config = {"from_attributes": True}
