from typing import List
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
    SERVICIOS_CATALOGO,
    codificar_falla_reportada,
    decodificar_falla_reportada,
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
    page = max(1, page)
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
            "catalogo_servicios": SERVICIOS_CATALOGO,
        },
    )


@router.post("/nueva")
async def crear_orden(
    request: Request,
    client_id: int = Form(...),
    motorcycle_id: int = Form(...),
    technician_id: str = Form(""),
    servicio_tipo: str = Form(""),
    fallas_seleccionadas: List[str] = Form([]),
    falla_reportada: str = Form(""),
    kilometraje_entrada: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    falla_completa = codificar_falla_reportada(servicio_tipo, fallas_seleccionadas, falla_reportada)
    data = OrdenServicioCreate(
        client_id=client_id,
        motorcycle_id=motorcycle_id,
        technician_id=int(technician_id) if technician_id and technician_id.strip().isdigit() else None,
        falla_reportada=falla_completa,
        kilometraje_entrada=int(kilometraje_entrada) if kilometraje_entrada and kilometraje_entrada.strip().isdigit() else None,
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
    subtotal_repuestos = sum(r['subtotal'] for r in repuestos)
    estados_posibles = FLUJO_ESTADOS.get(orden.estado, [])
    repuestos_list = orden_service.getRepuestosList(db)
    falla_decodificada = decodificar_falla_reportada(orden.falla_reportada)

    from app.services import notificacion_service

    notificaciones = notificacion_service.get_notificaciones_orden(db, orden.id)
    _, mensaje_wa = notificacion_service.mensaje_orden_lista(orden)
    wa_link = None
    if orden.cliente:
        wa_link = notificacion_service.link_whatsapp(orden.cliente.telefono, mensaje_wa)

    # resultados de envio manual (?notif=ok:email | ?notif=err:telegram:<motivo>)
    import urllib.parse

    success = error = None
    notif_param = request.query_params.get("notif")
    if notif_param:
        label = {"email": "Email", "telegram": "Telegram"}.get(
            notif_param.split(":")[1] if ":" in notif_param else "", "el canal")
        if notif_param.startswith("ok:"):
            success = f"Notificacion enviada por {label}"
        elif notif_param.startswith("err:") and notif_param.count(":") >= 2:
            canal = notif_param.split(":")[1]
            motivo = urllib.parse.unquote(notif_param.split(":", 2)[2])
            label = {"email": "Email", "telegram": "Telegram"}.get(canal, canal)
            error = f"No se pudo enviar por {label}: {motivo}"

    return templates.TemplateResponse(
        "ordenes/detalle.html",
        {
            "request": request,
            "user": user,
            "orden": orden,
            "historial": historial,
            "repuestos": repuestos,
            "subtotal_repuestos": subtotal_repuestos,
            "estados_posibles": estados_posibles,
            "estados_labels": ESTADO_LABELS,
            "repuestos_list": repuestos_list,
            "falla_decodificada": falla_decodificada,
            "catalogo_servicios": SERVICIOS_CATALOGO,
            "notificaciones": notificaciones,
            "wa_link": wa_link,
            "success": success,
            "error": error,
        },
    )


@router.post("/{codigo}/notificar/{canal}")
def notificar_orden(
    codigo: str,
    canal: str,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    import urllib.parse

    from app.services import notificacion_service

    if canal not in ("email", "telegram"):
        raise HTTPException(status_code=400, detail="Canal no soportado")

    orden = orden_service.get_orden(db, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    resultados = notificacion_service.notificar_orden_lista(db, orden, canal=canal)
    r = resultados[0] if resultados else {"estado": "fallido", "error": "Error inesperado"}

    if r["estado"] == "enviado":
        url = f"/ordenes/{codigo}?notif=ok:{canal}"
    else:
        motivo = urllib.parse.quote(r.get("error") or "Error desconocido", safe="")
        url = f"/ordenes/{codigo}?notif=err:{canal}:{motivo}"
    return RedirectResponse(url=url, status_code=303)


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
    mano_obra: str = Form(""),
    kilometraje_salida: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    orden = orden_service.get_orden(db, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    data = OrdenServicioUpdate(
        diagnostico=diagnostico or None,
        presupuesto=float(presupuesto) if presupuesto and presupuesto.replace('.', '', 1).isdigit() else None,
        mano_obra=float(mano_obra) if mano_obra and mano_obra.replace('.', '', 1).isdigit() else None,
        kilometraje_salida=int(kilometraje_salida) if kilometraje_salida and kilometraje_salida.strip().isdigit() else None,
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


@router.post("/{codigo}/eliminar-repuesto/{item_id}")
async def eliminar_repuesto(
    request: Request,
    codigo: str,
    item_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    orden = orden_service.get_orden(db, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    success, message = orden_service.remove_repuesto_orden(db, orden.id, item_id)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return RedirectResponse(url=f"/ordenes/{codigo}", status_code=303)


@router.post("/{codigo}/confirmar")
async def confirmar_orden(
    request: Request,
    codigo: str,
    observaciones: str = Form(""),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    orden = orden_service.get_orden(db, codigo)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    success, message = orden_service.confirmar_orden(
        db, orden.id, user.id, observaciones or None
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

    deleted = orden_service.delete_orden(db, orden.id)
    if not deleted:
        raise HTTPException(status_code=400, detail="No se puede eliminar una orden en estado activo")

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

    pdf_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf_path = tmp.name

        generar_pdf_orden(datos, pdf_path)

        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={codigo}.pdf"},
        )
    finally:
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)
