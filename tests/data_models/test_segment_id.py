"""Tests for the SegmentId data model."""

from pydantic import ValidationError
import pytest

from snap_fit.config.types import EdgePos
from snap_fit.data_models.piece_id import PieceId
from snap_fit.data_models.segment_id import SegmentId


class TestSegmentIdBasics:
    """Test basic SegmentId functionality."""

    def test_create_segment_id(self) -> None:
        """Test creating a SegmentId."""
        pid = PieceId(sheet_id="sheet_01", piece_id=0)
        seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)

        assert seg_id.sheet_id == "sheet_01"
        assert seg_id.piece_id_int == 0
        assert seg_id.piece_id == pid
        assert seg_id.edge_pos == EdgePos.LEFT

    def test_str_representation(self) -> None:
        """Test string representation."""
        pid = PieceId(sheet_id="sheet_01", piece_id=2)
        seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.BOTTOM)

        assert str(seg_id) == "sheet_01:2:bottom"

    def test_repr_representation(self) -> None:
        """Test repr representation."""
        pid = PieceId(sheet_id="sheet_01", piece_id=0)
        seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)

        result = repr(seg_id)
        assert "SegmentId" in result
        assert "PieceId" in result
        assert "'sheet_01'" in result
        assert "0" in result
        assert "LEFT" in result

    def test_as_tuple_property(self) -> None:
        """Test as_tuple property."""
        pid = PieceId(sheet_id="sheet_01", piece_id=3)
        seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.RIGHT)

        expected = ("sheet_01", 3, EdgePos.RIGHT)
        assert seg_id.as_tuple == expected

    def test_as_tuple_unpacking(self) -> None:
        """Test unpacking via as_tuple."""
        pid = PieceId(sheet_id="sheet_01", piece_id=1)
        seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.TOP)

        sheet_id, piece_id, edge_pos = seg_id.as_tuple
        assert sheet_id == "sheet_01"
        assert piece_id == 1
        assert edge_pos == EdgePos.TOP


class TestSegmentIdHashability:
    """Test SegmentId hashability (frozen model)."""

    def test_hashable(self) -> None:
        """Test that SegmentId is hashable."""
        pid = PieceId(sheet_id="sheet_01", piece_id=0)
        seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)

        # Should not raise
        hash_value = hash(seg_id)
        assert isinstance(hash_value, int)

    def test_usable_in_set(self) -> None:
        """Test that SegmentId can be used in a set."""
        pid1 = PieceId(sheet_id="sheet_01", piece_id=0)
        pid2 = PieceId(sheet_id="sheet_01", piece_id=1)
        seg1 = SegmentId(piece_id=pid1, edge_pos=EdgePos.LEFT)
        seg2 = SegmentId(piece_id=pid1, edge_pos=EdgePos.RIGHT)
        seg3 = SegmentId(piece_id=pid2, edge_pos=EdgePos.LEFT)

        seg_set = {seg1, seg2, seg3}
        assert len(seg_set) == 3

    def test_usable_as_dict_key(self) -> None:
        """Test that SegmentId can be used as a dict key."""
        pid = PieceId(sheet_id="sheet_01", piece_id=0)
        seg1 = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)
        seg2 = SegmentId(piece_id=pid, edge_pos=EdgePos.RIGHT)

        seg_dict = {seg1: "data_1", seg2: "data_2"}

        assert seg_dict[seg1] == "data_1"
        assert seg_dict[seg2] == "data_2"

    def test_immutable(self) -> None:
        """Test that SegmentId is immutable (frozen)."""
        pid = PieceId(sheet_id="sheet_01", piece_id=0)
        seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)

        with pytest.raises(ValidationError):
            seg_id.piece_id = PieceId(sheet_id="new", piece_id=1)  # pyright: ignore[reportAttributeAccessIssue]


