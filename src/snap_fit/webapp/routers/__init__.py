"""Router package for the webapp."""

from . import debug
from . import interactive
from . import piece_ingestion
from . import puzzle_solve
from . import ui

__all__ = ["debug", "interactive", "piece_ingestion", "puzzle_solve", "ui"]
