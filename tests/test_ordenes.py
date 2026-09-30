import urllib.parse


class TestOrdenes:
    def test_lista_ordenes(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Falla en el motor",
            estado="received",
        )
        db.add(orden)
        db.commit()

        response = client.get("/ordenes", cookies=auth_headers)
        assert response.status_code == 200
        assert "BZ-" in response.text

    def test_detalle_orden(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Frenos desgastados",
            estado="received",
        )
        db.add(orden)
        db.commit()
        db.refresh(orden)

        response = client.get(f"/ordenes/{orden.codigo}", cookies=auth_headers)
        assert response.status_code == 200
        assert "Frenos desgastados" in response.text

    def test_crear_orden(self, client, auth_headers, sample_cliente, sample_moto):
        response = client.post(
            "/ordenes/nueva",
            data={
                "client_id": sample_cliente.id,
                "motorcycle_id": sample_moto.id,
                "falla_reportada": "Cambio de aceite",
                "tecnico_id": "",
                "kilometraje_entrada": "",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_cambiar_estado(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Cambio de aceite",
            estado="received",
        )
        db.add(orden)
        db.commit()
        db.refresh(orden)

        response = client.post(
            f"/ordenes/{orden.codigo}/cambiar-estado",
            data={"nuevo_estado": "diagnosed", "observaciones": "Diagnostico realizado"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_editar_orden(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Cambio de aceite",
            estado="received",
        )
        db.add(orden)
        db.commit()
        db.refresh(orden)

        response = client.post(
            f"/ordenes/{orden.codigo}/editar",
            data={
                "diagnostico": "Aceite muy sucio",
                "presupuesto": "500",
                "precio_final": "450",
                "kilometraje_salida": "15500",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_agregar_repuesto(self, client, auth_headers, sample_cliente, sample_moto, sample_repuesto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Cambio de aceite",
            estado="repairing",
        )
        db.add(orden)
        db.commit()
        db.refresh(orden)

        response = client.post(
            f"/ordenes/{orden.codigo}/agregar-repuesto",
            data={"repuesto_id": sample_repuesto.id, "cantidad": "2"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_eliminar_orden(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Prueba",
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

    def test_flujo_completo(self, client, auth_headers, sample_cliente, sample_moto, sample_repuesto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Reparacion completa",
            estado="received",
        )
        db.add(orden)
        db.commit()
        db.refresh(orden)

        for estado in ["diagnosed", "quote_sent", "quote_approved", "in_progress", "repairing", "ready", "delivered"]:
            response = client.post(
                f"/ordenes/{orden.codigo}/cambiar-estado",
                data={"nuevo_estado": estado, "observaciones": ""},
                follow_redirects=False,
            )
            assert response.status_code == 303

    def test_crear_orden_sin_ids_redirige_con_error(self, client, auth_headers):
        response = client.post(
            "/ordenes/nueva",
            data={"client_id": "", "motorcycle_id": "", "falla_reportada": ""},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"].startswith("/ordenes/nueva?error=")

    def test_crear_orden_ids_inexistentes(self, client, auth_headers):
        response = client.post(
            "/ordenes/nueva",
            data={"client_id": "9999", "motorcycle_id": "9999", "falla_reportada": "Falla"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "no%20existe" in response.headers["location"]

    def test_crear_orden_moto_de_otro_cliente(self, client, auth_headers, sample_cliente, db):
        from app.models.cliente import Cliente
        from app.models.moto import Moto

        otro = Cliente(nombre="Otro Cliente")
        db.add(otro)
        db.commit()
        db.refresh(otro)

        moto_ajena = Moto(client_id=otro.id, marca="Yamaha", modelo="FZ")
        db.add(moto_ajena)
        db.commit()
        db.refresh(moto_ajena)

        response = client.post(
            "/ordenes/nueva",
            data={
                "client_id": sample_cliente.id,
                "motorcycle_id": moto_ajena.id,
                "falla_reportada": "Falla",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "no%20pertenece" in response.headers["location"]

    def test_crear_orden_tecnico_inexistente(self, client, auth_headers, sample_cliente, sample_moto):
        response = client.post(
            "/ordenes/nueva",
            data={
                "client_id": sample_cliente.id,
                "motorcycle_id": sample_moto.id,
                "technician_id": "9999",
                "falla_reportada": "Falla",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "tecnico%20seleccionado%20no%20existe" in response.headers["location"]

    def test_formulario_muestra_error_recibido(self, client, auth_headers):
        response = client.get("/ordenes/nueva?error=Selecciona%20un%20cliente%20y%20una%20moto")
        assert response.status_code == 200
        assert "Selecciona un cliente y una moto" in response.text

    def test_detecta_conflicto_de_codigo_vs_error_de_fk(self):
        from sqlalchemy import exc as sa_exc
        from app.services.orden_service import es_conflicto_codigo

        duplicado = sa_exc.IntegrityError(
            "INSERT",
            {},
            Exception('duplicate key value violates unique constraint "service_orders_codigo_key"'),
        )
        duplicado_sqlite = sa_exc.IntegrityError(
            "INSERT", {}, Exception("UNIQUE constraint failed: service_orders.codigo")
        )
        fk = sa_exc.IntegrityError("INSERT", {}, Exception("FOREIGN KEY constraint failed"))

        assert es_conflicto_codigo(duplicado) is True
        assert es_conflicto_codigo(duplicado_sqlite) is True
        assert es_conflicto_codigo(fk) is False

    def test_error_del_servicio_de_crear_orden_se_muestra(self, client, auth_headers, sample_cliente, sample_moto, monkeypatch):
        from app.services import orden_service

        def _falla(db, data, user_id):
            raise orden_service.OrdenError("No se pudo crear la orden: cliente, moto o tecnico invalidos")

        monkeypatch.setattr(orden_service, "create_orden", _falla)

        response = client.post(
            "/ordenes/nueva",
            data={"client_id": sample_cliente.id, "motorcycle_id": sample_moto.id, "falla_reportada": "x"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "invalidos" in urllib.parse.unquote(response.headers["location"])
