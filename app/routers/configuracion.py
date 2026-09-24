import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.site_config import DEFAULT_SITE_LOGO, DEFAULT_SITE_TITLE, SiteConfig
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.services import site_service
from app.template_config import templates

router = APIRouter(prefix="/configuracion", tags=["configuracion"])

UPLOAD_DIR = "app/static/img/uploads"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"}
MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2MB


def require_admin(user: Usuario):
    if user.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden acceder")


@router.get("", response_class=HTMLResponse)
async def configuracion_form(
    request: Request,
    ok: int = 0,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    require_admin(user)
    config = site_service.get_site_config(db)
    from app.config import settings
    return templates.TemplateResponse(
        "configuracion/index.html",
        {
            "request": request,
            "user": user,
            "config": config,
            "smtp_configurado": bool(settings.SMTP_HOST and settings.SMTP_FROM),
            "telegram_configurado": bool(settings.TELEGRAM_BOT_TOKEN),
            "success": "Configuracion guardada" if ok else None,
        },
    )


@router.post("/notificaciones", response_class=HTMLResponse)
async def guardar_notificaciones(
    request: Request,
    notif_email_auto: str | None = Form(None),
    notif_telegram_auto: str | None = Form(None),
    preventivo_dias_anticipacion: str = Form("7"),
    preventivo_km_anticipacion: str = Form("500"),
    preventivo_km_intervalo: str = Form("5000"),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    require_admin(user)

    try:
        dias = int(preventivo_dias_anticipacion)
        km = int(preventivo_km_anticipacion)
        intervalo = int(preventivo_km_intervalo)
    except ValueError:
        return _form_response(request, user, site_service.get_site_config(db), db,
                              error="Los valores de anticipacion deben ser numeros")
    if not (1 <= dias <= 365) or not (0 <= km <= 100000):
        return _form_response(request, user, site_service.get_site_config(db), db,
                              error="Dias: 1-365. Kilometros: 0-100000")
    if not (0 <= intervalo <= 100000):
        return _form_response(request, user, site_service.get_site_config(db), db,
                              error="Intervalo de servicio: 0-100000 km")

    config = site_service.get_site_config(db)
    config.notif_email_auto = bool(notif_email_auto)
    config.notif_telegram_auto = bool(notif_telegram_auto)
    config.preventivo_dias_anticipacion = dias
    config.preventivo_km_anticipacion = km
    config.preventivo_km_intervalo = intervalo
    db.commit()
    site_service.invalidate_cache()
    return RedirectResponse(url="/configuracion?ok=1", status_code=303)


@router.post("", response_class=HTMLResponse)
async def guardar_configuracion(
    request: Request,
    site_title: str = Form(...),
    logo: UploadFile | None = File(None),
    restore_logo: str | None = Form(None),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    require_admin(user)

    title = site_title.strip()
    if not title or len(title) > 80:
        return _form_response(request, user, site_service.get_site_config(db), db,
                              error="El titulo debe tener entre 1 y 80 caracteres")

    config = site_service.get_site_config(db)
    config.site_title = title

    if restore_logo:
        _delete_custom_logo(config.site_logo)
        config.site_logo = DEFAULT_SITE_LOGO
    elif logo is not None and logo.filename:
        ext = os.path.splitext(logo.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return _form_response(request, user, config, db,
                                  error="Formato de logo no valido. Usa PNG, JPG, SVG, WEBP o GIF")
        data = await logo.read()
        if len(data) > MAX_LOGO_BYTES:
            return _form_response(request, user, config, db,
                                  error="El logo no puede superar 2MB")
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        path = os.path.join(UPLOAD_DIR, f"logo_{uuid.uuid4().hex}{ext}")
        with open(path, "wb") as f:
            f.write(data)
        _delete_custom_logo(config.site_logo)
        config.site_logo = f"/static/img/uploads/{os.path.basename(path)}"

    db.commit()
    site_service.invalidate_cache()
    return RedirectResponse(url="/configuracion?ok=1", status_code=303)


def _form_response(request, user, config, db, error: str):
    return templates.TemplateResponse(
        "configuracion/index.html",
        {"request": request, "user": user, "config": config, "error": error},
        status_code=400,
    )


def _delete_custom_logo(current_path: str | None):
    if not current_path or current_path == DEFAULT_SITE_LOGO:
        return
    if not current_path.startswith("/static/img/uploads/"):
        return
    file_path = os.path.join("app/static/img/uploads", os.path.basename(current_path))
    try:
        os.remove(file_path)
    except OSError:
        pass
