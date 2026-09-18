from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric

from app.database import Base


class Repuesto(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text)
    categoria = Column(String(50))
    marca = Column(String(50))
    compatible_models = Column(String(200))
    stock_minimo = Column(Integer, default=3)
    stock_actual = Column(Integer, default=0)
    stock_reservado = Column(Integer, default=0)
    precio_compra = Column(Numeric(10, 2))
    precio_venta = Column(Numeric(10, 2))
    ubicacion = Column(String(50))
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
