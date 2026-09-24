import os
import uuid

import pytest

from app.models.site_config import DEFAULT_SITE_LOGO, SiteConfig
from app.services import site_service


@pytest.fixture(autouse=True)
def use_test_db(db, monkeypatch, setup_database):
    """El caché de branding debe leer de la misma BD que los tests (SQLite)."""
    monkeypatch.setattr(site_service, "session_factory", lambda: db)
    site_service.invalidate_cache()
    yield
    site_service.invalidate_cache()


class TestConfiguracionAccess:
    def test_login_required(self, client):
        r = client.get("/configuracion", follow_redirects=False)
        assert r.status_code in (302, 303)
        assert "/login" in r.headers["location"]

    def test_non_admin_forbidden(self, client, tecnico_user):
        client.post("/login", data={"email": "tecnico@test.com", "password": "tecnico123"},
                    follow_redirects=False)
        r = client.get("/configuracion")
        assert r.status_code == 403

    def test_admin_can_view(self, client, auth_headers):
        r = client.get("/configuracion", cookies=auth_headers)
        assert r.status_code == 200
        assert "Configuracion del Sitio" in r.text
        assert 'name="site_title"' in r.text

    def test_admin_menu_link(self, client, auth_headers):
        r = client.get("/dashboard", cookies=auth_headers)
        assert 'href="/configuracion"' in r.text

    def test_non_admin_menu_hidden(self, client, tecnico_user):
        client.post("/login", data={"email": "tecnico@test.com", "password": "tecnico123"},
                    follow_redirects=False)
        r = client.get("/dashboard")
        assert 'href="/configuracion"' not in r.text


class TestDefaults:
    def test_default_title_and_logo(self, client, auth_headers, db):
        r = client.get("/dashboard", cookies=auth_headers)
        assert "BikerZone" in r.text
        assert "/static/img/logo.svg" in r.text

    def test_no_row_means_defaults(self, db):
        assert db.query(SiteConfig).count() == 0
        assert site_service.site_title() == "BikerZone"
        assert site_service.site_logo() == DEFAULT_SITE_LOGO


class TestSaveTitle:
    def test_save_custom_title(self, client, auth_headers, db):
        r = client.post("/configuracion", data={"site_title": "Mi Taller Pro"},
                        cookies=auth_headers, follow_redirects=False)
        assert r.status_code == 303
        assert db.query(SiteConfig).one().site_title == "Mi Taller Pro"
        # el nuevo titulo se refleja en cualquier pagina (sidebar)
        r2 = client.get("/dashboard", cookies=auth_headers)
        assert "Mi Taller Pro" in r2.text

    def test_empty_title_rejected(self, client, auth_headers):
        r = client.post("/configuracion", data={"site_title": "   "},
                        cookies=auth_headers)
        assert r.status_code == 400
        assert "1 y 80" in r.text

    def test_long_title_rejected(self, client, auth_headers):
        r = client.post("/configuracion", data={"site_title": "x" * 81},
                        cookies=auth_headers)
        assert r.status_code == 400

    def test_title_persists_after_restart_cache_invalidation(self, client, auth_headers, db):
        client.post("/configuracion", data={"site_title": "Taller X"},
                    cookies=auth_headers, follow_redirects=False)
        site_service.invalidate_cache()
        assert site_service.site_title() == "Taller X"


class TestLogoUpload:
    TINY_PNG = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    def test_upload_logo(self, client, auth_headers, db):
        filename = f"test_logo_{uuid.uuid4().hex}.png"
        r = client.post(
            "/configuracion",
            data={"site_title": "BikerZone"},
            files={"logo": (filename, self.TINY_PNG, "image/png")},
            cookies=auth_headers,
            follow_redirects=False,
        )
        assert r.status_code == 303
        logo_path = db.query(SiteConfig).one().site_logo
        assert logo_path.startswith("/static/img/uploads/")
        disk_path = os.path.join("app/static/img/uploads", os.path.basename(logo_path))
        try:
            assert os.path.exists(disk_path)
            with open(disk_path, "rb") as f:
                assert f.read() == self.TINY_PNG
            # el sidebar usa el logo nuevo
            r2 = client.get("/dashboard", cookies=auth_headers)
            assert logo_path in r2.text
        finally:
            if os.path.exists(disk_path):
                os.remove(disk_path)

    def test_invalid_extension_rejected(self, client, auth_headers):
        r = client.post(
            "/configuracion",
            data={"site_title": "BikerZone"},
            files={"logo": ("evil.exe", b"MZ...", "application/octet-stream")},
            cookies=auth_headers,
        )
        assert r.status_code == 400
        assert "no valido" in r.text

    def test_oversized_logo_rejected(self, client, auth_headers):
        big = b"\x89PNG\r\n\x1a\n" + b"0" * (2 * 1024 * 1024 + 1)
        r = client.post(
            "/configuracion",
            data={"site_title": "BikerZone"},
            files={"logo": ("big.png", big, "image/png")},
            cookies=auth_headers,
        )
        assert r.status_code == 400
        assert "2MB" in r.text

    def test_restore_default_logo(self, client, auth_headers, db):
        # subir uno personalizado primero
        client.post(
            "/configuracion",
            data={"site_title": "BikerZone"},
            files={"logo": ("a.png", self.TINY_PNG, "image/png")},
            cookies=auth_headers,
            follow_redirects=False,
        )
        custom = db.query(SiteConfig).one().site_logo
        assert custom != DEFAULT_SITE_LOGO
        disk_path = os.path.join("app/static/img/uploads", os.path.basename(custom))

        # restaurar el predeterminado
        r = client.post("/configuracion",
                        data={"site_title": "BikerZone", "restore_logo": "1"},
                        cookies=auth_headers, follow_redirects=False)
        assert r.status_code == 303
        assert db.query(SiteConfig).one().site_logo == DEFAULT_SITE_LOGO
        assert not os.path.exists(disk_path)  # el archivo custom se elimina
