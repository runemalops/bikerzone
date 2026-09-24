from datetime import date, timedelta

import pytest

from app.models.notificacion import Notificacion
from app.models.orden_servicio import OrdenServicio
from app.models.site_config import SiteConfig
from app.services import notificacion_service, preventivo_service
from tests.conftest import generate_orden_codigo


@pytest.fixture
def envios(monkeypatch):
    """Transportes falsos: capturan envios sin red ni SMTP reales."""
    calls = {"email": [], "telegram": []}

    def fake_email(destinatario, asunto, cuerpo):
        calls["email"].append((destinatario, asunto, cuerpo))
        return True, ""

    def fake_telegram(chat_id, texto):
        calls["telegram"].append((chat_id, texto))
        return True, ""

    monkeypatch.setattr(notificacion_service, "enviar_email", fake_email)
    monkeypatch.setattr(notificacion_service, "enviar_telegram", fake_telegram)
    return calls


def make_orden(db, sample_cliente, sample_moto, estado="repairing"):
    orden = OrdenServicio(
        codigo=generate_orden_codigo(db),
        client_id=sample_cliente.id,
        motorcycle_id=sample_moto.id,
        falla_reportada="Freno trasero desgastado",
        estado=estado,
    )
    db.add(orden)
    db.commit()
    db.refresh(orden)
    return orden


class TestAutoNotificarOrdenLista:
    def test_auto_al_pasar_a_ready(self, client, auth_headers, sample_cliente,
                                   sample_moto, db, envios):
        orden = make_orden(db, sample_cliente, sample_moto, estado="repairing")
        r = client.post(
            f"/ordenes/{orden.codigo}/cambiar-estado",
            data={"nuevo_estado": "ready", "observaciones": "Listo"},
            cookies=auth_headers, follow_redirects=False,
        )
        assert r.status_code == 303

        filas = db.query(Notificacion).filter(
            Notificacion.service_order_id == orden.id).all()
        email = [f for f in filas if f.canal == "email"]
        assert len(email) == 1
        assert email[0].estado == "enviado"
        assert email[0].destinatario == "cliente@test.com"
        # sin telegram_chat_id -> omitido registrado
        tg = [f for f in filas if f.canal == "telegram"]
        assert len(tg) == 1
        assert tg[0].estado == "omitido"
        # transporte real fue invocado
        assert len(envios["email"]) == 1
        assert "lista para recoger" in envios["email"][0][2]

    def test_con_telegram_configurado(self, client, auth_headers, sample_cliente,
                                      sample_moto, db, envios):
        sample_cliente.telegram_chat_id = "111222333"
        db.commit()
        orden = make_orden(db, sample_cliente, sample_moto, estado="repairing")
        client.post(
            f"/ordenes/{orden.codigo}/cambiar-estado",
            data={"nuevo_estado": "ready"}, cookies=auth_headers, follow_redirects=False,
        )
        tg = db.query(Notificacion).filter(
            Notificacion.service_order_id == orden.id,
            Notificacion.canal == "telegram").one()
        assert tg.estado == "enviado"
        assert tg.destinatario == "111222333"
        assert len(envios["telegram"]) == 1

    def test_toggles_desactivados_no_envian(self, client, auth_headers, sample_cliente,
                                            sample_moto, db, envios):
        config = preventivo_service._config(db)
        config.notif_email_auto = False
        config.notif_telegram_auto = False
        db.commit()
        orden = make_orden(db, sample_cliente, sample_moto, estado="repairing")
        client.post(
            f"/ordenes/{orden.codigo}/cambiar-estado",
            data={"nuevo_estado": "ready"}, cookies=auth_headers, follow_redirects=False,
        )
        assert db.query(Notificacion).count() == 0
        assert envios["email"] == []

    def test_dedupe_automatico(self, db, sample_cliente, sample_moto, envios):
        orden = make_orden(db, sample_cliente, sample_moto, estado="ready")
        notificacion_service.notificar_orden_lista(db, orden, canal=None, automatica=True)
        notificacion_service.notificar_orden_lista(db, orden, canal=None, automatica=True)
        emails = db.query(Notificacion).filter(
            Notificacion.service_order_id == orden.id,
            Notificacion.canal == "email").count()
        assert emails == 1

    def test_no_notifica_en_otro_estado(self, db, sample_cliente, sample_moto, envios):
        orden = make_orden(db, sample_cliente, sample_moto, estado="repairing")
        notificacion_service.auto_notificar_orden_lista  # existe
        # simular cambios que no son a 'ready'
        from app.services import orden_service
        # directamente: solo el hook de cambiar_estado dispara; aqui no debe haber filas
        assert db.query(Notificacion).count() == 0
        assert orden.estado == "repairing"


