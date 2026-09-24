from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.moto import Moto
from app.models.notificacion import Notificacion
from app.models.orden_servicio import OrdenServicio
from app.models.site_config import SiteConfig
from app.services import notificacion_service, site_service

NIVEL_LABELS = {
    "vencido": "Vencido",
    "proximo": "Proximo",
    "ok": "Programado",
    "sin_programar": "Sin programar",
}


def _config(db: Session) -> SiteConfig:
    config = db.query(SiteConfig).filter(SiteConfig.id == 1).first()
    if config is None:
        config = site_service.get_site_config(db)
    return config


def evaluar_moto(moto: Moto, config: SiteConfig, hoy: Optional[date] = None) -> dict:
    """Clifica el service preventivo de una moto."""
    hoy = hoy or date.today()
    dias = config.preventivo_dias_anticipacion or 7
    km_ante = config.preventivo_km_anticipacion or 500

    tiene_fecha = moto.proximo_service_fecha is not None
    tiene_km = moto.proximo_service_km is not None

    motivos: List[str] = []
    vencido = False
    proximo = False

    if tiene_fecha:
        delta = (moto.proximo_service_fecha - hoy).days
        if delta < 0:
            vencido = True
            motivos.append(f"fecha vencida hace {-delta} dia(s) ({moto.proximo_service_fecha.strftime('%d/%m/%Y')})")
        elif delta <= dias:
            proximo = True
            motivos.append(f"fecha en {delta} dia(s) ({moto.proximo_service_fecha.strftime('%d/%m/%Y')})")

    if tiene_km:
        actual = moto.kilometraje or 0
        objetivo = moto.proximo_service_km
        if actual >= objetivo:
            vencido = True
            motivos.append(f"km alcanzados ({actual:,} de {objetivo:,} km)".replace(",", "."))
        elif actual >= objetivo - km_ante:
            proximo = True
            motivos.append(f"faltan {objetivo - actual:,} km ({actual:,} de {objetivo:,} km)".replace(",", "."))

    if vencido:
        nivel = "vencido"
    elif proximo:
        nivel = "proximo"
    elif tiene_fecha or tiene_km:
        nivel = "ok"
    else:
        nivel = "sin_programar"

    return {
        "nivel": nivel,
        "nivel_label": NIVEL_LABELS[nivel],
        "detalle": "; ".join(motivos),
        "requiere_aviso": vencido or proximo,
    }


def get_panel(db: Session, hoy: Optional[date] = None) -> Tuple[list, dict]:
    """Motos con preventivo programado, ordenadas por urgencia."""
    hoy = hoy or date.today()
    config = _config(db)
    orden_prioridad = {"vencido": 0, "proximo": 1, "ok": 2}

    rows = []
    total_sin = 0
    motos = db.query(Moto).join(Cliente).order_by(Cliente.nombre).all()
    for moto in motos:
        estado = evaluar_moto(moto, config, hoy)
        if estado["nivel"] == "sin_programar":
            total_sin += 1
            continue
        cliente = moto.cliente
        rows.append({
            "moto": moto,
            "estado": estado,
            "cliente": cliente,
            "tiene_contacto": bool(
                (cliente and (cliente.email or cliente.telefono or cliente.telegram_chat_id))
            ),
        })

    rows.sort(key=lambda r: (
        orden_prioridad.get(r["estado"]["nivel"], 9),
        r["moto"].proximo_service_fecha or date.max,
        r["moto"].proximo_service_km or 10**9,
    ))

    resumen = {
        "vencidos": sum(1 for r in rows if r["estado"]["nivel"] == "vencido"),
        "proximos": sum(1 for r in rows if r["estado"]["nivel"] == "proximo"),
        "ok": sum(1 for r in rows if r["estado"]["nivel"] == "ok"),
        "sin_programar": total_sin,
        "total": len(rows),
    }
    return rows, resumen


# ------------------------------------------------------------- recordatorios

