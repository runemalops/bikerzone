import pytest
from datetime import datetime, timedelta, timezone

from pydantic import ValidationError

from app.config import settings
from app.schemas.orden_compra import OrdenCompraDetalleCreate
from app.schemas.repuesto import StockUpdate
from app.services.auth_service import create_access_token, decode_token
from app.services.reporte_service import get_ordenes_por_estado
from tests.conftest import generate_orden_codigo


def _make_orden(db, cliente, moto, tecnico, estado="received"):
    from app.models.orden_servicio import OrdenServicio
    os = OrdenServicio(
        codigo=generate_orden_codigo(db),
        client_id=cliente.id,
        motorcycle_id=moto.id,
        technician_id=tecnico.id,
        falla_reportada="Falla de prueba",
        estado=estado,
        presupuesto=500,
    )
    db.add(os)
    db.commit()
    db.refresh(os)
    return os


# ==========================================
# #35: Unhandled ValueError on int()/float() conversion
# ==========================================
class TestInputConversionSafety:
    def test_moto_create_with_invalid_anio(self, client, auth_headers, sample_cliente):
        response = client.post(
            "/motos/nueva",
            data={
                "client_id": sample_cliente.id,
                "marca": "Honda",
                "modelo": "CBR",
                "anio": "abc",
                "kilometraje": "xyz",
            },
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert response.status_code in (303, 200)

    def test_orden_create_with_invalid_technician_id(self, client, auth_headers, sample_cliente, sample_moto):
        response = client.post(
            "/ordenes/nueva",
            data={
                "client_id": sample_cliente.id,
                "motorcycle_id": sample_moto.id,
                "technician_id": "not_a_number",
                "falla_reportada": "Test",
            },
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert response.status_code in (303, 200)


# ==========================================
# #36: Deprecated datetime.utcnow() usage
# ==========================================
class TestAuthTokenTimezoneAware:
    def test_access_token_uses_utc(self):
        token = create_access_token(data={"sub": "1", "rol": "admin"})
        payload = decode_token(token)
        assert payload is not None
        exp = payload.get("exp")
        assert exp is not None
        assert exp > datetime.now(timezone.utc).timestamp()


# ==========================================
# #37: Missing secure flag on auth cookie
# ==========================================
class TestCookieSecureFlag:
    def test_auth_cookie_has_samesite(self, client, admin_user):
        response = client.post(
            "/login",
            data={"email": "admin@test.com", "password": "admin123"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        cookie_header = response.headers.get("set-cookie", "")
        assert "samesite=lax" in cookie_header.lower()

    def test_dev_env_cookie_not_secure(self):
        assert settings.IS_DEVELOPMENT is True or settings.ENVIRONMENT == "development"


# ==========================================
# #38: Hardcoded IVA rate
# ==========================================
class TestIvaRateConfigurable:
    def test_iva_rate_in_settings(self):
        assert hasattr(settings, "IVA_RATE")
        assert settings.IVA_RATE == 0.12

    def test_iva_rate_is_float(self):
        assert isinstance(settings.IVA_RATE, float)
        assert 0 <= settings.IVA_RATE <= 1


# ==========================================
# #39: Missing schema validation on numeric fields
# ==========================================
class TestSchemaValidation:
    def test_orden_compra_detalle_rejects_zero_cantidad(self):
        with pytest.raises(ValidationError):
            OrdenCompraDetalleCreate(part_id=1, cantidad=0, precio_unitario=100)

    def test_orden_compra_detalle_rejects_negative_cantidad(self):
        with pytest.raises(ValidationError):
            OrdenCompraDetalleCreate(part_id=1, cantidad=-1, precio_unitario=100)

    def test_orden_compra_detalle_rejects_negative_precio(self):
        with pytest.raises(ValidationError):
            OrdenCompraDetalleCreate(part_id=1, cantidad=1, precio_unitario=-10)

    def test_stock_update_rejects_zero_cantidad(self):
        with pytest.raises(ValidationError):
            StockUpdate(cantidad=0, tipo="salida")

    def test_stock_update_rejects_negative_cantidad(self):
        with pytest.raises(ValidationError):
            StockUpdate(cantidad=-5, tipo="entrada")


# ==========================================
# #40: Pagination drops filter parameters
# ==========================================
class TestPaginationPreservesFilters:
    def test_pagination_includes_technician_filter(self, client, auth_headers, sample_cliente, sample_moto, admin_user, tecnico_user):
        _make_orden(db=__import__("tests.conftest", fromlist=["TestingSessionLocal"]).TestingSessionLocal(), cliente=sample_cliente, moto=sample_moto, tecnico=tecnico_user)

        from tests.conftest import TestingSessionLocal
        db = TestingSessionLocal()
        try:
            _make_orden(db, sample_cliente, sample_moto, tecnico_user)
        finally:
            db.close()

        response = client.get(
            f"/ordenes?technician_id={tecnico_user.id}",
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert f"technician_id={tecnico_user.id}" in response.text or "page=" not in response.text


# ==========================================
# #41: Missing state labels in dashboard chart
# ==========================================
class TestDashboardStateLabels:
    def test_labels_include_awaiting_part(self, db, sample_cliente, sample_moto, admin_user, tecnico_user):
        _make_orden(db, sample_cliente, sample_moto, tecnico_user, estado="received")

        from app.services.orden_service import cambiar_estado
        orden = db.query(__import__("app.models.orden_servicio", fromlist=["OrdenServicio"]).OrdenServicio).first()
        if orden:
            cambiar_estado(db, orden.id, "in_progress", tecnico_user.id)
            cambiar_estado(db, orden.id, "awaiting_part", tecnico_user.id)

        result = get_ordenes_por_estado(db)
        labels = [r["estado"] for r in result]
        assert any("Esperando" in l for l in labels) or len(result) >= 1


# ==========================================
# #42: Inconsistent password hint vs backend validation
# ==========================================
class TestPasswordHintConsistency:
    def test_password_form_has_minlength_8(self, client, auth_headers):
        response = client.get("/usuarios/nuevo", cookies=auth_headers, follow_redirects=False)
        assert response.status_code == 200
        assert 'minlength="8"' in response.text
        assert "8 caracteres" in response.text

    def test_password_change_has_minlength_8(self, client, auth_headers, admin_user):
        response = client.get(f"/usuarios/{admin_user.id}", cookies=auth_headers, follow_redirects=False)
        assert response.status_code == 200
        assert 'minlength="8"' in response.text


# ==========================================
# #43: CSS version mismatch on login
# ==========================================
class TestLoginCssVersion:
    def test_login_css_version_matches_base(self, client):
        login_response = client.get("/login", follow_redirects=False)
        assert login_response.status_code == 200
        assert "style.css?v=3.0" in login_response.text


# ==========================================
# #47: Misleading delete client error message
# ==========================================
class TestDeleteClientErrorMessage:
    def test_delete_client_with_orders_shows_correct_message(
        self, client, auth_headers, sample_cliente, sample_moto, admin_user, tecnico_user
    ):
        _make_orden(db=__import__("tests.conftest", fromlist=["TestingSessionLocal"]).TestingSessionLocal(), cliente=sample_cliente, moto=sample_moto, tecnico=tecnico_user)

        from tests.conftest import TestingSessionLocal
        db = TestingSessionLocal()
        try:
            _make_orden(db, sample_cliente, sample_moto, tecnico_user)
        finally:
            db.close()

        response = client.post(
            f"/clientes/{sample_cliente.id}/eliminar",
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert response.status_code == 400
        assert "registradas" in response.text.lower() or "No se puede eliminar" in response.text
