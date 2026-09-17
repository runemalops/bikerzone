class TestOrdenes:
    def test_lista_ordenes(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio

        orden = OrdenServicio(
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

        orden = OrdenServicio(
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

        orden = OrdenServicio(
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

        orden = OrdenServicio(
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

        orden = OrdenServicio(
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

        orden = OrdenServicio(
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

        orden = OrdenServicio(
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
