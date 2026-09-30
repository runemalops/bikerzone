class TestOrdenesCompra:
    def test_lista_ordenes_compra(self, client, auth_headers, sample_proveedor, db):
        from app.models.orden_compra import OrdenCompra
        from tests.conftest import generate_oc_codigo

        oc = OrdenCompra(
            codigo=generate_oc_codigo(db),
            supplier_id=sample_proveedor.id,
            estado="pending",
        )
        db.add(oc)
        db.commit()

        response = client.get("/ordenes-compra", cookies=auth_headers)
        assert response.status_code == 200
        assert "OC-" in response.text

    def test_detalle_orden_compra(self, client, auth_headers, sample_proveedor, db):
        from app.models.orden_compra import OrdenCompra
        from tests.conftest import generate_oc_codigo

        oc = OrdenCompra(
            codigo=generate_oc_codigo(db),
            supplier_id=sample_proveedor.id,
            estado="pending",
        )
        db.add(oc)
        db.commit()
        db.refresh(oc)

        response = client.get(f"/ordenes-compra/{oc.codigo}", cookies=auth_headers)
        assert response.status_code == 200
        assert "OC-" in response.text

    def test_crear_orden_compra(self, client, auth_headers, sample_proveedor, sample_repuesto):
        response = client.post(
            "/ordenes-compra/nueva",
            data={
                "supplier_id": sample_proveedor.id,
                "notas": "Compra urgente",
                "repuestos_ids": [sample_repuesto.id],
                "cantidades": [5],
                "precios": ["200"],
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_cambiar_estado_compra(self, client, auth_headers, sample_proveedor, db):
        from app.models.orden_compra import OrdenCompra
        from tests.conftest import generate_oc_codigo

        oc = OrdenCompra(
            codigo=generate_oc_codigo(db),
            supplier_id=sample_proveedor.id,
            estado="pending",
        )
        db.add(oc)
        db.commit()
        db.refresh(oc)

        response = client.post(
            f"/ordenes-compra/{oc.codigo}/cambiar-estado",
            data={"nuevo_estado": "sent"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_flujo_compra_completo(self, client, auth_headers, sample_proveedor, db):
        from app.models.orden_compra import OrdenCompra
        from tests.conftest import generate_oc_codigo

        oc = OrdenCompra(
            codigo=generate_oc_codigo(db),
            supplier_id=sample_proveedor.id,
            estado="pending",
        )
        db.add(oc)
        db.commit()
        db.refresh(oc)

        for estado in ["sent", "cancelled"]:
            response = client.post(
                f"/ordenes-compra/{oc.codigo}/cambiar-estado",
                data={"nuevo_estado": estado},
                follow_redirects=False,
            )
            assert response.status_code == 303

    def test_conflicto_de_codigo_muestra_error_real(self, client, auth_headers, sample_proveedor, sample_repuesto, db, monkeypatch):
        from app.models.orden_compra import OrdenCompra
        from app.services import orden_compra_service

        ocupado = OrdenCompra(codigo="OC-2099-00001", supplier_id=sample_proveedor.id, estado="pending")
        db.add(ocupado)
        db.commit()

        monkeypatch.setattr(orden_compra_service, "generate_codigo", lambda _db: "OC-2099-00001")

        response = client.post(
            "/ordenes-compra/nueva",
            data={
                "supplier_id": sample_proveedor.id,
                "notas": "",
                "repuestos_ids": [sample_repuesto.id],
                "cantidades": [1],
                "precios": ["100"],
            },
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "codigo unico" in response.text
        assert "No se pudo asignar" in response.text
