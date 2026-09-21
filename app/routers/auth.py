from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import LoginRequest, TokenResponse, UsuarioResponse
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_password_hash,
)
from app.config import settings
from app.template_config import templates

router = APIRouter()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Usuario:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=302, headers={"Location": "/login"})

    from app.services.auth_service import decode_token
    payload = decode_token(token.replace("Bearer ", ""))
    if not payload:
        raise HTTPException(status_code=302, headers={"Location": "/login"})

    user_id = payload.get("sub")
    user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if not user or not user.activo:
        raise HTTPException(status_code=302, headers={"Location": "/login"})

    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> Optional[Usuario]:
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, response: Response, db: Session = Depends(get_db)):
    form = await request.form()
    email = form.get("email", "")
    password = form.get("password", "")

    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Email o contrasena incorrectos"},
            status_code=401,
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "rol": user.rol},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        secure=not settings.IS_DEVELOPMENT,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token", samesite="lax")
    return response


@router.get("/api/auth/me")
async def get_me(user: Usuario = Depends(get_current_user)):
    return UsuarioResponse.model_validate(user)


@router.get("/api/auth/validate")
async def validate_token(user: Usuario = Depends(get_current_user)):
    return {"valid": True, "user_id": user.id, "rol": user.rol}
