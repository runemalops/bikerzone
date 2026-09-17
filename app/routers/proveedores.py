from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.schemas.proveedor import ProveedorCreate, ProveedorUpdate
from app.services import proveedor_service
from app.template_config import templates

router = APIRouter(prefix="/proveedores", tags=["proveedores"])


@router.get("", response_class=HTMLResponse)
async def lista_proveedores(
    request: Request,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    proveedores, total = proveedor_service.get_proveedores(db, search=search, page=page)
    total_pages = max(1, (total + 19) // 20)

    return templates.TemplateResponse(
        "proveedores/lista.html",
        {
            "request": request,
            "user": user,
            "proveedores": proveedores,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search,
        },
    )


@router.get("/nuevo", response_class=HTMLResponse)
async def nuevo_proveedor_form(
    request: Request,
    user: Usuario = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "proveedores/formulario.html",
        {"request": request, "user": user, "proveedor": None},
    )


@router.post("/nuevo")
async def crear_proveedor(
    request: Request,
    nombre: str = Form(...),
    contacto: str = Form(""),
    telefono: str = Form(""),
    email: str = Form(""),
    direccion: str = Form(""),
    rfc: str = Form(""),
    notas: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    data = ProveedorCreate(
        nombre=nombre,
        contacto=contacto or None,
        telefono=telefono or None,
        email=email or None,
        direccion=direccion or None,
        rfc=rfc or None,
        notas=notas or None,
    )
    proveedor = proveedor_service.create_proveedor(db, data)
    return RedirectResponse(url=f"/proveedores/{proveedor.id}", status_code=303)


@router.get("/{proveedor_id}", response_class=HTMLResponse)
async def detalle_proveedor(
    request: Request,
    proveedor_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    proveedor = proveedor_service.get_proveedor(db, proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    ordenes = proveedor_service.get_proveedor_ordenes(db, proveedor_id)

    return templates.TemplateResponse(
        "proveedores/detalle.html",
        {
            "request": request,
            "user": user,
            "proveedor": proveedor,
            "ordenes": ordenes,
        },
    )


@router.get("/{proveedor_id}/editar", response_class=HTMLResponse)
async def editar_proveedor_form(
    request: Request,
    proveedor_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    proveedor = proveedor_service.get_proveedor(db, proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    return templates.TemplateResponse(
        "proveedores/formulario.html",
        {"request": request, "user": user, "proveedor": proveedor},
    )


@router.post("/{proveedor_id}/editar")
async def actualizar_proveedor(
    request: Request,
    proveedor_id: int,
    nombre: str = Form(...),
    contacto: str = Form(""),
    telefono: str = Form(""),
    email: str = Form(""),
    direccion: str = Form(""),
    rfc: str = Form(""),
    notas: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    data = ProveedorUpdate(
        nombre=nombre,
        contacto=contacto or None,
        telefono=telefono or None,
        email=email or None,
        direccion=direccion or None,
        rfc=rfc or None,
        notas=notas or None,
    )
    proveedor = proveedor_service.update_proveedor(db, proveedor_id, data)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    return RedirectResponse(url=f"/proveedores/{proveedor_id}", status_code=303)


@router.post("/{proveedor_id}/eliminar")
async def eliminar_proveedor(
    request: Request,
    proveedor_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    if user.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo admins pueden eliminar")

    deleted = proveedor_service.delete_proveedor(db, proveedor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    return RedirectResponse(url="/proveedores", status_code=303)
