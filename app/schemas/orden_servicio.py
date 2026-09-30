from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class OrdenServicioBase(BaseModel):
    client_id: int
    motorcycle_id: int
    falla_reportada: str
    kilometraje_entrada: Optional[int] = None


class OrdenServicioCreate(OrdenServicioBase):
    technician_id: Optional[int] = None


class OrdenServicioUpdate(BaseModel):
    diagnostico: Optional[str] = None
    presupuesto: Optional[float] = None
    mano_obra: Optional[float] = None
    kilometraje_salida: Optional[int] = None


class EstadoUpdate(BaseModel):
    nuevo_estado: str
    observaciones: Optional[str] = None


class HistorialEstadoResponse(BaseModel):
    id: int
    estado: str
    observaciones: Optional[str] = None
    fecha: datetime
    usuario_nombre: str = ""

    model_config = {"from_attributes": True}


class OrdenRepuestoResponse(BaseModel):
    id: int
    repuesto_nombre: str
    cantidad: int
    precio_unitario: float
    subtotal: float

    model_config = {"from_attributes": True}


class OrdenServicioResponse(OrdenServicioBase):
    id: int
    codigo: str
    estado: str
    diagnostico: Optional[str] = None
    presupuesto: Optional[float] = None
    precio_final: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrdenServicioListResponse(BaseModel):
    id: int
    codigo: str
    cliente_nombre: str
    moto_info: str
    estado: str
    falla_reportada: str
    presupuesto: Optional[float] = None
    precio_final: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Estados validos del flujo
ESTADOS_VALIDOS = [
    "received",
    "diagnosed",
    "quote_sent",
    "quote_approved",
    "quote_rejected",
    "in_progress",
    "repairing",
    "awaiting_part",
    "ready",
    "delivered",
    "cancelled",
]

FLUJO_ESTADOS = {
    "received": ["diagnosed", "in_progress", "cancelled"],
    "diagnosed": ["quote_sent", "cancelled"],
    "quote_sent": ["quote_approved", "quote_rejected"],
    "quote_approved": ["in_progress"],
    "quote_rejected": ["cancelled"],
    "in_progress": ["repairing", "awaiting_part"],
    "repairing": ["ready", "awaiting_part"],
    "awaiting_part": ["repairing"],
    "ready": ["delivered"],
    "delivered": [],
    "cancelled": [],
}

ESTADO_LABELS = {
    "received": "Recibido",
    "diagnosed": "Diagnosticado",
    "quote_sent": "Presupuesto Enviado",
    "quote_approved": "Presupuesto Aprobado",
    "quote_rejected": "Presupuesto Rechazado",
    "in_progress": "En Proceso",
    "repairing": "Reparando",
    "awaiting_part": "Esperando Pieza",
    "ready": "Listo",
    "delivered": "Entregado",
    "cancelled": "Cancelado",
}

# --- Catalogo de Servicios y Fallas ---
# Cada categoria tiene un icono y una lista de fallas/servicios tipicos.

SERVICIOS_CATALOGO = {
    "mantenimiento": {
        "label": "Mantenimiento Preventivo",
        "subtitle": "Aceite, filtros, ajustes",
        "icon": "wrench",
        "color": "#2980b9",
        "fallas": [
            "Cambio de aceite y filtro",
            "Ajuste de valvulas",
            "Cambio de filtro de aire",
            "Cambio de bujias",
            "Limpieza de carburador / inyectores",
            "Cambio de liquido de frenos",
            "Revision de cadena y pinones",
            "Cambio de neumaticos",
            "Alineacion y balanceo",
            "Revision de suspension",
            "Cambio de liquido de refrigeracion",
            "Limpieza general",
            "Servicio a los 1,000 km",
            "Servicio a los 5,000 km",
            "Servicio a los 10,000 km",
        ],
    },
    "frenos": {
        "label": "Frenos",
        "subtitle": "Pastillas, discos, lineas",
        "icon": "disc",
        "color": "#c0392b",
        "fallas": [
            "Pastillas desgastadas",
            "Discos rayados o deformados",
            "Linea de frenos con aire",
            "Cilindro maestro defectuoso",
            "Freno delantero no funciona",
            "Freno trasero no funciona",
            "Freno bloqueado",
            "Vibracion al frenar",
            "Liquido de frenos sucio o viejo",
            "Caliper atascado",
        ],
    },
    "motor": {
        "label": "Motor",
        "subtitle": "Compresion, aceite, arranque",
        "icon": "cog",
        "color": "#e67e22",
        "fallas": [
            "No enciende",
            "Sobrecalentamiento",
            "Fuga de aceite",
            "Ruidos extraños en motor",
            "Perdida de potencia",
            "Consumo excesivo de combustible",
            "Humo azul (quema aceite)",
            "Humo negro (mezcla rica)",
            "Compresion baja",
            "Cadena de distribicion suelta",
            "Tensionador de cadena defectuoso",
            "Juntas quemadas",
        ],
    },
    "electrico": {
        "label": "Sistema Electrico",
        "subtitle": "Bateria, luces, cableado",
        "icon": "zap",
        "color": "#f1c40f",
        "fallas": [
            "Bateria descargada o muerta",
            "Alternador / generador defectuoso",
            "Luces delanteras quemadas",
            "Luces traseras quemadas",
            "Direccionales no funcionan",
            "Corto circuito",
            "Switch de encendido defectuoso",
            "Marcha no funciona",
            "Bocina no suena",
            "Tablero sin funcionar",
            "Cableado dañado",
            "Regulador de voltaje defectuoso",
        ],
    },
    "transmision": {
        "label": "Transmision y Embrague",
        "subtitle": "Cadena, pinones, caja",
        "icon": "layers",
        "color": "#9b59b6",
        "fallas": [
            "Embrague duro",
            "Embrague patina",
            "Cambio de marcha duro",
            "No entra en primera",
            "Se sale de marcha",
            "Cadena suelta o floja",
            "Tensor de cadena defectuoso",
            "Pinones desgastados",
            "Piñon de arranque desgastado",
            "Eje de transmision flojo",
            "Rodamiento de caja defectuoso",
        ],
    },
    "suspension": {
        "label": "Suspension y Direccion",
        "subtitle": "Horquilla, amortiguadores",
        "icon": "move-vertical",
        "color": "#1abc9c",
        "fallas": [
            "Horquilla con fuga de aceite",
            "Horquilla suave (perdida de precarga)",
            "Amortiguador trasero defectuoso",
            "Rulemanes de direccion desgastados",
            "Triple tree flojo",
            "Direcccion se siente pesada",
            "Direcccion se siente floja",
            "Rodamientos de rueda desgastados",
            "Cubiertas de horquilla dañadas",
        ],
    },
    "carroceria": {
        "label": "Carroceria y Exterior",
        "subtitle": "Tanque, carenado, asiento",
        "icon": "shield",
        "color": "#34495e",
        "fallas": [
            "Rayones en tanque",
            "Rayones en carenado",
            "Espejo roto",
            "Carenado dañado",
            "Asiento rasgado",
            "Tablero agrietado",
            "Molduras sueltas",
            "Parabrisas rayado",
            "Guardabarros daliado",
            "Estribos doblados",
        ],
    },
    "otro": {
        "label": "Otro Servicio",
        "subtitle": "General, accesorios",
        "icon": "tool",
        "color": "#7f8c8d",
        "fallas": [
            "Revision general",
            "Diagnostico sin falla especifica",
            "Second opinion",
            "Instalacion de accesorios",
            "Ajustes generales",
            "Lavado y detallado",
            "Pre-entrega",
            "Revision pre-compra",
        ],
    },
}