class TestSegmentIdEquality:
    """Test SegmentId equality comparison."""

    def test_equal_segment_ids(self) -> None:
        """Test that identical SegmentIds are equal."""
        pid1 = PieceId(sheet_id="sheet_01", piece_id=0)
        pid2 = PieceId(sheet_id="sheet_01", piece_id=0)
        seg1 = SegmentId(piece_id=pid1, edge_pos=EdgePos.LEFT)
        seg2 = SegmentId(piece_id=pid2, edge_pos=EdgePos.LEFT)

        assert seg1 == seg2
        assert hash(seg1) == hash(seg2)

    def test_different_sheet_id(self) -> None:
        """Test that different sheet_ids are not equal."""
        pid1 = PieceId(sheet_id="sheet_01", piece_id=0)
        pid2 = PieceId(sheet_id="sheet_02", piece_id=0)
        seg1 = SegmentId(piece_id=pid1, edge_pos=EdgePos.LEFT)
        seg2 = SegmentId(piece_id=pid2, edge_pos=EdgePos.LEFT)

        assert seg1 != seg2

    def test_different_piece_id(self) -> None:
        """Test that different piece_ids are not equal."""
        pid1 = PieceId(sheet_id="sheet_01", piece_id=0)
        pid2 = PieceId(sheet_id="sheet_01", piece_id=1)
        seg1 = SegmentId(piece_id=pid1, edge_pos=EdgePos.LEFT)
        seg2 = SegmentId(piece_id=pid2, edge_pos=EdgePos.LEFT)

        assert seg1 != seg2

    def test_different_edge_pos(self) -> None:
        """Test that different edge_pos are not equal."""
        pid = PieceId(sheet_id="sheet_01", piece_id=0)
        seg1 = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)
        seg2 = SegmentId(piece_id=pid, edge_pos=EdgePos.RIGHT)

        assert seg1 != seg2

    def test_membership_in_set(self) -> None:
        """Test membership check in a set."""
        pid = PieceId(sheet_id="sheet_01", piece_id=0)
        seg1 = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)
        seg2 = SegmentId(piece_id=pid, edge_pos=EdgePos.RIGHT)

        seg_set = {seg1, seg2}

        # Same values as seg1
        pid_copy = PieceId(sheet_id="sheet_01", piece_id=0)
        seg1_copy = SegmentId(piece_id=pid_copy, edge_pos=EdgePos.LEFT)
        assert seg1_copy in seg_set

        # Different values
        pid3 = PieceId(sheet_id="sheet_01", piece_id=1)
        seg3 = SegmentId(piece_id=pid3, edge_pos=EdgePos.LEFT)
        assert seg3 not in seg_set


class TestSegmentIdSerialization:
    """Test SegmentId serialization/deserialization."""

    def test_model_dump(self) -> None:
        """Test model_dump() returns a dict."""
        pid = PieceId(sheet_id="sheet_01", piece_id=0)
        seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)

        dumped = seg_id.model_dump()

        assert isinstance(dumped, dict)
        assert dumped["piece_id"]["sheet_id"] == "sheet_01"
        assert dumped["piece_id"]["piece_id"] == 0
        assert dumped["edge_pos"] == EdgePos.LEFT

    def test_model_dump_json(self) -> None:
        """Test model_dump_json() returns valid JSON string."""
        pid = PieceId(sheet_id="sheet_01", piece_id=0)
        seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)

        json_str = seg_id.model_dump_json()

        assert isinstance(json_str, str)
        assert "sheet_01" in json_str
        assert "0" in json_str
        assert "left" in json_str

    def test_json_roundtrip(self) -> None:
        """Test serialization/deserialization roundtrip."""
        pid = PieceId(sheet_id="sheet_01", piece_id=5)
        original = SegmentId(piece_id=pid, edge_pos=EdgePos.TOP)

        json_str = original.model_dump_json()
        restored = SegmentId.model_validate_json(json_str)
        assert restored == original

    def test_dict_roundtrip(self) -> None:
        """Test dict serialization/deserialization roundtrip."""
        pid = PieceId(sheet_id="sheet_01", piece_id=2)
        original = SegmentId(piece_id=pid, edge_pos=EdgePos.BOTTOM)

        dumped = original.model_dump()
        restored = SegmentId.model_validate(dumped)
        assert restored == original

        assert restored == original
        assert restored.sheet_id == original.sheet_id
        assert restored.piece_id == original.piece_id
        assert restored.edge_pos == original.edge_pos
