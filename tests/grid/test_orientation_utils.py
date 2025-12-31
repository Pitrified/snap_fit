"""Tests for orientation utility functions."""

import pytest

from snap_fit.config.types import EdgePos
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation import OrientedPieceType
from snap_fit.grid.orientation import PieceType
from snap_fit.grid.orientation_utils import compute_rotation
from snap_fit.grid.orientation_utils import detect_base_orientation
from snap_fit.grid.orientation_utils import get_original_edge_pos
from snap_fit.grid.orientation_utils import get_piece_type
from snap_fit.grid.orientation_utils import get_rotated_edge_pos


class TestGetPieceType:
    """Tests for get_piece_type function."""

    def test_inner(self) -> None:
        """Test 0 flat edges -> INNER."""
        assert get_piece_type(0) == PieceType.INNER

    def test_edge(self) -> None:
        """Test 1 flat edge -> EDGE."""
        assert get_piece_type(1) == PieceType.EDGE

    def test_corner(self) -> None:
        """Test 2 flat edges -> CORNER."""
        assert get_piece_type(2) == PieceType.CORNER

    def test_invalid(self) -> None:
        """Test invalid flat edge count raises ValueError."""
        with pytest.raises(ValueError, match="Invalid flat_edge_count"):
            get_piece_type(3)
        with pytest.raises(ValueError, match="Invalid flat_edge_count"):
            get_piece_type(-1)


class TestDetectBaseOrientation:
    """Tests for detect_base_orientation function."""

    def test_inner_no_flats(self) -> None:
        """Test inner piece (no flats) returns DEG_0."""
        assert detect_base_orientation([]) == Orientation.DEG_0

    def test_edge_flat_on_top(self) -> None:
        """Test edge piece with flat on top (canonical) returns DEG_0."""
        assert detect_base_orientation([EdgePos.TOP]) == Orientation.DEG_0

    def test_edge_flat_on_right(self) -> None:
        """Test edge piece with flat on right returns DEG_90."""
        assert detect_base_orientation([EdgePos.RIGHT]) == Orientation.DEG_90

    def test_edge_flat_on_bottom(self) -> None:
        """Test edge piece with flat on bottom returns DEG_180."""
        assert detect_base_orientation([EdgePos.BOTTOM]) == Orientation.DEG_180

    def test_edge_flat_on_left(self) -> None:
        """Test edge piece with flat on left returns DEG_270."""
        assert detect_base_orientation([EdgePos.LEFT]) == Orientation.DEG_270

    def test_corner_top_left(self) -> None:
        """Test corner with flats on top+left (canonical) returns DEG_0."""
        assert detect_base_orientation([EdgePos.TOP, EdgePos.LEFT]) == Orientation.DEG_0
        # Order shouldn't matter
        assert detect_base_orientation([EdgePos.LEFT, EdgePos.TOP]) == Orientation.DEG_0

    def test_corner_top_right(self) -> None:
        """Test corner with flats on top+right returns DEG_90."""
        assert (
            detect_base_orientation([EdgePos.TOP, EdgePos.RIGHT]) == Orientation.DEG_90
        )

    def test_corner_bottom_right(self) -> None:
        """Test corner with flats on bottom+right returns DEG_180."""
        assert (
            detect_base_orientation([EdgePos.BOTTOM, EdgePos.RIGHT])
            == Orientation.DEG_180
        )

    def test_corner_bottom_left(self) -> None:
        """Test corner with flats on bottom+left returns DEG_270."""
        assert (
            detect_base_orientation([EdgePos.BOTTOM, EdgePos.LEFT])
            == Orientation.DEG_270
        )


