from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.database import Base


class OrdenServicio(Base):
    __tablename__ = "service_orders"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    motorcycle_id = Column(Integer, ForeignKey("motorcycles.id"), nullable=False)
    technician_id = Column(Integer, ForeignKey("users.id"))
    falla_reportada = Column(Text, nullable=False)
    diagnostico = Column(Text)
    estado = Column(String(30), default="received")
    presupuesto = Column(Numeric(10, 2))
    precio_final = Column(Numeric(10, 2))
    kilometraje_entrada = Column(Integer)
    kilometraje_salida = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="ordenes")
    moto = relationship("Moto", back_populates="ordenes")
    tecnico = relationship("Usuario", foreign_keys=[technician_id])
    historial = relationship("HistorialEstado", back_populates="orden", cascade="all, delete-orphan")
    repuestos = relationship("OrdenRepuesto", back_populates="orden", cascade="all, delete-orphan")
