"""Core utilities for the webapp."""

__all__ = ["configure_logging", "get_settings"]

from .logging_config import configure_logging
from .settings import get_settings
