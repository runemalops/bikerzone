class TestMotos:
    def test_lista_motos(self, client, auth_headers, sample_moto):
        response = client.get("/motos", cookies=auth_headers)
        assert response.status_code == 200
        assert "Honda" in response.text
        assert "CBR600" in response.text

    def test_detalle_moto(self, client, auth_headers, sample_moto):
        response = client.get(f"/motos/{sample_moto.id}", cookies=auth_headers)
        assert response.status_code == 200
        assert "Honda" in response.text
        assert "ABC-123" in response.text

    def test_crear_moto(self, client, auth_headers, sample_cliente):
        response = client.post(
            "/motos/nueva",
            data={
                "client_id": sample_cliente.id,
                "marca": "Yamaha",
                "modelo": "MT-07",
                "placa": "XYZ-789",
                "anio": "2021",
                "kilometraje": "5000",
                "color": "Azul",
                "numero_serie": "SN98765",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_editar_moto(self, client, auth_headers, sample_moto):
        response = client.post(
            f"/motos/{sample_moto.id}/editar",
            data={
                "client_id": sample_moto.client_id,
                "marca": "Honda",
                "modelo": "CBR650",
                "placa": "ABC-123",
                "anio": "2021",
                "kilometraje": "18000",
                "color": "Rojo",
                "numero_serie": "SN12345",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_eliminar_moto(self, client, auth_headers, sample_moto):
        response = client.post(
            f"/motos/{sample_moto.id}/eliminar",
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_buscar_moto(self, client, auth_headers, sample_moto):
        response = client.get("/motos?search=CBR", cookies=auth_headers)
        assert response.status_code == 200
        assert "Honda" in response.text
