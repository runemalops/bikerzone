from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.services import usuario_service
from app.template_config import templates

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def require_admin(user: Usuario):
    if user.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden acceder")


@router.get("", response_class=HTMLResponse)
async def lista_usuarios(
    request: Request,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    require_admin(user)

    usuarios, total = usuario_service.get_usuarios(db, search=search, page=page)
    total_pages = max(1, (total + 19) // 20)
    stats = usuario_service.get_usuarios_stats(db)

    return templates.TemplateResponse(
        "usuarios/lista.html",
        {
            "request": request,
            "user": user,
            "usuarios": usuarios,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search,
            "stats": stats,
        },
    )


@router.get("/nuevo", response_class=HTMLResponse)
async def nuevo_usuario_form(
    request: Request,
    user: Usuario = Depends(get_current_user),
):
    require_admin(user)

    return templates.TemplateResponse(
        "usuarios/formulario.html",
        {"request": request, "user": user, "usuario": None},
    )


@router.post("/nuevo")
async def crear_usuario(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    rol: str = Form("tecnico"),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    require_admin(user)

    existing = usuario_service.get_usuario_by_email(db, email)
    if existing:
        return templates.TemplateResponse(
            "usuarios/formulario.html",
            {
                "request": request,
                "user": user,
                "usuario": None,
                "error": "Ya existe un usuario con ese email",
            },
            status_code=400,
        )

    data = UsuarioCreate(nombre=nombre, email=email, password=password, rol=rol)
    nuevo = usuario_service.create_usuario(db, data)
    return RedirectResponse(url=f"/usuarios/{nuevo.id}", status_code=303)


@router.get("/{usuario_id}", response_class=HTMLResponse)
async def detalle_usuario(
    request: Request,
    usuario_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    require_admin(user)

    usuario = usuario_service.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return templates.TemplateResponse(
        "usuarios/detalle.html",
        {"request": request, "user": user, "usuario": usuario},
    )


@router.get("/{usuario_id}/editar", response_class=HTMLResponse)
async def editar_usuario_form(
    request: Request,
    usuario_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    require_admin(user)

    usuario = usuario_service.get_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return templates.TemplateResponse(
        "usuarios/formulario.html",
        {"request": request, "user": user, "usuario": usuario},
    )


@router.post("/{usuario_id}/editar")
async def actualizar_usuario(
    request: Request,
    usuario_id: int,
    nombre: str = Form(...),
    email: str = Form(...),
    rol: str = Form("tecnico"),
    activo: str = Form("on"),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    require_admin(user)

    existing = usuario_service.get_usuario_by_email(db, email)
    if existing and existing.id != usuario_id:
        return templates.TemplateResponse(
            "usuarios/formulario.html",
            {
                "request": request,
                "user": user,
                "usuario": usuario_service.get_usuario(db, usuario_id),
                "error": "Ya existe otro usuario con ese email",
            },
            status_code=400,
        )

    data = UsuarioUpdate(
        nombre=nombre,
        email=email,
        rol=rol,
        activo=activo == "on",
    )
    updated = usuario_service.update_usuario(db, usuario_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return RedirectResponse(url=f"/usuarios/{usuario_id}", status_code=303)


@router.post("/{usuario_id}/cambiar-password")
async def cambiar_password(
    request: Request,
    usuario_id: int,
    new_password: str = Form(...),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    require_admin(user)

    success = usuario_service.change_password(db, usuario_id, new_password)
    if not success:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return RedirectResponse(url=f"/usuarios/{usuario_id}", status_code=303)


@router.post("/{usuario_id}/toggle")
async def toggle_usuario(
    request: Request,
    usuario_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    require_admin(user)

    updated = usuario_service.toggle_usuario_activo(db, usuario_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return RedirectResponse(url=f"/usuarios/{usuario_id}", status_code=303)


@router.post("/{usuario_id}/eliminar")
async def eliminar_usuario(
    request: Request,
    usuario_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    require_admin(user)

    if user.id == usuario_id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta")

    deleted = usuario_service.delete_usuario(db, usuario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return RedirectResponse(url="/usuarios", status_code=303)
