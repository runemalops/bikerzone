from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class UsuarioBase(BaseModel):
    nombre: str
    email: EmailStr
    rol: str = "tecnico"


class UsuarioCreate(UsuarioBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contrasena debe tener al menos 8 caracteres")
        if not any(c.isupper() for c in v):
            raise ValueError("La contrasena debe contener al menos una letra mayuscula")
        if not any(c.islower() for c in v):
            raise ValueError("La contrasena debe contener al menos una letra minuscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("La contrasena debe contener al menos un numero")
        return v


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None


class UsuarioResponse(UsuarioBase):
    id: int
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse
