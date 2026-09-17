from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.schemas.moto import MotoCreate, MotoUpdate
from app.services import moto_service
from app.template_config import templates

router = APIRouter(prefix="/motos", tags=["motos"])


@router.get("", response_class=HTMLResponse)
async def lista_motos(
    request: Request,
    search: str = "",
    cliente_id: int = Query(None),
    page: int = 1,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    motos, total = moto_service.get_motos(db, search=search, client_id=cliente_id, page=page)
    total_pages = max(1, (total + 19) // 20)
    clientes = moto_service.get_clientes_list(db)

    return templates.TemplateResponse(
        "motos/lista.html",
        {
            "request": request,
            "user": user,
            "motos": motos,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search,
            "clientes": clientes,
            "cliente_id": cliente_id,
        },
    )


@router.get("/nueva", response_class=HTMLResponse)
async def nueva_moto_form(
    request: Request,
    cliente_id: int = Query(None),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    clientes = moto_service.get_clientes_list(db)
    return templates.TemplateResponse(
        "motos/formulario.html",
        {
            "request": request,
            "user": user,
            "moto": None,
            "clientes": clientes,
            "cliente_id": cliente_id,
        },
    )


@router.post("/nueva")
async def crear_moto(
    request: Request,
    client_id: int = Form(...),
    marca: str = Form(...),
    modelo: str = Form(...),
    anio: str = Form(""),
    placa: str = Form(""),
    color: str = Form(""),
    vin: str = Form(""),
    kilometraje: str = Form("0"),
    notas: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    data = MotoCreate(
        client_id=client_id,
        marca=marca,
        modelo=modelo,
        anio=int(anio) if anio else None,
        placa=placa or None,
        color=color or None,
        vin=vin or None,
        kilometraje=int(kilometraje) if kilometraje else 0,
        notas=notas or None,
    )
    moto = moto_service.create_moto(db, data)
    return RedirectResponse(url=f"/motos/{moto.id}", status_code=303)


@router.get("/{moto_id}", response_class=HTMLResponse)
async def detalle_moto(
    request: Request,
    moto_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    moto = moto_service.get_moto(db, moto_id)
    if not moto:
        raise HTTPException(status_code=404, detail="Moto no encontrada")

    ordenes = moto_service.get_moto_ordenes(db, moto_id)

    return templates.TemplateResponse(
        "motos/detalle.html",
        {
            "request": request,
            "user": user,
            "moto": moto,
            "ordenes": ordenes,
        },
    )


@router.get("/{moto_id}/editar", response_class=HTMLResponse)
async def editar_moto_form(
    request: Request,
    moto_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    moto = moto_service.get_moto(db, moto_id)
    if not moto:
        raise HTTPException(status_code=404, detail="Moto no encontrada")

    clientes = moto_service.get_clientes_list(db)
    return templates.TemplateResponse(
        "motos/formulario.html",
        {
            "request": request,
            "user": user,
            "moto": moto,
            "clientes": clientes,
            "cliente_id": None,
        },
    )


@router.post("/{moto_id}/editar")
async def actualizar_moto(
    request: Request,
    moto_id: int,
    client_id: int = Form(...),
    marca: str = Form(...),
    modelo: str = Form(...),
    anio: str = Form(""),
    placa: str = Form(""),
    color: str = Form(""),
    vin: str = Form(""),
    kilometraje: str = Form("0"),
    notas: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    data = MotoUpdate(
        marca=marca,
        modelo=modelo,
        anio=int(anio) if anio else None,
        placa=placa or None,
        color=color or None,
        vin=vin or None,
        kilometraje=int(kilometraje) if kilometraje else 0,
        notas=notas or None,
    )
    moto = moto_service.update_moto(db, moto_id, data)
    if not moto:
        raise HTTPException(status_code=404, detail="Moto no encontrada")

    return RedirectResponse(url=f"/motos/{moto_id}", status_code=303)


@router.post("/{moto_id}/eliminar")
async def eliminar_moto(
    request: Request,
    moto_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    if user.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo admins pueden eliminar")

    deleted = moto_service.delete_moto(db, moto_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Moto no encontrada")

    return RedirectResponse(url="/motos", status_code=303)
