class TestExport:
    def test_export_ordenes_csv(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Prueba de export",
            estado="received",
        )
        db.add(orden)
        db.commit()

        response = client.get("/ordenes/export/csv", cookies=auth_headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_inventario_csv(self, client, auth_headers, sample_repuesto):
        response = client.get("/reportes/export/inventario/csv", cookies=auth_headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_clientes_csv(self, client, auth_headers, sample_cliente):
        response = client.get("/reportes/export/clientes/csv", cookies=auth_headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_orden_pdf(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Prueba de PDF",
            estado="received",
        )
        db.add(orden)
        db.commit()
        db.refresh(orden)

        response = client.get(f"/ordenes/{orden.codigo}/pdf", cookies=auth_headers)
        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]
