from fastapi.templating import Jinja2Templates
from app.config import settings

templates = Jinja2Templates(directory="app/templates")

templates.env.globals["currency_symbol"] = settings.CURRENCY_SYMBOL
templates.env.globals["currency_code"] = settings.CURRENCY_CODE
templates.env.globals["currency_decimals"] = settings.CURRENCY_DECIMALS
