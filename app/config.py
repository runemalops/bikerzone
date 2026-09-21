import os
import secrets
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

INSECURE_DEFAULTS = {
    "SECRET_KEY": "cambia-esta-clave-secreta",
    "ADMIN_PASSWORD": "admin123",
}


def _get_secret(env_var: str, default: str = "") -> str:
    value = os.getenv(env_var, default)
    if value in ("", None) or value == INSECURE_DEFAULTS.get(env_var):
        if env_var == "SECRET_KEY":
            logger.warning(
                "SECRET_KEY no configurado o usa valor inseguro. "
                "Sesiones se invalidaran en cada reinicio. "
                "Configure SECRET_KEY en .env para produccion."
            )
            return secrets.token_hex(32)
        return ""
    return value


class Settings:
    PROJECT_NAME: str = "BikerZone"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "Sistema de gestion para taller de motocicletas"

    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "bikerzone")
    DB_USER: str = os.getenv("DB_USER", "bikerzone_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # Security - Reject hardcoded insecure defaults
    SECRET_KEY: str = _get_secret("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Admin - No hardcoded default for password
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@bikerzone.com")
    ADMIN_PASSWORD: str = _get_secret("ADMIN_PASSWORD")

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    @property
    def IS_DEVELOPMENT(self) -> bool:
        return self.ENVIRONMENT == "development"

    # Currency
    CURRENCY_SYMBOL: str = os.getenv("CURRENCY_SYMBOL", "Q")
    CURRENCY_CODE: str = os.getenv("CURRENCY_CODE", "GTQ")
    CURRENCY_DECIMALS: int = int(os.getenv("CURRENCY_DECIMALS", "2"))

    # Tax
    IVA_RATE: float = float(os.getenv("IVA_RATE", "0.12"))

    @property
    def IS_DEVELOPMENT(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()
