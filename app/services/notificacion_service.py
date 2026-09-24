import re
import smtplib
import urllib.parse
from email.message import EmailMessage
from typing import List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.notificacion import Notificacion
from app.models.orden_servicio import OrdenServicio
from app.services import site_service

CANALES = ("email", "telegram")
CANAL_LABELS = {"email": "Email", "telegram": "Telegram", "whatsapp": "WhatsApp"}


# ---------------------------------------------------------------- mensajes

def mensaje_orden_lista(orden: OrdenServicio) -> Tuple[str, str]:
    """Devuelve (asunto, texto) de la notificacion de orden lista para recoger."""
    titulo = site_service.site_title()
    cliente = orden.cliente
    moto = orden.moto
    nombre = cliente.nombre if cliente else "cliente"
    moto_info = f"{moto.marca} {moto.modelo}" if moto else "tu moto"
    asunto = f"{titulo}: Orden {orden.codigo} lista para recoger"
    lineas = [
        f"Hola {nombre},",
        "",
        f"Tu {moto_info} esta lista para recoger en el taller.",
        f"Orden: {orden.codigo}",
    ]
    total = orden.precio_final or orden.presupuesto
    if total:
        lineas.append(f"Total: {settings.CURRENCY_SYMBOL}{total}")
    lineas += ["", "Te esperamos!", titulo]
    return asunto, "\n".join(lineas)


def telefono_digits(telefono: Optional[str]) -> Optional[str]:
    """Normaliza a formato wa.me. El formulario del cliente usa +502 + 8 digitos."""
    if not telefono:
        return None
    digits = re.sub(r"\D", "", telefono)
    if digits.startswith("00"):
        digits = digits[2:]
    if len(digits) == 8:  # Guatemala: el form muestra prefijo +502
        digits = "502" + digits
    return digits or None


def link_whatsapp(telefono: Optional[str], texto: str) -> Optional[str]:
    digits = telefono_digits(telefono)
    if not digits:
        return None
    return f"https://wa.me/{digits}?text={urllib.parse.quote(texto)}"


# ------------------------------------------------------------- transportes

def enviar_email(destinatario: str, asunto: str, cuerpo: str) -> Tuple[bool, str]:
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        return False, "SMTP no configurado (SMTP_HOST / SMTP_FROM en .env)"
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg.set_content(cuerpo)
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True, ""
    except Exception as exc:  # noqa: BLE001 - se registra en notifications.error
        return False, str(exc)


def enviar_telegram(chat_id: str, texto: str) -> Tuple[bool, str]:
    if not settings.TELEGRAM_BOT_TOKEN:
        return False, "Telegram no configurado (TELEGRAM_BOT_TOKEN en .env)"
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = httpx.post(url, json={"chat_id": chat_id, "text": texto}, timeout=15)
        if resp.status_code == 200:
            return True, ""
        return False, resp.text[:300]
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


# ------------------------------------------------------------------ registro

def _log(db: Session, *, canal: str, estado: str, asunto: str, mensaje: str,
         destinatario: str, error: Optional[str] = None,
         referencia: Optional[str] = None,
         orden: Optional[OrdenServicio] = None) -> Notificacion:
    row = Notificacion(
        canal=canal,
        estado=estado,
        asunto=asunto,
        mensaje=mensaje,
        destinatario=destinatario,
        error=error or None,
        referencia=referencia,
        service_order_id=orden.id if orden else None,
        motorcycle_id=orden.motorcycle_id if orden else None,
        cliente_id=orden.client_id if orden else None,
    )
    db.add(row)
    db.commit()
    return row


def get_notificaciones_orden(db: Session, orden_id: int) -> List[dict]:
    rows = (
        db.query(Notificacion)
        .filter(Notificacion.service_order_id == orden_id)
        .order_by(Notificacion.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "canal": r.canal,
            "canal_label": CANAL_LABELS.get(r.canal, r.canal),
            "estado": r.estado,
            "destinatario": r.destinatario,
            "error": r.error,
            "created_at": r.created_at,
        }
        for r in rows
    ]


def _ya_enviado(db: Session, orden_id: int, canal: str) -> bool:
    return (
        db.query(Notificacion.id)
        .filter(
            Notificacion.service_order_id == orden_id,
            Notificacion.canal == canal,
            Notificacion.estado == "enviado",
        )
        .first()
        is not None
    )


def _enviar_canal(db: Session, orden: OrdenServicio, canal: str,
                  asunto: str, texto: str, automatica: bool) -> dict:
    cliente = orden.cliente
    destinatario = ""
    skip: Optional[str] = None

    if canal == "email":
        destinatario = (cliente.email if cliente else "") or ""
        if not destinatario:
            skip = "El cliente no tiene email registrado"
        else:
            ok, detalle = enviar_email(destinatario, asunto, texto)
    elif canal == "telegram":
        destinatario = (cliente.telegram_chat_id if cliente else "") or ""
        if not destinatario:
            skip = "El cliente no tiene chat de Telegram registrado"
        else:
            ok, detalle = enviar_telegram(destinatario, texto)
    else:
        skip = f"Canal no soportado: {canal}"

    if skip is not None:
        estado = "omitido" if automatica else "fallido"
        _log(db, canal=canal, estado=estado, asunto=asunto, mensaje=texto,
             destinatario=destinatario or "-", error=skip, orden=orden)
        return {"canal": canal, "estado": estado, "error": skip}

    estado = "enviado" if ok else "fallido"
    _log(db, canal=canal, estado=estado, asunto=asunto, mensaje=texto,
         destinatario=destinatario, error=None if ok else detalle, orden=orden)
    return {"canal": canal, "estado": estado, "error": None if ok else detalle}


def notificar_orden_lista(db: Session, orden: OrdenServicio,
                          canal: Optional[str] = None,
                          automatica: bool = False) -> List[dict]:
    """canal=None -> automatico (canales habilitados en configuracion).
    canal='email'|'telegram' -> manual (siempre intenta, sin dedupe)."""
    from app.models.site_config import SiteConfig

    config = db.query(SiteConfig).filter(SiteConfig.id == 1).first()
    if config is None:
        # get-or-create para no depender del orden de visitas
        config = site_service.get_site_config(db)

    asunto, texto = mensaje_orden_lista(orden)

    if canal is not None:
        if canal not in CANALES:
            return []
        canales = [canal]
    else:
        canales = []
        if config.notif_email_auto:
            canales.append("email")
        if config.notif_telegram_auto:
            canales.append("telegram")

    resultados = []
    for c in canales:
        if automatica and _ya_enviado(db, orden.id, c):
            continue
        resultados.append(_enviar_canal(db, orden, c, asunto, texto, automatica))
    return resultados


def auto_notificar_orden_lista(db: Session, orden: OrdenServicio) -> List[dict]:
    """Hook post-cambio de estado a 'ready'. Nunca debe propagar excepciones."""
    try:
        return notificar_orden_lista(db, orden, canal=None, automatica=True)
    except Exception:  # noqa: BLE001 - el cambio de estado no puede fallar por notificaciones
        return []
