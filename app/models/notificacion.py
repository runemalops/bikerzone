from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base


class Notificacion(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    canal = Column(String(20), nullable=False)          # email | telegram
    estado = Column(String(20), nullable=False)         # enviado | fallido | omitido
    asunto = Column(String(200))
    mensaje = Column(Text)
    destinatario = Column(String(100))
    error = Column(Text)                                # motivo de fallo/omision
    referencia = Column(String(150))                    # clave de dedupe (preventivo)
    service_order_id = Column(Integer, ForeignKey("service_orders.id", ondelete="SET NULL"))
    motorcycle_id = Column(Integer, ForeignKey("motorcycles.id", ondelete="SET NULL"))
    cliente_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=datetime.utcnow)
