"""Tests for the PieceId data model."""

from pydantic import ValidationError
import pytest

from snap_fit.data_models.piece_id import PieceId


class TestPieceIdBasics:
    """Test basic PieceId functionality."""

    def test_create_piece_id(self) -> None:
        """Test creating a PieceId."""
        piece_id = PieceId(sheet_id="sheet_01", piece_id=0)

        assert piece_id.sheet_id == "sheet_01"
        assert piece_id.piece_id == 0

    def test_str_representation(self) -> None:
        """Test string representation."""
        piece_id = PieceId(sheet_id="sheet_01", piece_id=2)

        assert str(piece_id) == "sheet_01:2"

    def test_repr_representation(self) -> None:
        """Test repr representation."""
        piece_id = PieceId(sheet_id="sheet_01", piece_id=0)

        result = repr(piece_id)
        assert "PieceId" in result
        assert "'sheet_01'" in result
        assert "0" in result

    def test_hashable(self) -> None:
        """Test that PieceId is hashable."""
        piece_id = PieceId(sheet_id="sheet_01", piece_id=0)

        # Should not raise
        hash_value = hash(piece_id)
        assert isinstance(hash_value, int)

    def test_immutable(self) -> None:
        """Test that PieceId is immutable (frozen)."""
        piece_id = PieceId(sheet_id="sheet_01", piece_id=0)

        with pytest.raises(ValidationError):
            piece_id.sheet_id = "new_sheet"  # pyright: ignore[reportAttributeAccessIssue]
