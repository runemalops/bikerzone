from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.schemas.cliente import ClienteCreate, ClienteUpdate
from app.services import cliente_service
from app.template_config import templates

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("", response_class=HTMLResponse)
async def lista_clientes(
    request: Request,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    clientes, total = cliente_service.get_clientes(db, search=search, page=page)
    total_pages = max(1, (total + 19) // 20)

    return templates.TemplateResponse(
        "clientes/lista.html",
        {
            "request": request,
            "user": user,
            "clientes": clientes,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search,
        },
    )


@router.get("/nueva", response_class=HTMLResponse)
async def nueva_cliente_form(
    request: Request,
    user: Usuario = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "clientes/formulario.html",
        {"request": request, "user": user, "cliente": None},
    )


@router.post("/nueva")
async def crear_cliente(
    request: Request,
    nombre: str = Form(...),
    telefono: str = Form(""),
    email: str = Form(""),
    direccion: str = Form(""),
    nit: str = Form(""),
    notas: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    data = ClienteCreate(
        nombre=nombre,
        telefono=telefono or None,
        email=email or None,
        direccion=direccion or None,
        nit=nit or None,
        notas=notas or None,
    )
    cliente = cliente_service.create_cliente(db, data)
    return RedirectResponse(url=f"/clientes/{cliente.id}", status_code=303)


@router.get("/{cliente_id}", response_class=HTMLResponse)
async def detalle_cliente(
    request: Request,
    cliente_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    cliente = cliente_service.get_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    ordenes = cliente_service.get_cliente_ordenes(db, cliente_id)
    motos = cliente_service.get_cliente_motos(db, cliente_id)

    return templates.TemplateResponse(
        "clientes/detalle.html",
        {
            "request": request,
            "user": user,
            "cliente": cliente,
            "ordenes": ordenes,
            "motos": motos,
        },
    )


@router.get("/{cliente_id}/editar", response_class=HTMLResponse)
async def editar_cliente_form(
    request: Request,
    cliente_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    cliente = cliente_service.get_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return templates.TemplateResponse(
        "clientes/formulario.html",
        {"request": request, "user": user, "cliente": cliente},
    )


@router.post("/{cliente_id}/editar")
async def actualizar_cliente(
    request: Request,
    cliente_id: int,
    nombre: str = Form(...),
    telefono: str = Form(""),
    email: str = Form(""),
    direccion: str = Form(""),
    nit: str = Form(""),
    notas: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    data = ClienteUpdate(
        nombre=nombre,
        telefono=telefono or None,
        email=email or None,
        direccion=direccion or None,
        nit=nit or None,
        notas=notas or None,
    )
    cliente = cliente_service.update_cliente(db, cliente_id, data)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return RedirectResponse(url=f"/clientes/{cliente_id}", status_code=303)


@router.post("/{cliente_id}/eliminar")
async def eliminar_cliente(
    request: Request,
    cliente_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    if user.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo admins pueden eliminar")

    deleted = cliente_service.delete_cliente(db, cliente_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return RedirectResponse(url="/clientes", status_code=303)
