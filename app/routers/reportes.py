from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.services import reporte_service
from app.services import export_service
from app.template_config import templates

router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get("", response_class=HTMLResponse)
async def index_reportes(
    request: Request,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "reportes/index.html",
        {"request": request, "user": user},
    )


@router.get("/ventas", response_class=HTMLResponse)
async def reporte_ventas(
    request: Request,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    stats = reporte_service.get_dashboard_stats(db)
    ordenes_mes = reporte_service.get_ordenes_por_mes(db)
    top_clientes = reporte_service.get_top_clientes(db)
    ventas_tecnico = reporte_service.get_ventas_por_tecnico(db)

    return templates.TemplateResponse(
        "reportes/ventas.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "ordenes_mes": ordenes_mes,
            "top_clientes": top_clientes,
            "ventas_tecnico": ventas_tecnico,
        },
    )


@router.get("/inventario", response_class=HTMLResponse)
async def reporte_inventario(
    request: Request,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    stats = reporte_service.get_inventario_stats(db)
    stock_categoria = reporte_service.get_stock_por_categoria(db)
    stock_bajo = reporte_service.get_stock_bajo_list(db)

    return templates.TemplateResponse(
        "reportes/inventario.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "stock_categoria": stock_categoria,
            "stock_bajo": stock_bajo,
        },
    )


@router.get("/compras", response_class=HTMLResponse)
async def reporte_compras(
    request: Request,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    compras_mes = reporte_service.get_compras_por_mes(db)
    total_compras = sum(c["total"] for c in compras_mes)

    return templates.TemplateResponse(
        "reportes/compras.html",
        {
            "request": request,
            "user": user,
            "compras_mes": compras_mes,
            "total_compras": total_compras,
        },
    )


@router.get("/productividad", response_class=HTMLResponse)
async def reporte_productividad(
    request: Request,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    tiempos = reporte_service.get_tiempos_reparacion(db)
    ordenes_tecnico = reporte_service.get_ordenes_por_tecnico(db)
    stats = reporte_service.get_dashboard_stats(db)

    return templates.TemplateResponse(
        "reportes/productividad.html",
        {
            "request": request,
            "user": user,
            "tiempos": tiempos,
            "ordenes_tecnico": ordenes_tecnico,
            "stats": stats,
        },
    )


@router.get("/export/ordenes/csv")
async def exportar_ordenes_csv(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    csv_content = export_service.export_ordenes_csv(db)

    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=ordenes_servicio.csv"},
    )


@router.get("/export/inventario/csv")
async def exportar_inventario_csv(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    csv_content = export_service.export_inventario_csv(db)

    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=inventario.csv"},
    )


@router.get("/export/clientes/csv")
async def exportar_clientes_csv(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    csv_content = export_service.export_clientes_csv(db)

    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=clientes.csv"},
    )
