class TestOrdenesCompra:
    def test_lista_ordenes_compra(self, client, auth_headers, sample_proveedor, db):
        from app.models.orden_compra import OrdenCompra

        oc = OrdenCompra(
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

        oc = OrdenCompra(
            supplier_id=sample_proveedor.id,
            estado="pending",
        )
        db.add(oc)
        db.commit()
        db.refresh(oc)

        response = client.get(f"/ordenes-compra/{oc.codigo}", cookies=auth_headers)
        assert response.status_code == 200
        assert "OC-" in response.text

    def test_crear_orden_compra(self, client, auth_headers, sample_proveedor):
        response = client.post(
            "/ordenes-compra/nueva",
            data={
                "supplier_id": sample_proveedor.id,
                "notas": "Compra urgente",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_cambiar_estado_compra(self, client, auth_headers, sample_proveedor, db):
        from app.models.orden_compra import OrdenCompra

        oc = OrdenCompra(
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

        oc = OrdenCompra(
            supplier_id=sample_proveedor.id,
            estado="pending",
        )
        db.add(oc)
        db.commit()
        db.refresh(oc)

        for estado in ["sent", "partial", "received"]:
            response = client.post(
                f"/ordenes-compra/{oc.codigo}/cambiar-estado",
                data={"nuevo_estado": estado},
                follow_redirects=False,
            )
            assert response.status_code == 303
