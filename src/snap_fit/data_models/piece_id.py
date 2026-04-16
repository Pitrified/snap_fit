"""Piece ID model for uniquely identifying pieces across sheets."""

from __future__ import annotations

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

    @classmethod
    def from_str(cls, s: str) -> PieceId:
        """Parse ``'sheet_id:piece_idx'`` format.

        Args:
            s: String in ``sheet_id:piece_idx`` format.

        Returns:
            Parsed ``PieceId``.

        Raises:
            ValueError: If the string does not contain a ``:``.
        """
        sheet_id, piece_idx = s.rsplit(":", 1)
        return cls(sheet_id=sheet_id, piece_id=int(piece_idx))
