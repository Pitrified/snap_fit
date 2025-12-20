"""Piece ID model for uniquely identifying pieces across sheets."""

from pydantic import BaseModel


class PieceId(BaseModel, frozen=True):
    """Unique identifier for a piece across sheets.

    Frozen for hashability (can be used in sets/dicts).

    Attributes:
        sheet_id: The sheet identifier string.
        piece_id: The piece index within the sheet.
    """

    sheet_id: str
    piece_id: int

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.sheet_id}:{self.piece_id}"

    def __repr__(self) -> str:
        """Detailed repr for debugging."""
        return f"PieceId({self.sheet_id!r}, {self.piece_id})"
