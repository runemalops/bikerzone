"""Tests para los fixes criticos del bug report."""
import pytest
import os
from unittest.mock import patch


class TestSearchOrderUrl:
    """Critical #1: search.py links usan {id} en vez de {codigo}."""

    def test_search_orden_url_uses_codigo(self, client, admin_user, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio

        client.post("/login", data={"email": "admin@test.com", "password": "admin123"})

        orden = OrdenServicio(
            codigo="BZ-2026-99999",
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Falla de frenos",
            estado="received",
        )
        db.add(orden)
        db.commit()
        db.refresh(orden)

        response = client.get("/api/search?q=BZ-2026")
        assert response.status_code == 200
        data = response.json()
        orden_results = [r for r in data["results"] if r["type"] == "orden"]
        assert len(orden_results) > 0
        assert orden_results[0]["url"] == f"/ordenes/{orden.codigo}"
        assert orden_results[0]["url"] != f"/ordenes/{orden.id}"

    def test_search_orden_url_nunca_usa_id(self, client, admin_user, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio

        client.post("/login", data={"email": "admin@test.com", "password": "admin123"})

        orden = OrdenServicio(
            codigo="BZ-2026-88888",
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Test",
            estado="received",
        )
        db.add(orden)
        db.commit()

        response = client.get("/api/search?q=BZ-2026")
        data = response.json()
        for r in data["results"]:
            if r["type"] == "orden":
                assert "/ordenes/" in r["url"]
                assert r["url"].split("/ordenes/")[1] == orden.codigo


class TestSearchAuthentication:
    """Critical #2: /api/search no tenia autenticacion."""

    def test_search_requires_auth(self, client):
        response = client.get("/api/search?q=test", follow_redirects=False)
        assert response.status_code == 302

    def test_search_with_auth_works(self, client, admin_user):
        client.post("/login", data={"email": "admin@test.com", "password": "admin123"})
        response = client.get("/api/search?q=test")
        assert response.status_code == 200
        assert "results" in response.json()


class TestConfigSecurity:
    """Critical #33 y #34: SECRET_KEY y ADMIN_PASSWORD hardcodeadas."""

    def test_get_secret_rejects_insecure_secret_key(self):
        from app.config import _get_secret
        result = _get_secret("SECRET_KEY", "cambia-esta-clave-secreta")
        assert result != "cambia-esta-clave-secreta"
        assert len(result) == 64

    def test_get_secret_rejects_insecure_admin_password(self):
        from app.config import _get_secret
        result = _get_secret("ADMIN_PASSWORD", "admin123")
        assert result != "admin123"
        assert result == ""

    def test_get_secret_generates_key_for_empty(self):
        from app.config import _get_secret
        result = _get_secret("SECRET_KEY", "")
        assert len(result) == 64

    def test_get_secret_generates_key_for_none(self):
        from app.config import _get_secret
        result = _get_secret("SECRET_KEY", None)
        assert len(result) == 64

    def test_get_secret_passes_through_valid_value(self):
        from app.config import _get_secret
        with patch.dict(os.environ, {"SECRET_KEY": "my-secure-key-abc"}):
            result = _get_secret("SECRET_KEY", "")
            assert result == "my-secure-key-abc"

    def test_get_secret_passes_through_valid_password(self):
        from app.config import _get_secret
        with patch.dict(os.environ, {"ADMIN_PASSWORD": "secure-password-456"}):
            result = _get_secret("ADMIN_PASSWORD", "")
            assert result == "secure-password-456"

    def test_settings_secret_key_not_insecure_default(self):
        from app.config import settings
        assert settings.SECRET_KEY != "cambia-esta-clave-secreta"
        assert len(settings.SECRET_KEY) == 64


class TestNITFieldFix:
    """Batch1 #5: NIT/RFC field mismatch — data loss."""

    def test_crear_cliente_con_nit(self, client, admin_user):
        client.post("/login", data={"email": "admin@test.com", "password": "admin123"})
        response = client.post(
            "/clientes/nueva",
            data={
                "nombre": "Cliente NIT",
                "telefono": "555-1111",
                "email": "nit@test.com",
                "nit": "1234567-8",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_nit_se_guarda_en_db(self, client, admin_user, db):
        from app.models.cliente import Cliente

        client.post("/login", data={"email": "admin@test.com", "password": "admin123"})
        client.post(
            "/clientes/nueva",
            data={
                "nombre": "Cliente NIT DB",
                "nit": "9876543-2",
            },
            follow_redirects=False,
        )
        cliente = db.query(Cliente).filter(Cliente.nombre == "Cliente NIT DB").first()
        assert cliente is not None
        assert cliente.nit == "9876543-2"

    def test_nit_aparece_en_detalle(self, client, auth_headers, sample_cliente, db):
        sample_cliente.nit = "1111111-1"
        db.commit()
        db.refresh(sample_cliente)

        response = client.get(f"/clientes/{sample_cliente.id}", cookies=auth_headers)
        assert response.status_code == 200
        assert "1111111-1" in response.text

    def test_editar_nit(self, client, auth_headers, sample_cliente):
        response = client.post(
            f"/clientes/{sample_cliente.id}/editar",
            data={
                "nombre": "Cliente Actualizado",
                "nit": "2222222-2",
            },
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert response.status_code == 303


class TestConfirmarOrdenStockGuard:
    """Batch1 #2: confirmar_orden stock puede ir negativo."""

    def test_confirmar_orden_stock_insuficiente(self, client, auth_headers, sample_cliente, sample_moto, sample_repuesto, db):
        from app.models.orden_servicio import OrdenServicio
        from app.models.orden_repuesto import OrdenRepuesto

        client.post("/login", data={"email": "admin@test.com", "password": "admin123"})

        orden = OrdenServicio(
            codigo="BZ-2026-77777",
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Falla test",
            estado="received",
        )
        db.add(orden)
        db.flush()

        item = OrdenRepuesto(
            service_order_id=orden.id,
            part_id=sample_repuesto.id,
            cantidad=100,
            precio_unitario=250.0,
            subtotal=25000.0,
        )
        db.add(item)
        db.commit()

        response = client.post(
            f"/ordenes/{orden.codigo}/confirmar",
            data={"observaciones": "Test stock insuficiente"},
            follow_redirects=False,
        )
        assert response.status_code == 400

    def test_confirmar_orden_stock_suficiente(self, client, auth_headers, sample_cliente, sample_moto, sample_repuesto, db):
        from app.models.orden_servicio import OrdenServicio
        from app.models.orden_repuesto import OrdenRepuesto

        client.post("/login", data={"email": "admin@test.com", "password": "admin123"})

        orden = OrdenServicio(
            codigo="BZ-2026-66666",
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Falla test ok",
            estado="received",
        )
        db.add(orden)
        db.flush()

        item = OrdenRepuesto(
            service_order_id=orden.id,
            part_id=sample_repuesto.id,
            cantidad=2,
            precio_unitario=250.0,
            subtotal=500.0,
        )
        db.add(item)
        db.commit()

        stock_antes = sample_repuesto.stock_actual
        response = client.post(
            f"/ordenes/{orden.codigo}/confirmar",
            data={"observaciones": "Test stock suficiente"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        db.refresh(sample_repuesto)
        assert sample_repuesto.stock_actual == stock_antes - 2


class TestDeleteLastAdmin:
    """Batch1 #4: Borrar el ultimo admin bloquea el sistema."""

    def test_no_puede_eliminar_ultimo_admin(self, client, auth_headers, admin_user, db):
        from app.models.usuario import Usuario
        from sqlalchemy import func

        admin_count = db.query(func.count(Usuario.id)).filter(
            Usuario.rol == "admin", Usuario.activo == True
        ).scalar()
        assert admin_count == 1

        response = client.post(
            f"/usuarios/{admin_user.id}/eliminar",
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert response.status_code == 400

    def test_puede_eliminar_admin_si_hay_mas(self, client, auth_headers, admin_user, db):
        from app.models.usuario import Usuario
        from app.services.auth_service import get_password_hash

        admin2 = Usuario(
            nombre="Admin 2",
            email="admin2@test.com",
            password_hash=get_password_hash("admin123"),
            rol="admin",
        )
        db.add(admin2)
        db.commit()
        db.refresh(admin2)

        response = client.post(
            f"/usuarios/{admin2.id}/eliminar",
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_no_puede_desactivar_a_si_mismo(self, client, auth_headers, admin_user):
        response = client.post(
            f"/usuarios/{admin_user.id}/toggle",
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert response.status_code == 400


class TestActivoCheckbox:
    """Batch1 #6: El checkbox de activo nunca se puede desmarcar."""

    def test_desactivar_usuario(self, client, admin_user, db):
        from app.models.usuario import Usuario

        client.post("/login", data={"email": "admin@test.com", "password": "admin123"})
        response = client.post(
            f"/usuarios/{admin_user.id}/editar",
            data={
                "nombre": admin_user.nombre,
                "email": admin_user.email,
                "rol": "admin",
            },
            follow_redirects=False,
        )
        assert response.status_code in (302, 303)
        db.refresh(admin_user)
        assert admin_user.activo is False

    def test_activar_usuario(self, client, admin_user, db):
        from app.models.usuario import Usuario

        client.post("/login", data={"email": "admin@test.com", "password": "admin123"})
        response = client.post(
            f"/usuarios/{admin_user.id}/editar",
            data={
                "nombre": admin_user.nombre,
                "email": admin_user.email,
                "rol": "admin",
                "activo": "on",
            },
            follow_redirects=False,
        )
        assert response.status_code in (302, 303)
        db.expire_all()
        updated = db.query(Usuario).filter(Usuario.id == admin_user.id).first()
        assert updated.activo is True


class TestPOIndexError:
    """Batch1 #7: IndexError en creacion de orden de compra."""

    def test_crear_orden_compra_con_detalles(self, client, auth_headers, sample_proveedor, sample_repuesto):
        response = client.post(
            "/ordenes-compra/nueva",
            data={
                "supplier_id": sample_proveedor.id,
                "notas": "Test order",
                "repuestos_ids": [str(sample_repuesto.id)],
                "cantidades": ["5"],
                "precios": ["200.00"],
            },
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_crear_orden_compra_arrays_vacios(self, client, auth_headers, sample_proveedor):
        response = client.post(
            "/ordenes-compra/nueva",
            data={
                "supplier_id": sample_proveedor.id,
                "notas": "Empty order",
                "repuestos_ids": "",
                "cantidades": "",
                "precios": "",
            },
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "error" in response.text.lower() or "debe incluir" in response.text.lower()
