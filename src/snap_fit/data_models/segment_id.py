"""Segment ID model for uniquely identifying segments across sheets/pieces/edges."""

from pydantic import BaseModel

from snap_fit.config.types import EdgePos
from snap_fit.data_models.piece_id import PieceId


class SegmentId(BaseModel, frozen=True):
    """Unique identifier for a segment across sheets/pieces/edges.

    Frozen for hashability (can be used in sets/dicts).

    Attributes:
        piece_id: The PieceId identifying the piece.
        edge_pos: The edge position (LEFT, BOTTOM, RIGHT, TOP).
    """

    piece_id: PieceId
    edge_pos: EdgePos

    @property
    def sheet_id(self) -> str:
        """Return the sheet ID for backward compatibility."""
        return self.piece_id.sheet_id

    @property
    def piece_id_int(self) -> int:
        """Return the piece ID integer for backward compatibility."""
        return self.piece_id.piece_id

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.piece_id}:{self.edge_pos.value}"

    def __repr__(self) -> str:
        """Detailed repr for debugging."""
        return f"SegmentId({self.piece_id!r}, {self.edge_pos!r})"

    @property
    def as_tuple(self) -> tuple[str, int, EdgePos]:
        """Return as tuple for unpacking compatibility."""
        return (self.sheet_id, self.piece_id_int, self.edge_pos)
