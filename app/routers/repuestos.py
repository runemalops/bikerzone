from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.schemas.repuesto import RepuestoCreate, RepuestoUpdate, StockUpdate, CATEGORIAS_REPUESTOS
from app.services import repuesto_service
from app.template_config import templates

router = APIRouter(prefix="/repuestos", tags=["repuestos"])


@router.get("", response_class=HTMLResponse)
async def lista_repuestos(
    request: Request,
    search: str = "",
    categoria: str = "",
    stock_bajo: bool = False,
    page: int = 1,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    page = max(1, page)
    repuestos, total = repuesto_service.get_repuestos(
        db,
        search=search,
        categoria=categoria or None,
        stock_bajo=stock_bajo,
        page=page,
    )
    total_pages = max(1, (total + 19) // 20)
    categorias = repuesto_service.get_categorias(db)

    return templates.TemplateResponse(
        "repuestos/lista.html",
        {
            "request": request,
            "user": user,
            "repuestos": repuestos,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search,
            "categoria": categoria,
            "stock_bajo": stock_bajo,
            "categorias": categorias,
            "categorias_list": CATEGORIAS_REPUESTOS,
        },
    )


@router.get("/stock-bajo", response_class=HTMLResponse)
async def lista_stock_bajo(
    request: Request,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    repuestos = repuesto_service.get_stock_bajo(db)

    return templates.TemplateResponse(
        "repuestos/lista.html",
        {
            "request": request,
            "user": user,
            "repuestos": repuestos,
            "total": len(repuestos),
            "page": 1,
            "total_pages": 1,
            "search": "",
            "categoria": "",
            "stock_bajo": True,
            "categorias": [],
            "categorias_list": CATEGORIAS_REPUESTOS,
        },
    )


@router.get("/nuevo", response_class=HTMLResponse)
async def nuevo_repuesto_form(
    request: Request,
    user: Usuario = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "repuestos/formulario.html",
        {
            "request": request,
            "user": user,
            "repuesto": None,
            "categorias": CATEGORIAS_REPUESTOS,
        },
    )


@router.post("/nuevo")
async def crear_repuesto(
    request: Request,
    codigo: str = Form(...),
    nombre: str = Form(...),
    descripcion: str = Form(""),
    categoria: str = Form(""),
    marca: str = Form(""),
    compatible_models: str = Form(""),
    stock_minimo: str = Form("3"),
    stock_actual: str = Form("0"),
    precio_compra: str = Form(""),
    precio_venta: str = Form(""),
    ubicacion: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    existing = repuesto_service.get_repuesto_by_codigo(db, codigo)
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un repuesto con ese codigo")

    data = RepuestoCreate(
        codigo=codigo,
        nombre=nombre,
        descripcion=descripcion or None,
        categoria=categoria or None,
        marca=marca or None,
        compatible_models=compatible_models or None,
        stock_minimo=int(stock_minimo) if stock_minimo else 3,
        stock_actual=int(stock_actual) if stock_actual else 0,
        precio_compra=float(precio_compra) if precio_compra else None,
        precio_venta=float(precio_venta) if precio_venta else None,
        ubicacion=ubicacion or None,
    )
    repuesto = repuesto_service.create_repuesto(db, data)
    return RedirectResponse(url=f"/repuestos/{repuesto.id}", status_code=303)


@router.get("/{repuesto_id}", response_class=HTMLResponse)
async def detalle_repuesto(
    request: Request,
    repuesto_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    repuesto = repuesto_service.get_repuesto(db, repuesto_id)
    if not repuesto:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado")

    return templates.TemplateResponse(
        "repuestos/detalle.html",
        {
            "request": request,
            "user": user,
            "repuesto": repuesto,
        },
    )


@router.get("/{repuesto_id}/editar", response_class=HTMLResponse)
async def editar_repuesto_form(
    request: Request,
    repuesto_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    repuesto = repuesto_service.get_repuesto(db, repuesto_id)
    if not repuesto:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado")

    return templates.TemplateResponse(
        "repuestos/formulario.html",
        {
            "request": request,
            "user": user,
            "repuesto": repuesto,
            "categorias": CATEGORIAS_REPUESTOS,
        },
    )


@router.post("/{repuesto_id}/editar")
async def actualizar_repuesto(
    request: Request,
    repuesto_id: int,
    codigo: str = Form(...),
    nombre: str = Form(...),
    descripcion: str = Form(""),
    categoria: str = Form(""),
    marca: str = Form(""),
    compatible_models: str = Form(""),
    stock_minimo: str = Form("3"),
    stock_actual: str = Form("0"),
    precio_compra: str = Form(""),
    precio_venta: str = Form(""),
    ubicacion: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    data = RepuestoUpdate(
        codigo=codigo,
        nombre=nombre,
        descripcion=descripcion or None,
        categoria=categoria or None,
        marca=marca or None,
        compatible_models=compatible_models or None,
        stock_minimo=int(stock_minimo) if stock_minimo else 3,
        stock_actual=int(stock_actual) if stock_actual else 0,
        precio_compra=float(precio_compra) if precio_compra else None,
        precio_venta=float(precio_venta) if precio_venta else None,
        ubicacion=ubicacion or None,
    )
    repuesto = repuesto_service.update_repuesto(db, repuesto_id, data)
    if not repuesto:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado")

    return RedirectResponse(url=f"/repuestos/{repuesto_id}", status_code=303)


@router.post("/{repuesto_id}/stock")
async def actualizar_stock(
    request: Request,
    repuesto_id: int,
    cantidad: int = Form(...),
    tipo: str = Form(...),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    success, message = repuesto_service.update_stock(db, repuesto_id, cantidad, tipo)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return RedirectResponse(url=f"/repuestos/{repuesto_id}", status_code=303)


@router.post("/{repuesto_id}/eliminar")
async def eliminar_repuesto(
    request: Request,
    repuesto_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    if user.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo admins pueden eliminar")

    deleted = repuesto_service.delete_repuesto(db, repuesto_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado")

    return RedirectResponse(url="/repuestos", status_code=303)
