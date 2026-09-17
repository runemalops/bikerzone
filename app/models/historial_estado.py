from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class HistorialEstado(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, index=True)
    service_order_id = Column(Integer, ForeignKey("service_orders.id", ondelete="CASCADE"), nullable=False)
    estado = Column(String(30), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    observaciones = Column(Text)
    fecha = Column(DateTime, default=datetime.utcnow)

    orden = relationship("OrdenServicio", back_populates="historial")
    usuario = relationship("Usuario", foreign_keys=[user_id])
