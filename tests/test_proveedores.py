class TestProveedores:
    def test_lista_proveedores(self, client, auth_headers, sample_proveedor):
        response = client.get("/proveedores", cookies=auth_headers)
        assert response.status_code == 200
        assert "Proveedor Test" in response.text

    def test_detalle_proveedor(self, client, auth_headers, sample_proveedor):
        response = client.get(f"/proveedores/{sample_proveedor.id}", cookies=auth_headers)
        assert response.status_code == 200
        assert "Proveedor Test" in response.text
        assert "555-0002" in response.text

    def test_crear_proveedor(self, client, auth_headers):
        response = client.post(
            "/proveedores/nuevo",
            data={
                "nombre": "Nuevo Proveedor",
                "email": "nuevo@proveedor.com",
                "telefono": "555-9999",
                "direccion": "Av. Nueva 123",
                "persona_contacto": "Maria Lopez",
                "notas": "Proveedor de confianza",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_editar_proveedor(self, client, auth_headers, sample_proveedor):
        response = client.post(
            f"/proveedores/{sample_proveedor.id}/editar",
            data={
                "nombre": "Proveedor Actualizado",
                "email": "actualizado@proveedor.com",
                "telefono": "555-8888",
                "direccion": "Av. Actualizada 456",
                "persona_contacto": "Pedro Garcia",
                "notas": "Actualizado",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_eliminar_proveedor(self, client, auth_headers, sample_proveedor):
        response = client.post(
            f"/proveedores/{sample_proveedor.id}/eliminar",
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_buscar_proveedor(self, client, auth_headers, sample_proveedor):
        response = client.get("/proveedores?search=Proveedor", cookies=auth_headers)
        assert response.status_code == 200
        assert "Proveedor Test" in response.text
