from app.database import SessionLocal
from app.models.site_config import DEFAULT_SITE_LOGO, DEFAULT_SITE_TITLE, SiteConfig

session_factory = SessionLocal  # los tests pueden reemplazarlo

_cache: dict | None = None


def invalidate_cache() -> None:
    global _cache
    _cache = None


def get_site_config(db) -> SiteConfig:
    row = db.query(SiteConfig).filter(SiteConfig.id == 1).first()
    if not row:
        row = SiteConfig(id=1, site_title=DEFAULT_SITE_TITLE, site_logo=DEFAULT_SITE_LOGO)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _load_cached() -> dict:
    global _cache
    if _cache is None:
        title, logo = DEFAULT_SITE_TITLE, DEFAULT_SITE_LOGO
        try:
            db = session_factory()
            try:
                row = db.query(SiteConfig).filter(SiteConfig.id == 1).first()
                if row:
                    title = row.site_title or DEFAULT_SITE_TITLE
                    logo = row.site_logo or DEFAULT_SITE_LOGO
            finally:
                db.close()
        except Exception:
            pass  # BD no disponible: usar valores por defecto
        _cache = {"title": title, "logo": logo}
    return _cache


def site_title() -> str:
    return _load_cached()["title"]


def site_logo() -> str:
    return _load_cached()["logo"]
