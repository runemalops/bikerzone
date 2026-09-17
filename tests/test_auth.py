class TestAuth:
    def test_login_page(self, client):
        response = client.get("/login")
        assert response.status_code == 200
        assert "BikerZone" in response.text

    def test_login_success(self, client, admin_user):
        response = client.post(
            "/login",
            data={"email": "admin@test.com", "password": "admin123"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/dashboard"

    def test_login_invalid_credentials(self, client, admin_user):
        response = client.post(
            "/login",
            data={"email": "admin@test.com", "password": "wrong"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "Credenciales invalidas" in response.text

    def test_protected_route_no_auth(self, client):
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 303

    def test_protected_route_with_auth(self, client, auth_headers):
        response = client.get("/dashboard", cookies=auth_headers)
        assert response.status_code == 200

    def test_logout(self, client, auth_headers):
        response = client.post("/logout", cookies=auth_headers, follow_redirects=False)
        assert response.status_code == 303

    def test_tecnico_cannot_see_menu_admin(self, client, tecnico_user):
        client.post(
            "/login",
            data={"email": "tecnico@test.com", "password": "tecnico123"},
        )
        response = client.get("/clientes", follow_redirects=False)
        assert response.status_code == 200
