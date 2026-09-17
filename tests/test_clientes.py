class TestClientes:
    def test_lista_clientes(self, client, auth_headers, sample_cliente):
        response = client.get("/clientes", cookies=auth_headers)
        assert response.status_code == 200
        assert "Cliente Prueba" in response.text

    def test_detalle_cliente(self, client, auth_headers, sample_cliente):
        response = client.get(f"/clientes/{sample_cliente.id}", cookies=auth_headers)
        assert response.status_code == 200
        assert "Cliente Prueba" in response.text
        assert "555-0001" in response.text

    def test_crear_cliente(self, client, auth_headers):
        response = client.post(
            "/clientes/nuevo",
            data={
                "nombre": "Cliente Nuevo",
                "telefono": "555-9999",
                "email": "nuevo@test.com",
                "direccion": "Nueva Direccion 789",
                "rfc": "TEST12345678",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_editar_cliente(self, client, auth_headers, sample_cliente):
        response = client.post(
            f"/clientes/{sample_cliente.id}/editar",
            data={
                "nombre": "Cliente Actualizado",
                "telefono": "555-0002",
                "email": "actualizado@test.com",
                "direccion": "Direccion Actualizada",
                "rfc": "ACT12345678",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_eliminar_cliente(self, client, auth_headers, sample_cliente):
        response = client.post(
            f"/clientes/{sample_cliente.id}/eliminar",
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_buscar_cliente(self, client, auth_headers, sample_cliente):
        response = client.get("/clientes?search=Prueba", cookies=auth_headers)
        assert response.status_code == 200
        assert "Cliente Prueba" in response.text
