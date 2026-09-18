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
    precio_final: Optional[float] = None
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
    "received": ["diagnosed", "cancelled"],
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


def codificar_falla_reportada(servicio_tipo: str, fallas_seleccionadas: list, descripcion_libre: str) -> str:
    """Codifica el tipo de servicio y fallas seleccionadas en el campo falla_reportada.
    Formato: [CATEGORIA: Falla1, Falla2] descripcion libre"""
    partes = []
    if servicio_tipo and servicio_tipo in SERVICIOS_CATALOGO:
        label = SERVICIOS_CATALOGO[servicio_tipo]["label"]
        if fallas_seleccionadas:
            partes.append(f"[{label}: {', '.join(fallas_seleccionadas)}]")
        else:
            partes.append(f"[{label}]")
    if descripcion_libre:
        partes.append(descripcion_libre)
    return " ".join(partes) if partes else ""


def decodificar_falla_reportada(falla_texto: str) -> dict:
    """Decodifica el campo falla_reportada para extraer categoria y fallas.
    Returns: { 'servicio_tipo': key, 'servicio_label': label, 'fallas': [...], 'descripcion': str }"""
    import re

    resultado = {
        "servicio_tipo": "",
        "servicio_label": "",
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

    # Buscar la categoria en el catalogo
    for key, cat in SERVICIOS_CATALOGO.items():
        if cat["label"] == contenido_parentesis:
            resultado["servicio_tipo"] = key
            resultado["servicio_label"] = cat["label"]
            return resultado

    # Si no matcheo exacto, intentar extraer fallas separadas por coma
    if ": " in contenido_parentesis:
        label_part, fallas_part = contenido_parentesis.split(": ", 1)
        resultado["servicio_label"] = label_part
        resultado["fallas"] = [f.strip() for f in fallas_part.split(", ") if f.strip()]
        for key, cat in SERVICIOS_CATALOGO.items():
            if cat["label"] == label_part:
                resultado["servicio_tipo"] = key
                break
    else:
        resultado["servicio_label"] = contenido_parentesis

    return resultado
