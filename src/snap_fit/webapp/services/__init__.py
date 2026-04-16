"""Thin service wrappers for webapp domain calls."""

from . import interactive_service
from . import piece_service
from . import puzzle_service

__all__ = ["interactive_service", "piece_service", "puzzle_service"]
