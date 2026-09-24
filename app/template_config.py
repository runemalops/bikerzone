from fastapi.templating import Jinja2Templates
from app.config import settings
from app.services import site_service

templates = Jinja2Templates(directory="app/templates")

templates.env.globals["currency_symbol"] = settings.CURRENCY_SYMBOL
templates.env.globals["currency_code"] = settings.CURRENCY_CODE
templates.env.globals["currency_decimals"] = settings.CURRENCY_DECIMALS

# Branding del sitio (titulo y logo configurables desde /configuracion)
templates.env.globals["site_title"] = site_service.site_title
templates.env.globals["site_logo"] = site_service.site_logo
