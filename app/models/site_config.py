from sqlalchemy import Boolean, Column, Integer, String

from app.database import Base

DEFAULT_SITE_TITLE = "BikerZone"
DEFAULT_SITE_LOGO = "/static/img/logo.svg"


class SiteConfig(Base):
    __tablename__ = "site_config"

    id = Column(Integer, primary_key=True)  # fila unica, siempre id=1
    site_title = Column(String(80), nullable=False, default=DEFAULT_SITE_TITLE)
    site_logo = Column(String(255), nullable=False, default=DEFAULT_SITE_LOGO)
    # Notificaciones y preventivo
    notif_email_auto = Column(Boolean, nullable=False, default=True)
    notif_telegram_auto = Column(Boolean, nullable=False, default=True)
    preventivo_dias_anticipacion = Column(Integer, nullable=False, default=7)
    preventivo_km_anticipacion = Column(Integer, nullable=False, default=500)
    # Km a sumar al kilometraje de salida para reprogramar el proximo servicio (0 = no reprogramar)
    preventivo_km_intervalo = Column(Integer, nullable=False, default=5000)
