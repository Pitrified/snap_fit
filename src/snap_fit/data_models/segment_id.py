"""Segment ID model for uniquely identifying segments across sheets/pieces/edges."""

from pydantic import BaseModel

from snap_fit.config.types import EdgePos


class SegmentId(BaseModel, frozen=True):
    """Unique identifier for a segment across sheets/pieces/edges.

    Frozen for hashability (can be used in sets/dicts).

    Attributes:
        sheet_id: The sheet identifier string.
        piece_id: The piece index within the sheet.
        edge_pos: The edge position (LEFT, BOTTOM, RIGHT, TOP).
    """

    sheet_id: str
    piece_id: int
    edge_pos: EdgePos

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.sheet_id}:{self.piece_id}:{self.edge_pos.value}"

    def __repr__(self) -> str:
        """Detailed repr for debugging."""
        return f"SegmentId({self.sheet_id!r}, {self.piece_id}, {self.edge_pos!r})"

    @property
    def as_tuple(self) -> tuple[str, int, EdgePos]:
        """Return as tuple for unpacking compatibility."""
        return (self.sheet_id, self.piece_id, self.edge_pos)
