from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session
import os
import tempfile

from app.database import get_db
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.schemas.orden_servicio import (
    OrdenServicioCreate,
    OrdenServicioUpdate,
    EstadoUpdate,
    FLUJO_ESTADOS,
    ESTADO_LABELS,
)
from app.services import orden_service
from app.services import export_service
from app.template_config import templates

router = APIRouter(prefix="/ordenes", tags=["ordenes"])


@router.get("", response_class=HTMLResponse)
async def lista_ordenes(
    request: Request,
    search: str = "",
    estado: str = "",
    technician_id: int = Query(None),
    client_id: int = Query(None),
    fecha_desde: str = "",
    fecha_hasta: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    ordenes, total = orden_service.get_ordenes(
        db,
        search=search,
        estado=estado or None,
        technician_id=technician_id,
        client_id=client_id,
        fecha_desde=fecha_desde or None,
        fecha_hasta=fecha_hasta or None,
        page=page,
    )
    total_pages = max(1, (total + 19) // 20)
    tecnicos = orden_service.getTecnicosList(db)

    return templates.TemplateResponse(
        "ordenes/lista.html",
        {
            "request": request,
            "user": user,
            "ordenes": ordenes,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "search": search,
            "estado": estado,
            "tecnico_id": technician_id,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "tecnicos": tecnicos,
            "estados": ESTADO_LABELS,
        },
    )


@router.get("/nueva", response_class=HTMLResponse)
async def nueva_orden_form(
    request: Request,
    client_id: int = Query(None),
    moto_id: int = Query(None),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    clientes = orden_service.getClientesList(db)
    motos = orden_service.getMotosList(db, client_id=client_id)
    tecnicos = orden_service.getTecnicosList(db)

    return templates.TemplateResponse(
        "ordenes/formulario.html",
        {
            "request": request,
            "user": user,
            "orden": None,
            "clientes": clientes,
            "motos": motos,
            "tecnicos": tecnicos,
            "client_id": client_id,
            "moto_id": moto_id,
        },
    )


@router.post("/nueva")
async def crear_orden(
    request: Request,
    client_id: int = Form(...),
    motorcycle_id: int = Form(...),
    technician_id: str = Form(""),
    falla_reportada: str = Form(...),
    kilometraje_entrada: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    data = OrdenServicioCreate(
        client_id=client_id,
        motorcycle_id=motorcycle_id,
        technician_id=int(technician_id) if technician_id else None,
        falla_reportada=falla_reportada,
        kilometraje_entrada=int(kilometraje_entrada) if kilometraje_entrada else None,
    )
    orden = orden_service.create_orden(db, data, user.id)
    return RedirectResponse(url=f"/ordenes/{orden.codigo}", status_code=303)


@router.get("/{codigo}", response_class=HTMLResponse)
async def detalle_orden(
    request: Request,
    codigo: str,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    orden = orden_service.get_orden(db, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    historial = orden_service.get_historial(db, orden.id)
    repuestos = orden_service.get_repuestos_orden(db, orden.id)
    estados_posibles = FLUJO_ESTADOS.get(orden.estado, [])
    repuestos_list = orden_service.getRepuestosList(db)

    return templates.TemplateResponse(
        "ordenes/detalle.html",
        {
            "request": request,
            "user": user,
            "orden": orden,
            "historial": historial,
            "repuestos": repuestos,
            "estados_posibles": estados_posibles,
            "estados_labels": ESTADO_LABELS,
            "repuestos_list": repuestos_list,
        },
    )


@router.post("/{codigo}/cambiar-estado")
async def cambiar_estado(
    request: Request,
    codigo: str,
    nuevo_estado: str = Form(...),
    observaciones: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    orden = orden_service.get_orden(db, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    success, message = orden_service.cambiar_estado(
        db, orden.id, nuevo_estado, user.id, observaciones or None
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return RedirectResponse(url=f"/ordenes/{codigo}", status_code=303)


@router.post("/{codigo}/editar")
async def actualizar_orden(
    request: Request,
    codigo: str,
    diagnostico: str = Form(""),
    presupuesto: str = Form(""),
    precio_final: str = Form(""),
    kilometraje_salida: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    orden = orden_service.get_orden(db, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    data = OrdenServicioUpdate(
        diagnostico=diagnostico or None,
        presupuesto=float(presupuesto) if presupuesto else None,
        precio_final=float(precio_final) if precio_final else None,
        kilometraje_salida=int(kilometraje_salida) if kilometraje_salida else None,
    )
    orden_service.update_orden(db, orden.id, data)

    return RedirectResponse(url=f"/ordenes/{codigo}", status_code=303)


@router.post("/{codigo}/agregar-repuesto")
async def agregar_repuesto(
    request: Request,
    codigo: str,
    repuesto_id: int = Form(...),
    cantidad: int = Form(...),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    orden = orden_service.get_orden(db, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    success, message = orden_service.add_repuesto_orden(
        db, orden.id, repuesto_id, cantidad
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return RedirectResponse(url=f"/ordenes/{codigo}", status_code=303)


@router.post("/{codigo}/eliminar")
async def eliminar_orden(
    request: Request,
    codigo: str,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    if user.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo admins pueden eliminar")

    orden = orden_service.get_orden(db, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    orden_service.delete_orden(db, orden.id)
    return RedirectResponse(url="/ordenes", status_code=303)


@router.get("/api/motos/{client_id}")
async def get_motos_cliente(
    client_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    motos = orden_service.getMotosList(db, client_id=client_id)
    return [{"id": m.id, "marca": m.marca, "modelo": m.modelo, "placa": m.placa} for m in motos]


@router.get("/export/csv")
async def exportar_ordenes_csv(
    estado: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    csv_content = export_service.export_ordenes_csv(
        db,
        estado=estado or None,
        fecha_desde=fecha_desde or None,
        fecha_hasta=fecha_hasta or None,
    )

    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=ordenes_servicio.csv"},
    )


@router.get("/{codigo}/pdf")
async def generar_pdf_orden(
    codigo: str,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    datos = export_service.generate_orden_pdf_data(db, codigo)
    if not datos:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    from app.services.pdf_generator import generar_pdf_orden

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf_path = tmp.name

    generar_pdf_orden(datos, pdf_path)

    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()

    os.unlink(pdf_path)

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={codigo}.pdf"},
    )
