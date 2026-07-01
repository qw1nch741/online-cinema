import secrets
from pathlib import Path
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class BaseAppSettings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent

    # 1. Native Environment Declarations (Clean and Scannable)
    EMAIL_HOST: str = "localhost"
    EMAIL_PORT: int = 25
    EMAIL_USE_TLS: bool = False

    MINIO_HOST: str = "cinema_minio_dev"  # Match your docker service names!
    MINIO_PORT: int = 9000

    # 2. Tell Pydantic to read from a local .env file automatically
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class Settings(BaseAppSettings):
    POSTGRES_USER: str = "cinema_admin"
    POSTGRES_PASSWORD: str = "cinema_password_2026"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_DB_PORT: int = 5432
    POSTGRES_DB: str = "online_cinema_dev"

    # Use safe string secrets generation to prevent byte string validation errors
    SECRET_KEY_ACCESS: str = secrets.token_hex(32)
    SECRET_KEY_REFRESH: str = secrets.token_hex(32)

    # 3. Dynamic SQLAlchemy Driver String Constructor
    @computed_field
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB}"


@lru_cache
def get_settings() -> Settings:
    """Instantiates and caches the application environment settings configuration."""
    return Settings()