def mensaje_preventivo(moto: Moto, estado: dict) -> Tuple[str, str]:
    titulo = site_service.site_title()
    cliente = moto.cliente
    nombre = cliente.nombre if cliente else "cliente"
    moto_info = f"{moto.marca} {moto.modelo}"
    asunto = f"{titulo}: Service preventivo {'vencido' if estado['nivel'] == 'vencido' else 'proximo'} - {moto_info}"
    cuerpo = (
        f"Hola {nombre},\n\n"
        f"Te recordamos que el service preventivo de tu {moto_info}"
        + (f" (placa {moto.placa})" if moto.placa else "")
        + f" esta {estado['nivel_label'].lower()}.\n"
        + (f"Detalle: {estado['detalle']}\n" if estado["detalle"] else "")
        + "\nAgenda tu cita respondiendo a este mensaje o visitandonos.\n"
        + titulo
    )
    return asunto, cuerpo


def _referencia(moto: Moto, canal: str) -> str:
    fecha = moto.proximo_service_fecha.isoformat() if moto.proximo_service_fecha else "sin-fecha"
    km = moto.proximo_service_km or "sin-km"
    return f"preventivo:{moto.id}:{fecha}:{km}:{canal}"


def _ya_recordado(db: Session, referencia: str) -> bool:
    return (
        db.query(Notificacion.id)
        .filter(Notificacion.referencia == referencia, Notificacion.estado == "enviado")
        .first()
        is not None
    )


def notificar_preventivo(db: Session, moto: Moto, canal: str,
                         automatica: bool = False) -> dict:
    config = _config(db)
    estado = evaluar_moto(moto, config)
    asunto, texto = mensaje_preventivo(moto, estado)
    cliente: Optional[Cliente] = moto.cliente
    referencia = _referencia(moto, canal)

    if automatica and _ya_recordado(db, referencia):
        return {"canal": canal, "estado": "omitido", "error": "ya recordado"}

    destinatario = ""
    if canal == "email":
        destinatario = (cliente.email if cliente else "") or ""
        if not destinatario:
            skip = "El cliente no tiene email registrado"
            estado_log = "omitido" if automatica else "fallido"
            _log_preventivo(db, canal, estado_log, asunto, texto, "-", skip, referencia, moto)
            return {"canal": canal, "estado": estado_log, "error": skip}
        ok, detalle = notificacion_service.enviar_email(destinatario, asunto, texto)
    elif canal == "telegram":
        destinatario = (cliente.telegram_chat_id if cliente else "") or ""
        if not destinatario:
            skip = "El cliente no tiene chat de Telegram registrado"
            estado_log = "omitido" if automatica else "fallido"
            _log_preventivo(db, canal, estado_log, asunto, texto, "-", skip, referencia, moto)
            return {"canal": canal, "estado": estado_log, "error": skip}
        ok, detalle = notificacion_service.enviar_telegram(destinatario, texto)
    else:
        return {"canal": canal, "estado": "fallido", "error": f"Canal no soportado: {canal}"}

    estado_log = "enviado" if ok else "fallido"
    _log_preventivo(db, canal, estado_log, asunto, texto,
                    destinatario, None if ok else detalle, referencia, moto)
    return {"canal": canal, "estado": estado_log, "error": None if ok else detalle}


def _log_preventivo(db: Session, canal: str, estado: str, asunto: str, mensaje: str,
                    destinatario: str, error: Optional[str], referencia: str,
                    moto: Moto) -> None:
    db.add(Notificacion(
        canal=canal,
        estado=estado,
        asunto=asunto,
        mensaje=mensaje,
        destinatario=destinatario,
        error=error or None,
        referencia=referencia,
        motorcycle_id=moto.id,
        cliente_id=moto.client_id,
    ))
    db.commit()


def enviar_recordatorios_pendientes(db: Session) -> int:
    """Aviso automatico (email/telegram) para preventivos vencidos/proximos.
    Dedupe por referencia: una sola vez por ciclo de service."""
    config = _config(db)
    hoy = date.today()
    filas, _ = get_panel(db, hoy)
    enviados = 0
    for fila in filas:
        if not fila["estado"]["requiere_aviso"]:
            continue
        moto = fila["moto"]
        cliente = fila["cliente"]
        if not cliente:
            continue
        if config.notif_email_auto and cliente.email:
            r = notificar_preventivo(db, moto, "email", automatica=True)
            if r["estado"] == "enviado":
                enviados += 1
        if config.notif_telegram_auto and cliente.telegram_chat_id:
            r = notificar_preventivo(db, moto, "telegram", automatica=True)
            if r["estado"] == "enviado":
                enviados += 1
    return enviados