def normalizar_tipos_servicio(servicio_tipo) -> list:
    """Acepta 'frenos,motor', ['frenos', 'motor'] o '' y devuelve las claves validas
    del catalogo, sin duplicados y en el orden recibido."""
    if isinstance(servicio_tipo, str):
        candidatos = servicio_tipo.split(",")
    elif isinstance(servicio_tipo, (list, tuple, set)):
        candidatos = list(servicio_tipo)
    else:
        candidatos = []

    tipos = []
    for item in candidatos:
        clave = str(item or "").strip()
        if clave in SERVICIOS_CATALOGO and clave not in tipos:
            tipos.append(clave)
    return tipos


def codificar_falla_reportada(servicio_tipo, fallas_seleccionadas: list, descripcion_libre: str) -> str:
    """Codifica uno o varios tipos de servicio y las fallas seleccionadas en el campo
    falla_reportada.
    Formato: [Tipo1 + Tipo2: Falla1, Falla2] descripcion libre"""
    etiquetas = [SERVICIOS_CATALOGO[clave]["label"] for clave in normalizar_tipos_servicio(servicio_tipo)]
    partes = []
    if etiquetas:
        base = " + ".join(etiquetas)
        fallas = [str(f).strip() for f in (fallas_seleccionadas or []) if str(f).strip()]
        if fallas:
            partes.append(f"[{base}: {', '.join(fallas)}]")
        else:
            partes.append(f"[{base}]")
    if descripcion_libre:
        partes.append(descripcion_libre)
    return " ".join(partes) if partes else ""


def decodificar_falla_reportada(falla_texto: str) -> dict:
    """Decodifica el campo falla_reportada para extraer tipos de servicio y fallas.

    Returns:
        servicio_tipos: claves del catalogo, una por tipo seleccionado
        servicio_labels: etiquetas tal como se guardaron
        servicio_tipo / servicio_label: primer tipo (compatibilidad con formatos anteriores)
        fallas: fallas seleccionadas
        descripcion: texto libre
    """
    import re

    resultado = {
        "servicio_tipo": "",
        "servicio_label": "",
        "servicio_tipos": [],
        "servicio_labels": [],
        "fallas": [],
        "descripcion": falla_texto or "",
    }

    if not falla_texto:
        return resultado

    match = re.match(r"^\[([^\]]+)\]\s*(.*)", falla_texto, re.DOTALL)
    if not match:
        return resultado

    contenido_parentesis = match.group(1).strip()
    resultado["descripcion"] = match.group(2).strip()

    etiquetas_part = contenido_parentesis
    if ": " in contenido_parentesis:
        etiquetas_part, fallas_part = contenido_parentesis.split(": ", 1)
        resultado["fallas"] = [f.strip() for f in fallas_part.split(", ") if f.strip()]

    for etiqueta in [e.strip() for e in etiquetas_part.split(" + ") if e.strip()]:
        if etiqueta in resultado["servicio_labels"]:
            continue
        resultado["servicio_labels"].append(etiqueta)
        for key, cat in SERVICIOS_CATALOGO.items():
            if cat["label"] == etiqueta:
                resultado["servicio_tipos"].append(key)
                break

    if resultado["servicio_tipos"]:
        resultado["servicio_tipo"] = resultado["servicio_tipos"][0]
    if resultado["servicio_labels"]:
        resultado["servicio_label"] = resultado["servicio_labels"][0]

    return resultado
