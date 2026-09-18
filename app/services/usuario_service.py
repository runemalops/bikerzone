from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.services.auth_service import get_password_hash


def get_usuarios(
    db: Session,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[dict], int]:
    query = db.query(Usuario)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Usuario.nombre.ilike(search_filter))
            | (Usuario.email.ilike(search_filter))
            | (Usuario.rol.ilike(search_filter))
        )

    total = query.count()
    usuarios = query.order_by(Usuario.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    result = []
    for u in usuarios:
        result.append({
            "id": u.id,
            "nombre": u.nombre,
            "email": u.email,
            "rol": u.rol,
            "activo": u.activo,
            "created_at": u.created_at,
        })

    return result, total


def get_usuario(db: Session, usuario_id: int) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def get_usuario_by_email(db: Session, email: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.email == email).first()


def create_usuario(db: Session, data: UsuarioCreate) -> Usuario:
    usuario = Usuario(
        nombre=data.nombre,
        email=data.email,
        password_hash=get_password_hash(data.password),
        rol=data.rol,
        activo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def update_usuario(db: Session, usuario_id: int, data: UsuarioUpdate) -> Optional[Usuario]:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(usuario, key, value)

    db.commit()
    db.refresh(usuario)
    return usuario


def change_password(db: Session, usuario_id: int, new_password: str) -> bool:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return False

    usuario.password_hash = get_password_hash(new_password)
    db.commit()
    return True


def delete_usuario(db: Session, usuario_id: int) -> bool:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return False

    db.delete(usuario)
    db.commit()
    return True


def toggle_usuario_activo(db: Session, usuario_id: int) -> Optional[Usuario]:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return None

    usuario.activo = not usuario.activo
    db.commit()
    db.refresh(usuario)
    return usuario


def get_usuarios_stats(db: Session) -> dict:
    total = db.query(func.count(Usuario.id)).scalar() or 0
    admins = db.query(func.count(Usuario.id)).filter(Usuario.rol == "admin").scalar() or 0
    tecnicos = db.query(func.count(Usuario.id)).filter(Usuario.rol == "tecnico").scalar() or 0
    activos = db.query(func.count(Usuario.id)).filter(Usuario.activo == True).scalar() or 0

    return {
        "total": total,
        "admins": admins,
        "tecnicos": tecnicos,
        "activos": activos,
    }