class TestComputeRotation:
    """Tests for compute_rotation function."""

    def test_same_orientation(self) -> None:
        """Test piece already at target orientation needs no rotation."""
        piece = OrientedPieceType(
            piece_type=PieceType.EDGE, orientation=Orientation.DEG_90
        )
        target = OrientedPieceType(
            piece_type=PieceType.EDGE, orientation=Orientation.DEG_90
        )
        assert compute_rotation(piece, target) == Orientation.DEG_0

    def test_rotation_needed(self) -> None:
        """Test computing rotation when piece needs to rotate."""
        # Piece has flat on right (90°), target wants flat on bottom (180°)
        piece = OrientedPieceType(
            piece_type=PieceType.EDGE, orientation=Orientation.DEG_90
        )
        target = OrientedPieceType(
            piece_type=PieceType.EDGE, orientation=Orientation.DEG_180
        )
        # Need 90° rotation to go from 90° to 180°
        assert compute_rotation(piece, target) == Orientation.DEG_90

    def test_rotation_wrap(self) -> None:
        """Test rotation that wraps around."""
        # Piece at 270°, target at 0°
        piece = OrientedPieceType(
            piece_type=PieceType.CORNER, orientation=Orientation.DEG_270
        )
        target = OrientedPieceType(
            piece_type=PieceType.CORNER, orientation=Orientation.DEG_0
        )
        # Need 90° rotation to go from 270° to 0°
        assert compute_rotation(piece, target) == Orientation.DEG_90


class TestGetRotatedEdgePos:
    """Tests for get_rotated_edge_pos function."""

    def test_no_rotation(self) -> None:
        """Test that no rotation leaves edge position unchanged."""
        assert get_rotated_edge_pos(EdgePos.TOP, Orientation.DEG_0) == EdgePos.TOP
        assert get_rotated_edge_pos(EdgePos.RIGHT, Orientation.DEG_0) == EdgePos.RIGHT

    def test_rotate_90(self) -> None:
        """Test 90° rotation moves edges clockwise."""
        assert get_rotated_edge_pos(EdgePos.TOP, Orientation.DEG_90) == EdgePos.RIGHT
        assert get_rotated_edge_pos(EdgePos.RIGHT, Orientation.DEG_90) == EdgePos.BOTTOM
        assert get_rotated_edge_pos(EdgePos.BOTTOM, Orientation.DEG_90) == EdgePos.LEFT
        assert get_rotated_edge_pos(EdgePos.LEFT, Orientation.DEG_90) == EdgePos.TOP

    def test_rotate_180(self) -> None:
        """Test 180° rotation flips edges."""
        assert get_rotated_edge_pos(EdgePos.TOP, Orientation.DEG_180) == EdgePos.BOTTOM
        assert get_rotated_edge_pos(EdgePos.RIGHT, Orientation.DEG_180) == EdgePos.LEFT
        assert get_rotated_edge_pos(EdgePos.BOTTOM, Orientation.DEG_180) == EdgePos.TOP
        assert get_rotated_edge_pos(EdgePos.LEFT, Orientation.DEG_180) == EdgePos.RIGHT

    def test_rotate_270(self) -> None:
        """Test 270° rotation moves edges counter-clockwise."""
        assert get_rotated_edge_pos(EdgePos.TOP, Orientation.DEG_270) == EdgePos.LEFT
        assert get_rotated_edge_pos(EdgePos.RIGHT, Orientation.DEG_270) == EdgePos.TOP


class TestGetOriginalEdgePos:
    """Tests for get_original_edge_pos function."""

    def test_no_rotation(self) -> None:
        """Test that no rotation leaves edge position unchanged."""
        assert get_original_edge_pos(EdgePos.TOP, Orientation.DEG_0) == EdgePos.TOP

    def test_inverse_of_rotated(self) -> None:
        """Test that get_original_edge_pos is inverse of get_rotated_edge_pos."""
        for original in EdgePos:
            for rotation in Orientation:
                rotated = get_rotated_edge_pos(original, rotation)
                recovered = get_original_edge_pos(rotated, rotation)
                assert recovered == original

    def test_rotate_90_inverse(self) -> None:
        """Test finding original edge after 90° rotation."""
        # After 90° rotation, what's at TOP was originally at LEFT
        assert get_original_edge_pos(EdgePos.TOP, Orientation.DEG_90) == EdgePos.LEFT
        # After 90° rotation, what's at RIGHT was originally at TOP
        assert get_original_edge_pos(EdgePos.RIGHT, Orientation.DEG_90) == EdgePos.TOP
