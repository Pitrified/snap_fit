"""Orientation enums and types for grid model."""

from __future__ import annotations

from enum import IntEnum

from pydantic import BaseModel


class Orientation(IntEnum):
    """Orientation enum representing rotation in degrees.

    Values are 0, 90, 180, 270 degrees clockwise.
    Supports arithmetic for rotation composition.
    """

    DEG_0 = 0
    DEG_90 = 90
    DEG_180 = 180
    DEG_270 = 270

    def __add__(self, other: Orientation | int) -> Orientation:
        """Add two orientations (compose rotations)."""
        other_val = other.value if isinstance(other, Orientation) else other
        return Orientation((self.value + other_val) % 360)

    def __radd__(self, other: int) -> Orientation:
        """Right-add for int + Orientation."""
        return self.__add__(other)

    def __sub__(self, other: Orientation | int) -> Orientation:
        """Subtract orientations (inverse rotation)."""
        other_val = other.value if isinstance(other, Orientation) else other
        return Orientation((self.value - other_val) % 360)

    def __rsub__(self, other: int) -> Orientation:
        """Right-subtract for int - Orientation."""
        return Orientation((other - self.value) % 360)

    def __neg__(self) -> Orientation:
        """Negate orientation (inverse rotation)."""
        return Orientation((360 - self.value) % 360)

    @property
    def steps(self) -> int:
        """Return the number of 90-degree steps (0, 1, 2, 3)."""
        return self.value // 90

    @classmethod
    def from_steps(cls, steps: int) -> Orientation:
        """Create orientation from number of 90-degree steps."""
        return cls((steps % 4) * 90)


class PieceType(IntEnum):
    """Piece type based on number of flat edges.

    INNER: 0 flat edges (4 interlocking edges)
    EDGE: 1 flat edge (puzzle boundary)
    CORNER: 2 flat edges (puzzle corner)
    """

    INNER = 0
    EDGE = 1
    CORNER = 2


class OrientedPieceType(BaseModel, frozen=True):
    """Combines piece type with its orientation.

    Used for both:
    - Describing a photographed piece's detected type and base orientation
    - Describing a grid slot's required type and orientation

    Canonical conventions:
    - EDGE pieces: flat edge on TOP in canonical orientation (DEG_0)
    - CORNER pieces: flat edges on TOP + LEFT in canonical orientation (DEG_0)
    - INNER pieces: orientation is arbitrary (no flat edges to anchor)

    Attributes:
        piece_type: The type of piece (CORNER, EDGE, INNER).
        orientation: The orientation relative to canonical position.
    """

    piece_type: PieceType
    orientation: Orientation

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.piece_type.name}@{self.orientation.value}°"

    def __repr__(self) -> str:
        """Detailed repr for debugging."""
        return f"OrientedPieceType({self.piece_type.name}, {self.orientation.name})"
