from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.schemas.orden_compra import (
    OrdenCompraCreate,
    OrdenCompraDetalleCreate,
    EstadoCompraUpdate,
    ESTADOS_COMPRA,
    FLUJO_ESTADOS_COMPRA,
)
from app.services import orden_compra_service
from app.template_config import templates

router = APIRouter(prefix="/ordenes-compra", tags=["ordenes_compra"])


@router.get("", response_class=HTMLResponse)
async def lista_ordenes_compra(
    request: Request,
    search: str = "",
    estado: str = "",
    proveedor_id: int = Query(None),
    page: int = 1,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    ordenes, total = orden_compra_service.get_ordenes_compra(
        db,
        search=search,
        estado=estado or None,
        proveedor_id=proveedor_id,
        page=page,
    )
    total_pages = max(1, (total + 19) // 20)

    return templates.TemplateResponse(
        "ordenes_compra/lista.html",
        {
            "request": request,
            "user": user,
            "ordenes": ordenes,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search,
            "estado": estado,
            "estados": ESTADOS_COMPRA,
        },
    )


@router.get("/nueva", response_class=HTMLResponse)
async def nueva_orden_compra_form(
    request: Request,
    proveedor_id: int = Query(None),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    proveedores = orden_compra_service.getProveedoresList(db)
    repuestos = orden_compra_service.getRepuestosList(db)

    return templates.TemplateResponse(
        "ordenes_compra/formulario.html",
        {
            "request": request,
            "user": user,
            "orden": None,
            "proveedores": proveedores,
            "repuestos": repuestos,
            "proveedor_id": proveedor_id,
        },
    )


@router.post("/nueva")
async def crear_orden_compra(
    request: Request,
    supplier_id: int = Form(...),
    notas: str = Form(""),
    repuestos_ids: list = Form([]),
    cantidades: list = Form([]),
    precios: list = Form([]),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    detalles = []
    for i, rep_id in enumerate(repuestos_ids):
        if rep_id and cantidades[i] and precios[i]:
            detalles.append(OrdenCompraDetalleCreate(
                part_id=int(rep_id),
                cantidad=int(cantidades[i]),
                precio_unitario=float(precios[i]),
            ))

    data = OrdenCompraCreate(
        supplier_id=supplier_id,
        notas=notas or None,
        detalles=detalles,
    )
    orden = orden_compra_service.create_orden_compra(db, data, user.id)
    return RedirectResponse(url=f"/ordenes-compra/{orden.codigo}", status_code=303)


@router.get("/{codigo}", response_class=HTMLResponse)
async def detalle_orden_compra(
    request: Request,
    codigo: str,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    orden = orden_compra_service.get_orden_compra(db, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    detalles = orden_compra_service.get_detalles_orden(db, orden.id)
    estados_posibles = FLUJO_ESTADOS_COMPRA.get(orden.estado, [])

    return templates.TemplateResponse(
        "ordenes_compra/detalle.html",
        {
            "request": request,
            "user": user,
            "orden": orden,
            "detalles": detalles,
            "estados_posibles": estados_posibles,
            "estados_labels": ESTADOS_COMPRA,
        },
    )


@router.post("/{codigo}/cambiar-estado")
async def cambiar_estado(
    request: Request,
    codigo: str,
    nuevo_estado: str = Form(...),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    orden = orden_compra_service.get_orden_compra(db, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    success, message = orden_compra_service.cambiar_estado_orden_compra(
        db, orden.id, nuevo_estado
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return RedirectResponse(url=f"/ordenes-compra/{codigo}", status_code=303)


@router.post("/{codigo}/recibir")
async def recibir_mercancia(
    request: Request,
    codigo: str,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    orden = orden_compra_service.get_orden_compra(db, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    success, message = orden_compra_service.recibir_mercancia(db, orden.id)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return RedirectResponse(url=f"/ordenes-compra/{codigo}", status_code=303)
