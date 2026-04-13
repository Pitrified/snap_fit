"""Application settings via pydantic-settings (v2 API)."""

from functools import lru_cache
from pathlib import Path

from pydantic import PrivateAttr
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
    cache_dir: str = "cache"

    # Dataset selection - can also be set at runtime via set_dataset()
    current_dataset: str | None = None

    # Runtime-mutable dataset override (not persisted to env)
    _current_dataset_override: str | None = PrivateAttr(default=None)

    @property
    def cache_path(self) -> Path:
        """Return the cache directory as a Path."""
        return Path(self.cache_dir)

    @property
    def data_path(self) -> Path:
        """Return the data directory as a Path."""
        return Path(self.data_dir)

    @property
    def active_dataset(self) -> str | None:
        """Return the active dataset (runtime override takes precedence)."""
        return self._current_dataset_override or self.current_dataset

    def set_dataset(self, tag: str | None) -> None:
        """Set the active dataset tag at runtime."""
        self._current_dataset_override = tag

    def available_datasets(self) -> list[str]:
        """List tag names that have a dataset.db in cache_path."""
        return sorted(p.parent.name for p in self.cache_path.glob("*/dataset.db"))


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
