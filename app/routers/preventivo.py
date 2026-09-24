import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.services import preventivo_service
from app.template_config import templates

router = APIRouter(prefix="/preventivo", tags=["preventivo"])


@router.get("", response_class=HTMLResponse)
async def panel_preventivo(
    request: Request,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    filas, resumen = preventivo_service.get_panel(db)

    success = error = None
    notif = request.query_params.get("notif")
    if notif:
        if notif.startswith("ok:"):
            canal = notif.split(":")[1]
            label = {"email": "Email", "telegram": "Telegram"}.get(canal, canal)
            success = f"Recordatorio enviado por {label}"
        elif notif.startswith("err:") and notif.count(":") >= 2:
            canal = notif.split(":")[1]
            motivo = urllib.parse.unquote(notif.split(":", 2)[2])
            label = {"email": "Email", "telegram": "Telegram"}.get(canal, canal)
            error = f"No se pudo enviar por {label}: {motivo}"

    return templates.TemplateResponse(
        "preventivo/index.html",
        {
            "request": request,
            "user": user,
            "filas": filas,
            "resumen": resumen,
            "success": success,
            "error": error,
        },
    )


@router.post("/{moto_id}/recordatorio/{canal}")
def enviar_recordatorio(
    moto_id: int,
    canal: str,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    from app.models.moto import Moto

    if canal not in ("email", "telegram"):
        raise HTTPException(status_code=400, detail="Canal no soportado")

    moto = db.query(Moto).filter(Moto.id == moto_id).first()
    if not moto:
        raise HTTPException(status_code=404, detail="Moto no encontrada")

    r = preventivo_service.notificar_preventivo(db, moto, canal, automatica=False)
    if r["estado"] == "enviado":
        url = f"/preventivo?notif=ok:{canal}"
    else:
        motivo = urllib.parse.quote(r.get("error") or "Error desconocido", safe="")
        url = f"/preventivo?notif=err:{canal}:{motivo}"
    return RedirectResponse(url=url, status_code=303)
