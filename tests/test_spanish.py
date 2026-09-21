class TestSpanishSupport:
    def test_clientes_with_spanish_chars(self, client, auth_headers):
        response = client.post(
            "/clientes/nueva",
            data={
                "nombre": "Juan García López",
                "telefono": "555-0001",
                "email": "garcia@test.com",
                "direccion": "Calle Niño Jesus 123",
                "nit": "GARCL800101ABC",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_repuestos_with_spanish_chars(self, client, auth_headers):
        response = client.post(
            "/repuestos/nuevo",
            data={
                "codigo": "REP-001",
                "nombre": "Repuesto ñandú",
                "categoria": "Filtros",
                "marca": "Marca Ñ",
                "descripcion": "Filtro para Niños",
                "precio_compra": "100",
                "precio_venta": "150",
                "stock_actual": "10",
                "stock_minimo": "3",
                "ubicacion": "Estante Ñ",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_ordenes_with_spanish_chars(self, client, auth_headers, sample_cliente, sample_moto):
        response = client.post(
            "/ordenes/nueva",
            data={
                "client_id": sample_cliente.id,
                "motorcycle_id": sample_moto.id,
                "falla_reportada": "Falla en el Niño de la moto",
                "tecnico_id": "",
                "kilometraje_entrada": "",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_clientes_csv_encoding(self, client, auth_headers, sample_cliente, db):
        from app.models.cliente import Cliente

        cliente = db.query(Cliente).filter(Cliente.id == sample_cliente.id).first()
        cliente.nombre = "María José"
        db.commit()

        response = client.get("/reportes/export/clientes/csv", cookies=auth_headers)
        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "María José" in content

    def test_ordenes_csv_encoding(self, client, auth_headers, sample_cliente, sample_moto, db):
        from app.models.orden_servicio import OrdenServicio
        from tests.conftest import generate_orden_codigo

        orden = OrdenServicio(
            codigo=generate_orden_codigo(db),
            client_id=sample_cliente.id,
            motorcycle_id=sample_moto.id,
            falla_reportada="Falla en el Niño",
            estado="received",
        )
        db.add(orden)
        db.commit()

        response = client.get("/ordenes/export/csv", cookies=auth_headers)
        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Falla en el Niño" in content
