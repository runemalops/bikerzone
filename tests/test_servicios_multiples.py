from app.schemas.orden_servicio import (
    codificar_falla_reportada,
    decodificar_falla_reportada,
    normalizar_tipos_servicio,
)


class TestNormalizarTiposServicio:
    def test_acepta_string_separado_por_comas(self):
        assert normalizar_tipos_servicio("frenos,motor") == ["frenos", "motor"]

    def test_acepta_lista_sin_duplicados(self):
        assert normalizar_tipos_servicio(["motor", "frenos", "motor"]) == ["motor", "frenos"]

    def test_descarta_claves_fuera_del_catalogo(self):
        assert normalizar_tipos_servicio("frenos, inventado, motor") == ["frenos", "motor"]

    def test_vacios(self):
        assert normalizar_tipos_servicio("") == []
        assert normalizar_tipos_servicio(None) == []
        assert normalizar_tipos_servicio(" , ") == []


class TestCodificarDecodificarMultiplesTipos:
    def test_codifica_varios_tipos(self):
        texto = codificar_falla_reportada(
            "frenos,motor",
            ["Pastillas desgastadas", "No enciende"],
            "Chasquido al frenar & al arrancar",
        )
        assert texto.startswith("[Frenos + Motor: ")
        assert "Pastillas desgastadas, No enciende" in texto
        assert texto.endswith("Chasquido al frenar & al arrancar")

    def test_codifica_tipo_unico_igual_que_antes(self):
        assert codificar_falla_reportada("frenos", [], "") == "[Frenos]"
        assert (
            codificar_falla_reportada("frenos", ["Freno bloqueado"], "se traba")
            == "[Frenos: Freno bloqueado] se traba"
        )

    def test_codifica_sin_tipos(self):
        assert codificar_falla_reportada("", [], "solo texto libre") == "solo texto libre"
        assert codificar_falla_reportada("", [], "") == ""

    def test_decodifica_varios_tipos(self):
        texto = codificar_falla_reportada(
            "frenos,motor,electrico",
            ["Pastillas desgastadas", "No enciende"],
            "Problema al frenar y al arrancar",
        )
        dec = decodificar_falla_reportada(texto)
        assert dec["servicio_tipos"] == ["frenos", "motor", "electrico"]
        assert dec["servicio_labels"] == ["Frenos", "Motor", "Sistema Electrico"]
        assert dec["servicio_tipo"] == "frenos"
        assert dec["servicio_label"] == "Frenos"
        assert dec["fallas"] == ["Pastillas desgastadas", "No enciende"]
        assert dec["descripcion"] == "Problema al frenar y al arrancar"

    def test_decodifica_formato_anterior_de_un_solo_tipo(self):
        dec = decodificar_falla_reportada("[Frenos: Pastillas desgastadas] se escucha al frenar")
        assert dec["servicio_tipos"] == ["frenos"]
        assert dec["servicio_labels"] == ["Frenos"]
        assert dec["fallas"] == ["Pastillas desgastadas"]
        assert dec["descripcion"] == "se escucha al frenar"

        solo_tipo = decodificar_falla_reportada("[Motor]")
        assert solo_tipo["servicio_tipos"] == ["motor"]
        assert solo_tipo["fallas"] == []
        assert solo_tipo["descripcion"] == ""

    def test_decodifica_texto_libre_sin_corchetes(self):
        dec = decodificar_falla_reportada("Ruido al frenar")
        assert dec["servicio_tipos"] == []
        assert dec["descripcion"] == "Ruido al frenar"

    def test_decodifica_vacio(self):
        dec = decodificar_falla_reportada("")
        assert dec["servicio_tipos"] == []
        assert dec["fallas"] == []
        assert dec["descripcion"] == ""

    def test_roundtrip_varios_tipos(self):
        original = codificar_falla_reportada("motor,carroceria", ["Fuga de aceite"], "Fuga en el tanque")
        dec = decodificar_falla_reportada(original)
        assert codificar_falla_reportada(
            ",".join(dec["servicio_tipos"]), dec["fallas"], dec["descripcion"]
        ) == original


class TestOrdenConMultiplesTipos:
    def test_crear_orden_con_varios_tipos(self, client, auth_headers, sample_cliente, sample_moto, db):
        response = client.post(
            "/ordenes/nueva",
            data={
                "client_id": sample_cliente.id,
                "motorcycle_id": sample_moto.id,
                "servicio_tipo": "frenos,motor",
                "fallas_seleccionadas": ["Pastillas desgastadas", "No enciende"],
                "falla_reportada": "Se traba al frenar y no enciende",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

        from app.models.orden_servicio import OrdenServicio

        orden = db.query(OrdenServicio).order_by(OrdenServicio.id.desc()).first()
        assert orden.falla_reportada.startswith("[Frenos + Motor: ")
        assert "Se traba al frenar y no enciende" in orden.falla_reportada

        dec = decodificar_falla_reportada(orden.falla_reportada)
        assert dec["servicio_tipos"] == ["frenos", "motor"]
        assert dec["fallas"] == ["Pastillas desgastadas", "No enciende"]

    def test_detalle_muestra_todos_los_tipos(self, client, auth_headers, sample_cliente, sample_moto, db):
        client.post(
            "/ordenes/nueva",
            data={
                "client_id": sample_cliente.id,
                "motorcycle_id": sample_moto.id,
                "servicio_tipo": "frenos,motor",
                "fallas_seleccionadas": ["Pastillas desgastadas"],
                "falla_reportada": "Varias cosas a la vez",
            },
            follow_redirects=False,
        )

        from app.models.orden_servicio import OrdenServicio

        orden = db.query(OrdenServicio).order_by(OrdenServicio.id.desc()).first()

        import re

        detalle = client.get(f"/ordenes/{orden.codigo}")
        assert detalle.status_code == 200
        etiquetas = re.findall(r'class="service-type-tag"[^>]*>\s*([^<]+)<', detalle.text)
        assert [etiqueta.strip() for etiqueta in etiquetas] == ["Frenos", "Motor"]

    def test_pdf_de_orden_con_varios_tipos_y_ampersand(self, client, auth_headers, sample_cliente, sample_moto, db, tmp_path):
        client.post(
            "/ordenes/nueva",
            data={
                "client_id": sample_cliente.id,
                "motorcycle_id": sample_moto.id,
                "servicio_tipo": "frenos,motor",
                "fallas_seleccionadas": ["Pastillas desgastadas"],
                "falla_reportada": "Aceite & filtros, ruido al frenar",
            },
            follow_redirects=False,
        )

        from app.models.orden_servicio import OrdenServicio
        from app.services import export_service
        from app.services.pdf_generator import generar_pdf_orden

        orden = db.query(OrdenServicio).order_by(OrdenServicio.id.desc()).first()
        datos = export_service.generate_orden_pdf_data(db, orden.codigo)
        salida = tmp_path / "orden.pdf"
        generar_pdf_orden(datos, str(salida))

        contenido = salida.read_bytes()
        assert contenido.startswith(b"%PDF")
        assert len(contenido) > 1000
