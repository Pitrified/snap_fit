"""Tests for Piece integration with grid model (OrientedPieceType, get_segment_at)."""

from snap_fit.config.types import EdgePos
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation import PieceType
from snap_fit.grid.orientation_utils import detect_base_orientation
from snap_fit.grid.orientation_utils import get_original_edge_pos
from snap_fit.grid.orientation_utils import get_piece_type


class TestPieceOrientedPieceType:
    """Tests for Piece.oriented_piece_type derivation.

    Note: These tests require actual piece images to be loaded.
    For unit testing without images, we test the underlying functions directly
    in test_orientation_utils.py.
    """

    def test_get_piece_type_from_flat_count(self) -> None:
        """Test that get_piece_type correctly classifies pieces."""
        assert get_piece_type(0) == PieceType.INNER
        assert get_piece_type(1) == PieceType.EDGE
        assert get_piece_type(2) == PieceType.CORNER

    def test_detect_base_orientation_edge(self) -> None:
        """Test orientation detection for edge pieces."""
        # Flat on TOP = canonical = DEG_0
        assert detect_base_orientation([EdgePos.TOP]) == Orientation.DEG_0
        # Flat on RIGHT = 90° from canonical
        assert detect_base_orientation([EdgePos.RIGHT]) == Orientation.DEG_90
        # Flat on BOTTOM = 180° from canonical
        assert detect_base_orientation([EdgePos.BOTTOM]) == Orientation.DEG_180
        # Flat on LEFT = 270° from canonical
        assert detect_base_orientation([EdgePos.LEFT]) == Orientation.DEG_270

    def test_detect_base_orientation_corner(self) -> None:
        """Test orientation detection for corner pieces."""
        # TOP+LEFT = canonical = DEG_0
        assert detect_base_orientation([EdgePos.TOP, EdgePos.LEFT]) == Orientation.DEG_0
        # TOP+RIGHT = 90° from canonical
        assert (
            detect_base_orientation([EdgePos.TOP, EdgePos.RIGHT]) == Orientation.DEG_90
        )


class TestPieceGetSegmentAt:
    """Tests for Piece.get_segment_at method logic.

    Since we can't easily create real Piece objects in unit tests,
    we test the underlying get_original_edge_pos function.
    """

    def test_get_original_edge_pos_no_rotation(self) -> None:
        """Test that no rotation returns same edge position."""
        assert get_original_edge_pos(EdgePos.TOP, Orientation.DEG_0) == EdgePos.TOP
        assert get_original_edge_pos(EdgePos.RIGHT, Orientation.DEG_0) == EdgePos.RIGHT
        assert (
            get_original_edge_pos(EdgePos.BOTTOM, Orientation.DEG_0) == EdgePos.BOTTOM
        )
        assert get_original_edge_pos(EdgePos.LEFT, Orientation.DEG_0) == EdgePos.LEFT

    def test_get_original_edge_pos_90_rotation(self) -> None:
        """Test edge mapping after 90° rotation.

        When piece is rotated 90° clockwise:
        - What's now at TOP was originally at LEFT
        - What's now at RIGHT was originally at TOP
        - What's now at BOTTOM was originally at RIGHT
        - What's now at LEFT was originally at BOTTOM
        """
        assert get_original_edge_pos(EdgePos.TOP, Orientation.DEG_90) == EdgePos.LEFT
        assert get_original_edge_pos(EdgePos.RIGHT, Orientation.DEG_90) == EdgePos.TOP
        assert (
            get_original_edge_pos(EdgePos.BOTTOM, Orientation.DEG_90) == EdgePos.RIGHT
        )
        assert get_original_edge_pos(EdgePos.LEFT, Orientation.DEG_90) == EdgePos.BOTTOM

    def test_get_original_edge_pos_180_rotation(self) -> None:
        """Test edge mapping after 180° rotation."""
        assert get_original_edge_pos(EdgePos.TOP, Orientation.DEG_180) == EdgePos.BOTTOM
        assert get_original_edge_pos(EdgePos.RIGHT, Orientation.DEG_180) == EdgePos.LEFT
        assert get_original_edge_pos(EdgePos.BOTTOM, Orientation.DEG_180) == EdgePos.TOP
        assert get_original_edge_pos(EdgePos.LEFT, Orientation.DEG_180) == EdgePos.RIGHT

    def test_get_original_edge_pos_270_rotation(self) -> None:
        """Test edge mapping after 270° rotation."""
        assert get_original_edge_pos(EdgePos.TOP, Orientation.DEG_270) == EdgePos.RIGHT
        assert (
            get_original_edge_pos(EdgePos.RIGHT, Orientation.DEG_270) == EdgePos.BOTTOM
        )
        assert (
            get_original_edge_pos(EdgePos.BOTTOM, Orientation.DEG_270) == EdgePos.LEFT
        )
        assert get_original_edge_pos(EdgePos.LEFT, Orientation.DEG_270) == EdgePos.TOP
