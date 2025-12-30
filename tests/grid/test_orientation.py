"""Tests for Orientation enum and OrientedPieceType."""

from pydantic import ValidationError
import pytest

from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation import OrientedPieceType
from snap_fit.grid.orientation import PieceType


class TestOrientation:
    """Tests for Orientation enum."""

    def test_values(self) -> None:
        """Test orientation values."""
        assert Orientation.DEG_0.value == 0
        assert Orientation.DEG_90.value == 90
        assert Orientation.DEG_180.value == 180
        assert Orientation.DEG_270.value == 270

    def test_add_orientations(self) -> None:
        """Test adding two orientations."""
        assert Orientation.DEG_0 + Orientation.DEG_90 == Orientation.DEG_90
        assert Orientation.DEG_90 + Orientation.DEG_90 == Orientation.DEG_180
        assert Orientation.DEG_180 + Orientation.DEG_180 == Orientation.DEG_0
        assert Orientation.DEG_270 + Orientation.DEG_180 == Orientation.DEG_90

    def test_add_int(self) -> None:
        """Test adding orientation and int."""
        assert Orientation.DEG_0 + 90 == Orientation.DEG_90
        assert Orientation.DEG_270 + 90 == Orientation.DEG_0

    def test_sub_orientations(self) -> None:
        """Test subtracting orientations."""
        assert Orientation.DEG_90 - Orientation.DEG_90 == Orientation.DEG_0
        assert Orientation.DEG_0 - Orientation.DEG_90 == Orientation.DEG_270
        assert Orientation.DEG_180 - Orientation.DEG_270 == Orientation.DEG_270

    def test_sub_int(self) -> None:
        """Test subtracting int from orientation."""
        assert Orientation.DEG_90 - 90 == Orientation.DEG_0
        assert Orientation.DEG_0 - 90 == Orientation.DEG_270

    def test_neg(self) -> None:
        """Test negating orientation (inverse)."""
        assert -Orientation.DEG_0 == Orientation.DEG_0
        assert -Orientation.DEG_90 == Orientation.DEG_270
        assert -Orientation.DEG_180 == Orientation.DEG_180
        assert -Orientation.DEG_270 == Orientation.DEG_90

    def test_steps(self) -> None:
        """Test steps property."""
        assert Orientation.DEG_0.steps == 0
        assert Orientation.DEG_90.steps == 1
        assert Orientation.DEG_180.steps == 2
        assert Orientation.DEG_270.steps == 3

    def test_from_steps(self) -> None:
        """Test creating orientation from steps."""
        assert Orientation.from_steps(0) == Orientation.DEG_0
        assert Orientation.from_steps(1) == Orientation.DEG_90
        assert Orientation.from_steps(2) == Orientation.DEG_180
        assert Orientation.from_steps(3) == Orientation.DEG_270
        # Wrapping
        assert Orientation.from_steps(4) == Orientation.DEG_0
        assert Orientation.from_steps(-1) == Orientation.DEG_270


class TestPieceType:
    """Tests for PieceType enum."""

    def test_values(self) -> None:
        """Test piece type values match flat edge count."""
        assert PieceType.INNER.value == 0
        assert PieceType.EDGE.value == 1
        assert PieceType.CORNER.value == 2


class TestOrientedPieceType:
    """Tests for OrientedPieceType model."""

    def test_creation(self) -> None:
        """Test creating OrientedPieceType."""
        opt = OrientedPieceType(
            piece_type=PieceType.CORNER, orientation=Orientation.DEG_90
        )
        assert opt.piece_type == PieceType.CORNER
        assert opt.orientation == Orientation.DEG_90

    def test_frozen(self) -> None:
        """Test that OrientedPieceType is immutable."""
        opt = OrientedPieceType(
            piece_type=PieceType.EDGE, orientation=Orientation.DEG_0
        )
        with pytest.raises(ValidationError):
            opt.piece_type = PieceType.INNER  # type: ignore[misc]

    def test_hashable(self) -> None:
        """Test that OrientedPieceType can be used in sets/dicts."""
        opt1 = OrientedPieceType(
            piece_type=PieceType.CORNER, orientation=Orientation.DEG_0
        )
        opt2 = OrientedPieceType(
            piece_type=PieceType.CORNER, orientation=Orientation.DEG_0
        )
        opt3 = OrientedPieceType(
            piece_type=PieceType.CORNER, orientation=Orientation.DEG_90
        )

        # Same values should be equal and have same hash
        assert opt1 == opt2
        assert hash(opt1) == hash(opt2)

        # Different values should be different
        assert opt1 != opt3

        # Can be used in set
        s = {opt1, opt2, opt3}
        assert len(s) == 2

    def test_str(self) -> None:
        """Test string representation."""
        opt = OrientedPieceType(
            piece_type=PieceType.EDGE, orientation=Orientation.DEG_180
        )
        assert str(opt) == "EDGE@180°"
