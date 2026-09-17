from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Proveedor(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    contacto = Column(String(100))
    telefono = Column(String(20))
    email = Column(String(100))
    direccion = Column(Text)
    rfc = Column(String(20))
    notas = Column(Text)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ordenes_compra = relationship("OrdenCompra", back_populates="proveedor")