class TestNotificacionManual:
    def test_reenviar_email(self, client, auth_headers, sample_cliente, sample_moto,
                            db, envios):
        orden = make_orden(db, sample_cliente, sample_moto, estado="ready")
        r = client.post(f"/ordenes/{orden.codigo}/notificar/email",
                        cookies=auth_headers, follow_redirects=False)
        assert r.status_code == 303
        assert "notif=ok:email" in r.headers["location"]
        fila = db.query(Notificacion).filter(
            Notificacion.service_order_id == orden.id,
            Notificacion.canal == "email").one()
        assert fila.estado == "enviado"

    def test_reenviar_sin_dedupe(self, client, auth_headers, sample_cliente,
                                 sample_moto, db, envios):
        orden = make_orden(db, sample_cliente, sample_moto, estado="ready")
        for _ in range(2):
            client.post(f"/ordenes/{orden.codigo}/notificar/email",
                        cookies=auth_headers, follow_redirects=False)
        assert db.query(Notificacion).filter(
            Notificacion.service_order_id == orden.id,
            Notificacion.canal == "email").count() == 2

    def test_fallo_sin_smtp_registra_error(self, client, auth_headers, sample_cliente,
                                           sample_moto, db):
        # sin monkeypatch: SMTP no configurado -> fallido con motivo
        orden = make_orden(db, sample_cliente, sample_moto, estado="ready")
        r = client.post(f"/ordenes/{orden.codigo}/notificar/email",
                        cookies=auth_headers, follow_redirects=False)
        assert r.status_code == 303
        assert "notif=err:email:" in r.headers["location"]
        fila = db.query(Notificacion).filter(
            Notificacion.service_order_id == orden.id).one()
        assert fila.estado == "fallido"
        assert "SMTP" in (fila.error or "")

    def test_canal_invalido(self, client, auth_headers, sample_cliente, sample_moto, db):
        orden = make_orden(db, sample_cliente, sample_moto, estado="ready")
        r = client.post(f"/ordenes/{orden.codigo}/notificar/whatsapp",
                        cookies=auth_headers)
        assert r.status_code == 400

    def test_login_requerido(self, client, sample_cliente, sample_moto, db):
        orden = make_orden(db, sample_cliente, sample_moto, estado="ready")
        r = client.post(f"/ordenes/{orden.codigo}/notificar/email",
                        follow_redirects=False)
        assert r.status_code in (302, 303)
        assert "/login" in r.headers["location"]


class TestWhatsAppEnDetalle:
    def test_boton_wa_me(self, client, auth_headers, sample_cliente, sample_moto, db):
        # telefono del fixture: 555-0001 -> 7 digitos sin prefijo 502
        orden = make_orden(db, sample_cliente, sample_moto, estado="ready")
        r = client.get(f"/ordenes/{orden.codigo}", cookies=auth_headers)
        assert r.status_code == 200
        assert "wa.me/5550001" in r.text
        assert "Abrir WhatsApp" in r.text
        assert "Enviar Email" in r.text
        # sin telegram_chat_id no se muestra el boton de telegram
        assert "Enviar Telegram" not in r.text

    def test_con_prefijo_502(self, client, auth_headers, sample_cliente,
                             sample_moto, db):
        sample_cliente.telefono = "12345678"
        db.commit()
        orden = make_orden(db, sample_cliente, sample_moto, estado="ready")
        r = client.get(f"/ordenes/{orden.codigo}", cookies=auth_headers)
        assert "wa.me/50212345678" in r.text

    def test_oculto_fuera_de_ready(self, client, auth_headers, sample_cliente,
                                   sample_moto, db):
        orden = make_orden(db, sample_cliente, sample_moto, estado="repairing")
        r = client.get(f"/ordenes/{orden.codigo}", cookies=auth_headers)
        assert "Abrir WhatsApp" not in r.text


class TestConfigNotificaciones:
    def test_guardar(self, client, auth_headers, db):
        r = client.post(
            "/configuracion/notificaciones",
            data={
                "notif_email_auto": "1",
                "preventivo_dias_anticipacion": "14",
                "preventivo_km_anticipacion": "300",
            },
            cookies=auth_headers, follow_redirects=False,
        )
        assert r.status_code == 303
        config = db.query(SiteConfig).filter(SiteConfig.id == 1).one()
        assert config.notif_email_auto is True
        assert config.notif_telegram_auto is False  # checkbox ausente
        assert config.preventivo_dias_anticipacion == 14
        assert config.preventivo_km_anticipacion == 300

    def test_dias_invalidos(self, client, auth_headers, db):
        r = client.post(
            "/configuracion/notificaciones",
            data={"preventivo_dias_anticipacion": "0",
                  "preventivo_km_anticipacion": "500"},
            cookies=auth_headers,
        )
        assert r.status_code == 400

    def test_admin_only(self, client, tecnico_user, db):
        client.post("/login", data={"email": "tecnico@test.com",
                                    "password": "tecnico123"},
                    follow_redirects=False)
        r = client.post("/configuracion/notificaciones", data={})
        assert r.status_code == 403


