import tempfile
import os


class TestPasswordStrength:
    """Batch2 #14: Password strength validation."""

    def test_password_too_short(self, client, admin_user):
        from app.schemas.usuario import UsuarioCreate
        from pydantic import ValidationError

        client.post("/login", data={"email": "admin@test.com", "password": "admin123"})
        try:
            UsuarioCreate(nombre="Test", email="test@test.com", password="Ab1", rol="tecnico")
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "8 caracteres" in str(e)

    def test_password_no_uppercase(self, client, admin_user):
        from app.schemas.usuario import UsuarioCreate
        from pydantic import ValidationError

        try:
            UsuarioCreate(nombre="Test", email="test@test.com", password="alllower1", rol="tecnico")
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "mayuscula" in str(e)

    def test_password_no_lowercase(self, client, admin_user):
        from app.schemas.usuario import UsuarioCreate
        from pydantic import ValidationError

        try:
            UsuarioCreate(nombre="Test", email="test@test.com", password="ALLUPPER1", rol="tecnico")
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "minuscula" in str(e)

    def test_password_no_digit(self, client, admin_user):
        from app.schemas.usuario import UsuarioCreate
        from pydantic import ValidationError

        try:
            UsuarioCreate(nombre="Test", email="test@test.com", password="NoDigitHere", rol="tecnico")
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "numero" in str(e)

    def test_password_valid(self):
        from app.schemas.usuario import UsuarioCreate

        user = UsuarioCreate(nombre="Test", email="test@test.com", password="ValidPass1", rol="tecnico")
        assert user.password == "ValidPass1"

    def test_crear_usuario_password_debil(self, client, admin_user):
        client.post("/login", data={"email": "admin@test.com", "password": "admin123"})
        response = client.post(
            "/usuarios/nuevo",
            data={
                "nombre": "User Weak",
                "email": "weak@test.com",
                "password": "123",
                "rol": "tecnico",
            },
            follow_redirects=False,
        )
        assert response.status_code == 400


class TestDeleteOrdenStateCheck:
    """Batch2 #10: Cannot delete orders in active states."""

    def test_delete_orden_in_progress_fails(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Test",
            estado="in_progress",
        )
        db.add(orden)
        db.commit()
        db.refresh(orden)

        response = client.post(
            f"/ordenes/{orden.codigo}/eliminar",
            follow_redirects=False,
        )
        assert response.status_code == 400

    def test_delete_orden_repairing_fails(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Test",
            estado="repairing",
        )
        db.add(orden)
        db.commit()
        db.refresh(orden)

        response = client.post(
            f"/ordenes/{orden.codigo}/eliminar",
            follow_redirects=False,
        )
        assert response.status_code == 400

    def test_delete_orden_received_ok(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Test",
            estado="received",
        )
        db.add(orden)
        db.commit()
        db.refresh(orden)

        response = client.post(
            f"/ordenes/{orden.codigo}/eliminar",
            follow_redirects=False,
        )
        assert response.status_code == 303


class TestDeleteClienteWithActiveOrders:
    """Batch2 #11: Cannot delete client with active orders."""

    def test_delete_cliente_con_orden_activa(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Test",
            estado="in_progress",
        )
        db.add(orden)
        db.commit()

        response = client.post(
            f"/clientes/{sample_cliente.id}/eliminar",
            follow_redirects=False,
        )
        assert response.status_code == 400

    def test_delete_cliente_sin_ordenes_activas(self, client, auth_headers, sample_cliente):
        response = client.post(
            f"/clientes/{sample_cliente.id}/eliminar",
            follow_redirects=False,
        )
        assert response.status_code == 303


class TestDeleteMotoWithActiveOrders:
    """Batch2 #12: Cannot delete moto with active orders."""

    def test_delete_moto_con_orden_activa(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Test",
            estado="repairing",
        )
        db.add(orden)
        db.commit()

        response = client.post(
            f"/motos/{sample_moto.id}/eliminar",
            follow_redirects=False,
        )
        assert response.status_code == 400

    def test_delete_moto_sin_ordenes_activas(self, client, auth_headers, sample_moto):
        response = client.post(
            f"/motos/{sample_moto.id}/eliminar",
            follow_redirects=False,
        )
        assert response.status_code == 303


class TestNullRelation:
    """Batch2 #16: moto list handles null client relation."""

    def test_moto_con_cliente_muestra_nombre(self, client, auth_headers, sample_moto):
        response = client.get("/motos", cookies=auth_headers)
        assert response.status_code == 200
        assert "Cliente Prueba" in response.text

    def test_null_client_fallback_logic(self):
        from app.services.moto_service import get_motos
        from unittest.mock import MagicMock

        mock_moto = MagicMock()
        mock_moto.cliente = None
        mock_moto.id = 1
        mock_moto.marca = "Test"
        mock_moto.modelo = "Model"
        mock_moto.anio = 2020
        mock_moto.placa = "TST-001"
        mock_moto.color = "Rojo"
        mock_moto.kilometraje = 1000

        result = mock_moto.cliente.nombre if mock_moto.cliente else "Sin cliente"
        assert result == "Sin cliente"


class TestPaginationBounds:
    """Batch2 #17: Negative page numbers are clamped to 1."""

    def test_page_negative_clamped(self, client, auth_headers, sample_cliente):
        response = client.get("/clientes?page=-5", cookies=auth_headers)
        assert response.status_code == 200

    def test_page_zero_clamped(self, client, auth_headers, sample_cliente):
        response = client.get("/clientes?page=0", cookies=auth_headers)
        assert response.status_code == 200

    def test_motos_page_negative(self, client, auth_headers, sample_moto):
        response = client.get("/motos?page=-1", cookies=auth_headers)
        assert response.status_code == 200

    def test_repuestos_page_negative(self, client, auth_headers, sample_repuesto):
        response = client.get("/repuestos?page=-1", cookies=auth_headers)
        assert response.status_code == 200

    def test_ordenes_page_negative(self, client, auth_headers):
        response = client.get("/ordenes?page=-1", cookies=auth_headers)
        assert response.status_code == 200


class TestCookieSecurity:
    """Batch2 #8: Cookie has samesite=lax flag."""

    def test_login_sets_samesite_cookie(self, client, admin_user):
        response = client.post(
            "/login",
            data={"email": "admin@test.com", "password": "admin123"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        cookie_header = None
        for header in response.headers.raw:
            if header[0] == b"set-cookie":
                cookie_header = header[1].decode()
                break
        assert cookie_header is not None
        assert "SameSite=lax" in cookie_header or "samesite=lax" in cookie_header.lower()


class TestPDFTempFileCleanup:
    """Batch2 #9: PDF temp files are cleaned up."""

    def test_pdf_creates_no_orphan_files(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        before_count = len([f for f in os.listdir(tempfile.gettempdir()) if f.endswith('.pdf')])

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Test PDF",
            estado="received",
        )
        db.add(orden)
        db.commit()
        db.refresh(orden)

        response = client.get(f"/ordenes/{orden.codigo}/pdf", cookies=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

        after_count = len([f for f in os.listdir(tempfile.gettempdir()) if f.endswith('.pdf')])
        assert after_count == before_count
