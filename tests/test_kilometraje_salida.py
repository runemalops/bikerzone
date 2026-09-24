from app.models.orden_servicio import OrdenServicio
from app.schemas.orden_servicio import OrdenServicioUpdate
from app.services import orden_service, site_service
from tests.conftest import generate_orden_codigo


def _make_orden(db, sample_cliente, sample_moto):
    orden = OrdenServicio(
        codigo=generate_orden_codigo(db),
        client_id=sample_cliente.id,
        motorcycle_id=sample_moto.id,
        falla_reportada="Cambio de aceite",
        estado="ready",
    )
    db.add(orden)
    db.commit()
    db.refresh(orden)
    return orden


class TestSalidaSincronizaMoto:
    def test_actualiza_kilometraje_y_reprograma(self, db, sample_cliente, sample_moto):
        orden = _make_orden(db, sample_cliente, sample_moto)
        sample_moto.kilometraje = 15000
        sample_moto.proximo_service_km = 14000  # vencido
        db.commit()

        orden_service.update_orden(
            db, orden.id, OrdenServicioUpdate(kilometraje_salida=15500)
        )
        db.refresh(sample_moto)

        assert sample_moto.kilometraje == 15500
        # vencido -> reprograma a salida + 5000 (default)
        assert sample_moto.proximo_service_km == 20500

    def test_no_baja_kilometraje_si_salida_menor(self, db, sample_cliente, sample_moto):
        orden = _make_orden(db, sample_cliente, sample_moto)
        sample_moto.kilometraje = 20000
        db.commit()

        orden_service.update_orden(
            db, orden.id, OrdenServicioUpdate(kilometraje_salida=18000)
        )
        db.refresh(sample_moto)

        assert sample_moto.kilometraje == 20000

    def test_no_reprograma_si_proximo_aun_lejos(self, db, sample_cliente, sample_moto):
        orden = _make_orden(db, sample_cliente, sample_moto)
        sample_moto.kilometraje = 15000
        sample_moto.proximo_service_km = 30000
        db.commit()

        orden_service.update_orden(
            db, orden.id, OrdenServicioUpdate(kilometraje_salida=15500)
        )
        db.refresh(sample_moto)

        assert sample_moto.kilometraje == 15500
        assert sample_moto.proximo_service_km == 30000  # no se toca

    def test_programa_si_estaba_sin_proximo(self, db, sample_cliente, sample_moto):
        orden = _make_orden(db, sample_cliente, sample_moto)
        sample_moto.kilometraje = 1000
        sample_moto.proximo_service_km = None
        db.commit()

        orden_service.update_orden(
            db, orden.id, OrdenServicioUpdate(kilometraje_salida=1200)
        )
        db.refresh(sample_moto)

        assert sample_moto.proximo_service_km == 6200  # 1200 + 5000

    def test_intervalo_cero_no_reprograma(self, db, sample_cliente, sample_moto):
        config = site_service.get_site_config(db)
        config.preventivo_km_intervalo = 0
        db.commit()

        orden = _make_orden(db, sample_cliente, sample_moto)
        sample_moto.kilometraje = 15000
        sample_moto.proximo_service_km = 14000
        db.commit()

        orden_service.update_orden(
            db, orden.id, OrdenServicioUpdate(kilometraje_salida=15500)
        )
        db.refresh(sample_moto)

        assert sample_moto.kilometraje == 15500
        assert sample_moto.proximo_service_km == 14000  # sin reprogramar

    def test_intervalo_personalizado(self, db, sample_cliente, sample_moto):
        config = site_service.get_site_config(db)
        config.preventivo_km_intervalo = 3000
        db.commit()

        orden = _make_orden(db, sample_cliente, sample_moto)
        sample_moto.kilometraje = 15000
        sample_moto.proximo_service_km = 14000
        db.commit()

        orden_service.update_orden(
            db, orden.id, OrdenServicioUpdate(kilometraje_salida=15500)
        )
        db.refresh(sample_moto)

        assert sample_moto.proximo_service_km == 18500  # 15500 + 3000

    def test_sin_salida_no_toca_moto(self, db, sample_cliente, sample_moto):
        orden = _make_orden(db, sample_cliente, sample_moto)
        sample_moto.kilometraje = 15000
        sample_moto.proximo_service_km = 14000
        db.commit()

        orden_service.update_orden(
            db, orden.id, OrdenServicioUpdate(diagnostico="ok")
        )
        db.refresh(sample_moto)

        assert sample_moto.kilometraje == 15000
        assert sample_moto.proximo_service_km == 14000

    def test_endpoint_editar_ordena_sincroniza(self, client, auth_headers, db,
                                               sample_cliente, sample_moto):
        orden = _make_orden(db, sample_cliente, sample_moto)
        sample_moto.kilometraje = 15000
        sample_moto.proximo_service_km = None
        db.commit()

        r = client.post(
            f"/ordenes/{orden.codigo}/editar",
            data={"kilometraje_salida": "15800", "diagnostico": "", "presupuesto": ""},
            cookies=auth_headers, follow_redirects=False,
        )
        assert r.status_code == 303
        db.refresh(sample_moto)
        assert sample_moto.kilometraje == 15800
        assert sample_moto.proximo_service_km == 20800

    def test_evaluar_preventivo_usa_kilometraje_actualizado(self, db, sample_cliente,
                                                            sample_moto):
        from datetime import date
        from app.services import preventivo_service

        orden = _make_orden(db, sample_cliente, sample_moto)
        sample_moto.kilometraje = 15000
        sample_moto.proximo_service_km = 14000
        db.commit()

        config = site_service.get_site_config(db)
        # antes: vencido
        estado = preventivo_service.evaluar_moto(sample_moto, config, date.today())
        assert estado["nivel"] == "vencido"

        orden_service.update_orden(
            db, orden.id, OrdenServicioUpdate(kilometraje_salida=15500)
        )
        db.refresh(sample_moto)
        # despues de cerrar: reprogramado 20500 -> ok
        estado = preventivo_service.evaluar_moto(sample_moto, config, date.today())
        assert estado["nivel"] == "ok"
