from datetime import datetime

from sqlalchemy import Column, Date, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Moto(Base):
    __tablename__ = "motorcycles"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    marca = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    anio = Column(Integer)
    placa = Column(String(20))
    color = Column(String(30))
    vin = Column(String(100))
    kilometraje = Column(Integer, default=0)
    proximo_service_km = Column(Integer)
    proximo_service_fecha = Column(Date)
    notas = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="motos")
    ordenes = relationship("OrdenServicio", back_populates="moto")
