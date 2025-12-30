"""Tests for GridPos type."""

from pydantic import ValidationError
import pytest

from snap_fit.grid.types import GridPos


class TestGridPos:
    """Tests for GridPos model."""

    def test_creation(self) -> None:
        """Test creating GridPos."""
        pos = GridPos(ro=1, co=2)
        assert pos.ro == 1
        assert pos.co == 2

    def test_frozen(self) -> None:
        """Test that GridPos is immutable."""
        pos = GridPos(ro=0, co=0)
        with pytest.raises(ValidationError):
            pos.ro = 1  # type: ignore[misc]

    def test_hashable(self) -> None:
        """Test that GridPos can be used in sets/dicts."""
        pos1 = GridPos(ro=0, co=0)
        pos2 = GridPos(ro=0, co=0)
        pos3 = GridPos(ro=1, co=0)

        # Same values should be equal and have same hash
        assert pos1 == pos2
        assert hash(pos1) == hash(pos2)

        # Different values should be different
        assert pos1 != pos3

        # Can be used in set
        s = {pos1, pos2, pos3}
        assert len(s) == 2

        # Can be used as dict key
        d = {pos1: "a", pos3: "b"}
        assert d[pos2] == "a"  # pos2 == pos1

    def test_str(self) -> None:
        """Test string representation."""
        pos = GridPos(ro=3, co=5)
        assert str(pos) == "(3, 5)"

    def test_repr(self) -> None:
        """Test repr."""
        pos = GridPos(ro=3, co=5)
        assert repr(pos) == "GridPos(ro=3, co=5)"
