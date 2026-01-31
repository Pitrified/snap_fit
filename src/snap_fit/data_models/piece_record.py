"""Piece record model for database persistence."""

from typing import TYPE_CHECKING

from pydantic import BaseModel

from snap_fit.config.types import CornerPos
from snap_fit.data_models.piece_id import PieceId
from snap_fit.grid.orientation import OrientedPieceType

if TYPE_CHECKING:
    from snap_fit.puzzle.piece import Piece


class PieceRecord(BaseModel):
    """DB-friendly representation of a Piece.

    Stores computed geometry metadata without heavy numpy arrays.
    Full contour points are stored separately in binary cache files.

    Attributes:
        piece_id: Unique identifier for the piece.
        corners: Corner positions as {CornerPos.value: (x, y)}.
        segment_shapes: Segment shapes as {EdgePos.value: SegmentShape.value}.
        oriented_piece_type: Piece type with orientation (INNER/EDGE/CORNER).
        flat_edges: List of flat edge positions (EdgePos.value).
        contour_point_count: Number of points in the contour.
        contour_region: Bounding rectangle (x, y, width, height).
    """

    piece_id: PieceId
    corners: dict[str, tuple[int, int]]
    segment_shapes: dict[str, str]
    oriented_piece_type: OrientedPieceType | None
    flat_edges: list[str]
    contour_point_count: int
    contour_region: tuple[int, int, int, int]

    @classmethod
    def from_piece(cls, piece: "Piece") -> "PieceRecord":
        """Create a PieceRecord from a Piece object.

        Args:
            piece: The Piece object to convert.

        Returns:
            A PieceRecord with metadata from the Piece.
        """
        return cls(
            piece_id=piece.piece_id,
            corners={pos.value: tuple(piece.corners[pos]) for pos in CornerPos},
            segment_shapes={
                pos.value: seg.shape.value for pos, seg in piece.segments.items()
            },
            oriented_piece_type=piece.oriented_piece_type,
            flat_edges=[e.value for e in piece.flat_edges],
            contour_point_count=len(piece.contour.cv_contour),
            contour_region=piece.contour.region,
        )
