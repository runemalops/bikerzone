from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime

from app.database import Base


class Usuario(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    rol = Column(String(20), nullable=False, default="tecnico")
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
