class TestDashboard:
    def test_dashboard_page(self, client, auth_headers):
        response = client.get("/dashboard", cookies=auth_headers)
        assert response.status_code == 200
        assert "Dashboard" in response.text

    def test_reportes_index(self, client, auth_headers):
        response = client.get("/reportes", cookies=auth_headers)
        assert response.status_code == 200
        assert "Reportes" in response.text

    def test_reporte_ventas(self, client, auth_headers):
        response = client.get("/reportes/ventas", cookies=auth_headers)
        assert response.status_code == 200
        assert "Ventas" in response.text

    def test_reporte_inventario(self, client, auth_headers):
        response = client.get("/reportes/inventario", cookies=auth_headers)
        assert response.status_code == 200
        assert "Inventario" in response.text

    def test_reporte_compras(self, client, auth_headers):
        response = client.get("/reportes/compras", cookies=auth_headers)
        assert response.status_code == 200
        assert "Compras" in response.text

    def test_reporte_productividad(self, client, auth_headers):
        response = client.get("/reportes/productividad", cookies=auth_headers)
        assert response.status_code == 200
        assert "Productividad" in response.text
