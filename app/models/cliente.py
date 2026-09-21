from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Cliente(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    telefono = Column(String(20))
    email = Column(String(100))
    direccion = Column(Text)
    nit = Column(String(20))
    notas = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    motos = relationship("Moto", back_populates="cliente", cascade="all, delete-orphan")
    ordenes = relationship("OrdenServicio", back_populates="cliente")
