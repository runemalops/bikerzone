import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import func

from app.main import app
from app.models.orden_servicio import OrdenServicio
from app.models.orden_repuesto import OrdenRepuesto
from app.models.repuesto import Repuesto
from app.models.cliente import Cliente
from app.models.moto import Moto
from app.models.usuario import Usuario
from app.models.historial_estado import HistorialEstado
from app.services.cliente_service import delete_cliente
from app.services.moto_service import delete_moto
from app.services.repuesto_service import update_stock
from app.services.orden_service import (
    create_orden,
    add_repuesto_orden,
    cambiar_estado,
    confirmar_orden,
)
from app.services.usuario_service import delete_usuario
from app.services.export_service import export_ordenes_csv
from app.schemas.orden_servicio import OrdenServicioCreate
from tests.conftest import generate_orden_codigo


def _make_orden(db, cliente, moto, tecnico, estado="received", codigo=None):
    os = OrdenServicio(
        codigo=codigo or generate_orden_codigo(db),
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
# #18: FK violation on client delete with delivered orders
# ==========================================
class TestDeleteClientWithDeliveredOrders:
    def test_cannot_delete_client_with_delivered_orders(
        self, db, sample_cliente, sample_moto, admin_user, tecnico_user
    ):
        _make_orden(db, sample_cliente, sample_moto, tecnico_user, estado="delivered")
        result = delete_cliente(db, sample_cliente.id)
        assert result is False
        assert db.query(Cliente).filter(Cliente.id == sample_cliente.id).first() is not None

    def test_cannot_delete_client_with_cancelled_orders(
        self, db, sample_cliente, sample_moto, admin_user, tecnico_user
    ):
        _make_orden(db, sample_cliente, sample_moto, tecnico_user, estado="cancelled")
        result = delete_cliente(db, sample_cliente.id)
        assert result is False

    def test_can_delete_client_with_no_orders(self, db, sample_cliente):
        result = delete_cliente(db, sample_cliente.id)
        assert result is True


# ==========================================
# #19: FK violation on moto delete with delivered orders
# ==========================================
class TestDeleteMotoWithDeliveredOrders:
    def test_cannot_delete_moto_with_delivered_orders(
        self, db, sample_cliente, sample_moto, admin_user, tecnico_user
    ):
        _make_orden(db, sample_cliente, sample_moto, tecnico_user, estado="delivered")
        result = delete_moto(db, sample_moto.id)
        assert result is False
        assert db.query(Moto).filter(Moto.id == sample_moto.id).first() is not None

    def test_can_delete_moto_with_no_orders(self, db, sample_moto):
        result = delete_moto(db, sample_moto.id)
        assert result is True


# ==========================================
# #20: Manual stock exit ignores reservations
# ==========================================
class TestStockExitRespectsReservations:
    def test_stock_exit_blocked_by_reservations(self, db, sample_repuesto):
        sample_repuesto.stock_actual = 10
        sample_repuesto.stock_reservado = 8
        db.commit()

        ok, msg = update_stock(db, sample_repuesto.id, 5, "salida")
        assert ok is False
        assert "Disponible: 2" in msg
        assert "reservado: 8" in msg

    def test_stock_exit_within_available(self, db, sample_repuesto):
        sample_repuesto.stock_actual = 10
        sample_repuesto.stock_reservado = 8
        db.commit()

        ok, msg = update_stock(db, sample_repuesto.id, 2, "salida")
        assert ok is True

        db.refresh(sample_repuesto)
        assert sample_repuesto.stock_actual == 8


# ==========================================
# #22: Cancelling order orphans stock reservations
# ==========================================
class TestCancelOrderReleasesReservations:
    def test_cancelling_order_releases_reservations(
        self, db, sample_cliente, sample_moto, sample_repuesto, admin_user, tecnico_user
    ):
        orden_data = OrdenServicioCreate(
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            technician_id=tecnico_user.id,
            falla_reportada="Falla de prueba",
            notas="Test",
        )
        orden = create_orden(db, orden_data, admin_user.id)

        add_repuesto_orden(db, orden.id, sample_repuesto.id, 3)

        db.refresh(sample_repuesto)
        assert sample_repuesto.stock_reservado == 3

        cambiar_estado(db, orden.id, "diagnosed", tecnico_user.id)
        cambiar_estado(db, orden.id, "quote_sent", tecnico_user.id)
        cambiar_estado(db, orden.id, "quote_rejected", tecnico_user.id)
        cambiar_estado(db, orden.id, "cancelled", tecnico_user.id)

        db.refresh(sample_repuesto)
        assert sample_repuesto.stock_reservado == 0


# ==========================================
# #23: fecha_hasta drops last-minute-of-day orders
# ==========================================
class TestExportFechaHastaInclusive:
    def test_export_includes_end_of_day_orders(self, db, sample_cliente, sample_moto, admin_user, tecnico_user):
        orden = _make_orden(db, sample_cliente, sample_moto, tecnico_user, estado="received")
        orden.created_at = datetime(2025, 6, 15, 23, 59, 30)
        db.commit()

        result = export_ordenes_csv(db, fecha_desde="2025-06-15", fecha_hasta="2025-06-15")
        assert "BZ-" in result


# ==========================================
# #24: Wrong state check (completed vs delivered)
# ==========================================
class TestClientDetailBadgeState:
    def test_delivered_order_shows_correct_badge(self, client, auth_headers, sample_cliente, sample_moto, tecnico_user):
        from tests.conftest import TestingSessionLocal
        db = TestingSessionLocal()
        try:
            _make_orden(db, sample_cliente, sample_moto, tecnico_user, estado="delivered")
        finally:
            db.close()

        response = client.get(
            f"/clientes/{sample_cliente.id}",
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "Completada" in response.text

    def test_cancelled_order_shows_cancelled_badge(self, client, auth_headers, sample_cliente, sample_moto, tecnico_user):
        from tests.conftest import TestingSessionLocal
        db = TestingSessionLocal()
        try:
            _make_orden(db, sample_cliente, sample_moto, tecnico_user, estado="cancelled")
        finally:
            db.close()

        response = client.get(
            f"/clientes/{sample_cliente.id}",
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "Cancelada" in response.text


# ==========================================
# #28: FK violation on user delete with referenced orders
# ==========================================
class TestDeleteUserWithReferencedOrders:
    def test_cannot_delete_technician_with_orders(
        self, db, sample_cliente, sample_moto, admin_user, tecnico_user
    ):
        _make_orden(db, sample_cliente, sample_moto, tecnico_user)
        result = delete_usuario(db, tecnico_user.id)
        assert result is False
        assert db.query(Usuario).filter(Usuario.id == tecnico_user.id).first() is not None

    def test_can_delete_technician_with_no_orders(self, db, tecnico_user):
        result = delete_usuario(db, tecnico_user.id)
        assert result is True

    def test_api_delete_technician_with_orders_returns_400(
        self, client, auth_headers, sample_cliente, sample_moto, admin_user, tecnico_user
    ):
        from tests.conftest import TestingSessionLocal
        db = TestingSessionLocal()
        try:
            _make_orden(db, sample_cliente, sample_moto, tecnico_user)
        finally:
            db.close()

        response = client.post(
            f"/usuarios/{tecnico_user.id}/eliminar",
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert response.status_code == 400
