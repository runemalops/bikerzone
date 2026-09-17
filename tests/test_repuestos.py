class TestRepuestos:
    def test_lista_repuestos(self, client, auth_headers, sample_repuesto):
        response = client.get("/repuestos", cookies=auth_headers)
        assert response.status_code == 200
        assert "Filtro de Aceite" in response.text
        assert "FILT-001" in response.text

    def test_detalle_repuesto(self, client, auth_headers, sample_repuesto):
        response = client.get(f"/repuestos/{sample_repuesto.id}", cookies=auth_headers)
        assert response.status_code == 200
        assert "Filtro de Aceite" in response.text
        assert "$150.00" in response.text

    def test_crear_repuesto(self, client, auth_headers):
        response = client.post(
            "/repuestos/nuevo",
            data={
                "codigo": "CAD-001",
                "nombre": "Cadena 520",
                "categoria": "Transmision",
                "marca": "RK",
                "descripcion": "Cadena reforzada",
                "precio_compra": "800",
                "precio_venta": "1200",
                "stock_actual": "10",
                "stock_minimo": "3",
                "ubicacion": "Estante B2",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_editar_repuesto(self, client, auth_headers, sample_repuesto):
        response = client.post(
            f"/repuestos/{sample_repuesto.id}/editar",
            data={
                "codigo": "FILT-001",
                "nombre": "Filtro de Aceite Premium",
                "categoria": "Filtros",
                "marca": "Honda",
                "descripcion": "Filtro premium",
                "precio_compra": "180",
                "precio_venta": "280",
                "stock_actual": "25",
                "stock_minimo": "5",
                "ubicacion": "Estante A1",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_actualizar_stock(self, client, auth_headers, sample_repuesto):
        response = client.post(
            f"/repuestos/{sample_repuesto.id}/actualizar-stock",
            data={"nuevo_stock": "30"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_eliminar_repuesto(self, client, auth_headers, sample_repuesto):
        response = client.post(
            f"/repuestos/{sample_repuesto.id}/eliminar",
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_buscar_repuesto(self, client, auth_headers, sample_repuesto):
        response = client.get("/repuestos?search=Filtro", cookies=auth_headers)
        assert response.status_code == 200
        assert "Filtro de Aceite" in response.text

    def test_stock_bajo(self, client, auth_headers, sample_repuesto, db):
        from app.models.repuesto import Repuesto

        repuesto = db.query(Repuesto).filter(Repuesto.id == sample_repuesto.id).first()
        repuesto.stock_actual = 2
        db.commit()

        response = client.get("/repuestos?search=FILT-001", cookies=auth_headers)
        assert response.status_code == 200
