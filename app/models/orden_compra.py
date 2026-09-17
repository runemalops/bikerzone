from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.database import Base


class OrdenCompra(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    estado = Column(String(20), default="pending")
    subtotal = Column(Numeric(10, 2))
    iva = Column(Numeric(10, 2))
    total = Column(Numeric(10, 2))
    notas = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    proveedor = relationship("Proveedor", back_populates="ordenes_compra")
    usuario = relationship("Usuario", foreign_keys=[user_id])
    detalles = relationship("OrdenCompraDetalle", back_populates="orden_compra", cascade="all, delete-orphan")
