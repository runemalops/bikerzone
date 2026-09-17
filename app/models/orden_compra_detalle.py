from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.database import Base


class OrdenCompraDetalle(Base):
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2))
    subtotal = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

    orden_compra = relationship("OrdenCompra", back_populates="detalles")
    repuesto = relationship("Repuesto")
