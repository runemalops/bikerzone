from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import usuario as usuario_model
from app.routers import auth as auth_router
from app.routers import clientes as clientes_router
from app.routers import motos as motos_router
from app.routers import ordenes as ordenes_router
from app.routers import repuestos as repuestos_router
from app.routers import proveedores as proveedores_router
from app.routers import ordenes_compra as ordenes_compra_router
from app.routers import dashboard as dashboard_router
from app.routers import reportes as reportes_router
from app.routers import search as search_router
from app.routers import usuarios as usuarios_router
from app.routers import configuracion as configuracion_router
from app.routers import preventivo as preventivo_router

import os


def ensure_admin():
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = SessionLocal()
    try:
        admin = db.query(usuario_model.Usuario).filter(
            usuario_model.Usuario.email == settings.ADMIN_EMAIL
        ).first()
        if not admin:
            admin = usuario_model.Usuario(
                nombre="Administrador",
                email=settings.ADMIN_EMAIL,
                password_hash=pwd_context.hash(settings.ADMIN_PASSWORD),
                rol="admin",
            )
            db.add(admin)
            db.commit()
            print(f"[BikerZone] Admin inicial creado: {settings.ADMIN_EMAIL}")
        else:
            print(f"[BikerZone] Admin ya existe: {settings.ADMIN_EMAIL}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_admin()

    import asyncio

    async def recordatorios_preventivos():
        # primera pasada tras 60s, luego cada 6 horas
        await asyncio.sleep(60)
        while True:
            try:
                db = SessionLocal()
                try:
                    from app.services import preventivo_service

                    await asyncio.to_thread(preventivo_service.enviar_recordatorios_pendientes, db)
                finally:
                    db.close()
            except Exception:
                pass
            await asyncio.sleep(6 * 3600)

    tarea = asyncio.create_task(recordatorios_preventivos())
    yield
    tarea.cancel()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs" if settings.IS_DEVELOPMENT else None,
    redoc_url="/redoc" if settings.IS_DEVELOPMENT else None,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_router.router)
app.include_router(clientes_router.router)
app.include_router(motos_router.router)
app.include_router(ordenes_router.router)
app.include_router(repuestos_router.router)
app.include_router(proveedores_router.router)
app.include_router(ordenes_compra_router.router)
app.include_router(dashboard_router.router)
app.include_router(reportes_router.router)
app.include_router(search_router.router)
app.include_router(usuarios_router.router)
app.include_router(configuracion_router.router)
app.include_router(preventivo_router.router)


@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/login")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION}
