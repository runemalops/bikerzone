from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.repuesto import Repuesto
from app.schemas.repuesto import RepuestoCreate, RepuestoUpdate


def get_repuestos(
    db: Session,
    search: Optional[str] = None,
    categoria: Optional[str] = None,
    stock_bajo: bool = False,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[dict], int]:
    query = db.query(Repuesto).filter(Repuesto.activo == True)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Repuesto.codigo.ilike(search_filter)) |
            (Repuesto.nombre.ilike(search_filter)) |
            (Repuesto.marca.ilike(search_filter)) |
            (Repuesto.descripcion.ilike(search_filter))
        )

    if categoria:
        query = query.filter(Repuesto.categoria == categoria)

    if stock_bajo:
        query = query.filter(Repuesto.stock_actual <= Repuesto.stock_minimo)

    total = query.count()
    repuestos = query.order_by(Repuesto.nombre).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    result = []
    for r in repuestos:
        if r.stock_actual == 0:
            estado = "out"
        elif r.stock_actual <= r.stock_minimo:
            estado = "low"
        else:
            estado = "ok"

        result.append({
            "id": r.id,
            "codigo": r.codigo,
            "nombre": r.nombre,
            "categoria": r.categoria,
            "marca": r.marca,
            "stock_actual": r.stock_actual,
            "stock_minimo": r.stock_minimo,
            "precio_venta": float(r.precio_venta) if r.precio_venta else None,
            "estado_stock": estado,
        })

    return result, total


def get_repuesto(db: Session, repuesto_id: int) -> Optional[Repuesto]:
    return db.query(Repuesto).filter(Repuesto.id == repuesto_id).first()


def get_repuesto_by_codigo(db: Session, codigo: str) -> Optional[Repuesto]:
    return db.query(Repuesto).filter(Repuesto.codigo == codigo).first()


def create_repuesto(db: Session, data: RepuestoCreate) -> Repuesto:
    repuesto = Repuesto(**data.model_dump())
    db.add(repuesto)
    db.commit()
    db.refresh(repuesto)
    return repuesto


def update_repuesto(db: Session, repuesto_id: int, data: RepuestoUpdate) -> Optional[Repuesto]:
    repuesto = db.query(Repuesto).filter(Repuesto.id == repuesto_id).first()
    if not repuesto:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(repuesto, key, value)

    db.commit()
    db.refresh(repuesto)
    return repuesto


def update_stock(
    db: Session,
    repuesto_id: int,
    cantidad: int,
    tipo: str,
) -> Tuple[bool, str]:
    repuesto = db.query(Repuesto).filter(Repuesto.id == repuesto_id).first()
    if not repuesto:
        return False, "Repuesto no encontrado"

    if tipo == "entrada":
        repuesto.stock_actual += cantidad
    elif tipo == "salida":
        disponible = repuesto.stock_actual - repuesto.stock_reservado
        if disponible < cantidad:
            return False, f"Stock insuficiente. Disponible: {disponible}, reservado: {repuesto.stock_reservado}"
        repuesto.stock_actual -= cantidad
    else:
        return False, "Tipo no valido (entrada/salida)"

    db.commit()
    return True, f"Stock actualizado: {repuesto.stock_actual}"


def delete_repuesto(db: Session, repuesto_id: int) -> bool:
    repuesto = db.query(Repuesto).filter(Repuesto.id == repuesto_id).first()
    if not repuesto:
        return False

    repuesto.activo = False
    db.commit()
    return True


def get_stock_bajo(db: Session) -> List[dict]:
    repuestos = db.query(Repuesto).filter(
        Repuesto.activo == True,
        Repuesto.stock_actual <= Repuesto.stock_minimo,
    ).order_by(Repuesto.stock_actual).all()

    result = []
    for r in repuestos:
        if r.stock_actual == 0:
            estado = "out"
        else:
            estado = "low"
        result.append({
            "id": r.id,
            "codigo": r.codigo,
            "nombre": r.nombre,
            "categoria": r.categoria,
            "stock_actual": r.stock_actual,
            "stock_minimo": r.stock_minimo,
            "estado_stock": estado,
        })

    return result


def get_categorias(db: Session) -> list:
    result = db.query(Repuesto.categoria).filter(
        Repuesto.activo == True,
        Repuesto.categoria.isnot(None),
    ).distinct().all()
    return [r[0] for r in result if r[0]]


def get_stock_disponible(db: Session, repuesto_id: int) -> int:
    repuesto = db.query(Repuesto).filter(Repuesto.id == repuesto_id).first()
    if not repuesto:
        return 0
    return repuesto.stock_actual - repuesto.stock_reservado


def reservar_stock(
    db: Session,
    repuesto_id: int,
    cantidad: int,
) -> Tuple[bool, str]:
    repuesto = db.query(Repuesto).filter(Repuesto.id == repuesto_id).first()
    if not repuesto:
        return False, "Repuesto no encontrado"

    disponible = repuesto.stock_actual - repuesto.stock_reservado
    if disponible < cantidad:
        return False, f"Stock insuficiente. Disponible: {disponible}"

    repuesto.stock_reservado += cantidad
    db.commit()
    return True, f"Stock reservado: {cantidad} unidades"


def liberar_reserva(
    db: Session,
    repuesto_id: int,
    cantidad: int,
) -> Tuple[bool, str]:
    repuesto = db.query(Repuesto).filter(Repuesto.id == repuesto_id).first()
    if not repuesto:
        return False, "Repuesto no encontrado"

    if repuesto.stock_reservado < cantidad:
        return False, f"Reserva insuficiente. Reservado: {repuesto.stock_reservado}"

    repuesto.stock_reservado -= cantidad
    db.commit()
    return True, f"Reserva liberada: {cantidad} unidades"


def confirmar_reserva(
    db: Session,
    repuesto_id: int,
    cantidad: int,
) -> Tuple[bool, str]:
    repuesto = db.query(Repuesto).filter(Repuesto.id == repuesto_id).first()
    if not repuesto:
        return False, "Repuesto no encontrado"

    if repuesto.stock_reservado < cantidad:
        return False, f"Reserva insuficiente. Reservado: {repuesto.stock_reservado}"

    if repuesto.stock_actual < cantidad:
        return False, f"Stock insuficiente. Actual: {repuesto.stock_actual}"

    repuesto.stock_actual -= cantidad
    repuesto.stock_reservado -= cantidad
    db.commit()
    return True, f"Stock confirmado: {cantidad} unidades descontadas"
