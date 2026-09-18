from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.services import reporte_service
from app.template_config import templates

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    if user.rol == "admin":
        stats = reporte_service.get_dashboard_stats(db)
        ordenes_estado = reporte_service.get_ordenes_por_estado(db)
        ordenes_mes = reporte_service.get_ordenes_por_mes(db)

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": user,
                "stats": stats,
                "ordenes_estado": ordenes_estado,
                "ordenes_mes": ordenes_mes,
            },
        )
    else:
        # Technician view
        stats = reporte_service.get_tecnico_stats(db, user.id)
        ordenes_estado = reporte_service.get_ordenes_tecnico_por_estado(db, user.id)
        ordenes_recientes = reporte_service.get_ordenes_tecnico_recientes(db, user.id)

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": user,
                "stats": stats,
                "ordenes_estado": ordenes_estado,
                "ordenes_recientes": ordenes_recientes,
            },
        )
