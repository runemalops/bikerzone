import os
from dotenv import load_dotenv

load_dotenv()


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

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "cambia-esta-clave-secreta")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Admin
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@bikerzone.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Currency
    CURRENCY_SYMBOL: str = os.getenv("CURRENCY_SYMBOL", "Q")
    CURRENCY_CODE: str = os.getenv("CURRENCY_CODE", "GTQ")
    CURRENCY_DECIMALS: int = int(os.getenv("CURRENCY_DECIMALS", "2"))

    @property
    def IS_DEVELOPMENT(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()
