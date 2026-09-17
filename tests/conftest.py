import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.moto import Moto
from app.models.orden_servicio import OrdenServicio
from app.models.repuesto import Repuesto
from app.models.proveedor import Proveedor
from app.services.auth_service import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_user(db):
    user = db.query(Usuario).filter(Usuario.email == "admin@test.com").first()
    if not user:
        user = Usuario(
            nombre="Admin Test",
            email="admin@test.com",
            password_hash=get_password_hash("admin123"),
            rol="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def tecnico_user(db):
    user = db.query(Usuario).filter(Usuario.email == "tecnico@test.com").first()
    if not user:
        user = Usuario(
            nombre="Tecnico Test",
            email="tecnico@test.com",
            password_hash=get_password_hash("tecnico123"),
            rol="tecnico",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client):
    response = client.post("/login", data={"email": "admin@test.com", "password": "admin123"})
    assert response.status_code == 303
    cookies = dict(response.cookies)
    return cookies


@pytest.fixture
def sample_cliente(db):
    cliente = Cliente(
        nombre="Cliente Prueba",
        telefono="555-0001",
        email="cliente@test.com",
        direccion="Calle Test 123",
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@pytest.fixture
def sample_moto(db, sample_cliente):
    moto = Moto(
        client_id=sample_cliente.id,
        marca="Honda",
        modelo="CBR600",
        placa="ABC-123",
        anio=2020,
        kilometraje=15000,
        color="Negro",
        numero_serie="SN12345",
    )
    db.add(moto)
    db.commit()
    db.refresh(moto)
    return moto


@pytest.fixture
def sample_repuesto(db):
    repuesto = Repuesto(
        codigo="FILT-001",
        nombre="Filtro de Aceite",
        categoria="Filtros",
        marca="Honda",
        descripcion="Filtro de aceite original",
        precio_compra=150.00,
        precio_venta=250.00,
        stock_actual=20,
        stock_minimo=5,
        ubicacion="Estante A1",
    )
    db.add(repuesto)
    db.commit()
    db.refresh(repuesto)
    return repuesto


@pytest.fixture
def sample_proveedor(db):
    proveedor = Proveedor(
        nombre="Proveedor Test",
        email="proveedor@test.com",
        telefono="555-0002",
        direccion="Av. Industrial 456",
        persona_contacto="Juan Perez",
    )
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return proveedor