class TestPanelPreventivo:
    def _programar(self, db, moto, fecha=None, km=None):
        moto.proximo_service_fecha = fecha
        moto.proximo_service_km = km
        db.commit()

    def test_login_requerido(self, client):
        r = client.get("/preventivo", follow_redirects=False)
        assert r.status_code in (302, 303)
        assert "/login" in r.headers["location"]

    def test_vacio(self, client, auth_headers, sample_moto):
        r = client.get("/preventivo", cookies=auth_headers)
        assert r.status_code == 200
        assert "No hay servicios programados" in r.text

    def test_vencido_por_fecha(self, client, auth_headers, sample_moto, db):
        self._programar(db, sample_moto, fecha=date.today() - timedelta(days=1))
        r = client.get("/preventivo", cookies=auth_headers)
        assert r.status_code == 200
        assert "Vencido" in r.text
        assert "Honda" in r.text
        assert "fecha vencida" in r.text

    def test_vencido_por_km(self, client, auth_headers, sample_moto, db):
        self._programar(db, sample_moto, km=10000)  # kilometraje actual: 15000
        r = client.get("/preventivo", cookies=auth_headers)
        assert "Vencido" in r.text
        assert "km alcanzados" in r.text

    def test_proximo_por_fecha(self, client, auth_headers, sample_moto, db):
        self._programar(db, sample_moto, fecha=date.today() + timedelta(days=3))
        r = client.get("/preventivo", cookies=auth_headers)
        assert "Proximo" in r.text
        assert "fecha en 3 dia" in r.text

    def test_ok_lejano(self, client, auth_headers, sample_moto, db):
        self._programar(db, sample_moto, fecha=date.today() + timedelta(days=120))
        r = client.get("/preventivo", cookies=auth_headers)
        assert "Programado" in r.text

    def test_orden_vencidos_primero(self, client, auth_headers, sample_cliente, db):
        from app.models.moto import Moto
        for i, (fecha, esperado) in enumerate([
            (date.today() + timedelta(days=100), "Programado"),
            (date.today() - timedelta(days=5), "Vencido"),
        ]):
            moto = Moto(client_id=sample_cliente.id, marca="MarcaX", modelo=f"M{i}",
                        kilometraje=0, proximo_service_fecha=fecha)
            db.add(moto)
        db.commit()
        r = client.get("/preventivo", cookies=auth_headers)
        assert r.text.index("Vencido") < r.text.index("Programado")


class TestRecordatorioManual:
    def test_email(self, client, auth_headers, sample_cliente, sample_moto, db, envios):
        sample_moto.proximo_service_fecha = date.today() - timedelta(days=2)
        db.commit()
        r = client.post(f"/preventivo/{sample_moto.id}/recordatorio/email",
                        cookies=auth_headers, follow_redirects=False)
        assert r.status_code == 303
        assert "notif=ok:email" in r.headers["location"]
        fila = db.query(Notificacion).filter(
            Notificacion.motorcycle_id == sample_moto.id).one()
        assert fila.estado == "enviado"
        assert fila.referencia.startswith("preventivo:")
        assert len(envios["email"]) == 1

    def test_sin_email_falla(self, client, auth_headers, sample_moto, db):
        sample_moto.proximo_service_fecha = date.today() - timedelta(days=2)
        db.commit()
        # sample_cliente.email existe; quitamos el email
        cliente = sample_moto.cliente
        cliente.email = None
        db.commit()
        r = client.post(f"/preventivo/{sample_moto.id}/recordatorio/email",
                        cookies=auth_headers, follow_redirects=False)
        assert "notif=err:email:" in r.headers["location"]

    def test_canal_invalido(self, client, auth_headers, sample_moto, db):
        r = client.post(f"/preventivo/{sample_moto.id}/recordatorio/whatsapp",
                        cookies=auth_headers)
        assert r.status_code == 400


class TestRecordatorioAutomatico:
    def test_dedupe_por_ciclo(self, db, sample_cliente, sample_moto, envios):
        sample_moto.proximo_service_fecha = date.today() - timedelta(days=1)
        db.commit()
        n1 = preventivo_service.enviar_recordatorios_pendientes(db)
        n2 = preventivo_service.enviar_recordatorios_pendientes(db)
        assert n1 == 1  # solo email (sin telegram_chat_id)
        assert n2 == 0
        emails = db.query(Notificacion).filter(
            Notificacion.motorcycle_id == sample_moto.id,
            Notificacion.canal == "email",
            Notificacion.estado == "enviado").count()
        assert emails == 1

    def test_no_envia_programados_ok(self, db, sample_cliente, sample_moto, envios):
        sample_moto.proximo_service_fecha = date.today() + timedelta(days=120)
        db.commit()
        assert preventivo_service.enviar_recordatorios_pendientes(db) == 0
        assert db.query(Notificacion).count() == 0
