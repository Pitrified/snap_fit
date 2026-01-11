"""Application settings via pydantic-settings (v2 API)."""

from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True

    # CORS
    cors_allow_origins: list[str] = ["*"]

    # Paths (optional overrides)
    data_dir: str = "data"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
