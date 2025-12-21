"""Puzzle management, matching, and generation."""

from snap_fit.puzzle.puzzle_config import PuzzleConfig
from snap_fit.puzzle.puzzle_config import SheetLayout
from snap_fit.puzzle.puzzle_generator import BezierEdge
from snap_fit.puzzle.puzzle_generator import BezierSegment
from snap_fit.puzzle.puzzle_generator import EdgeType
from snap_fit.puzzle.puzzle_generator import PuzzleGenerator
from snap_fit.puzzle.puzzle_generator import PuzzlePiece
from snap_fit.puzzle.puzzle_generator import SeededRandom
from snap_fit.puzzle.puzzle_generator import generate_label
from snap_fit.puzzle.puzzle_rasterizer import PuzzleRasterizer
from snap_fit.puzzle.puzzle_sheet import PuzzleSheetComposer

__all__ = [
    "BezierEdge",
    "BezierSegment",
    "EdgeType",
    "PuzzleConfig",
    "PuzzleGenerator",
    "PuzzlePiece",
    "PuzzleRasterizer",
    "PuzzleSheetComposer",
    "SeededRandom",
    "SheetLayout",
    "generate_label",
]
