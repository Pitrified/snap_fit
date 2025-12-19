"""Tests for the MatchResult data model."""

import pytest

from snap_fit.config.types import EdgePos
from snap_fit.data_models.match_result import MatchResult
from snap_fit.data_models.segment_id import SegmentId


def test_match_result_pair_symmetry() -> None:
    """Test that the pair property is symmetric."""
    id1 = SegmentId(sheet_id="A", piece_id=1, edge_pos=EdgePos.TOP)
    id2 = SegmentId(sheet_id="B", piece_id=2, edge_pos=EdgePos.BOTTOM)

    res1 = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.5)
    res2 = MatchResult(seg_id1=id2, seg_id2=id1, similarity=0.5)

    assert res1.pair == res2.pair
    assert isinstance(res1.pair, frozenset)
    assert len(res1.pair) == 2


def test_match_result_get_other() -> None:
    """Test the get_other method."""
    id1 = SegmentId(sheet_id="A", piece_id=1, edge_pos=EdgePos.TOP)
    id2 = SegmentId(sheet_id="B", piece_id=2, edge_pos=EdgePos.BOTTOM)
    id3 = SegmentId(sheet_id="C", piece_id=3, edge_pos=EdgePos.LEFT)

    res = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.5)

    assert res.get_other(id1) == id2
    assert res.get_other(id2) == id1

    with pytest.raises(ValueError, match="not in this match result"):
        res.get_other(id3)


def test_match_result_serialization() -> None:
    """Test serialization and deserialization."""
    id1 = SegmentId(sheet_id="A", piece_id=1, edge_pos=EdgePos.TOP)
    id2 = SegmentId(sheet_id="B", piece_id=2, edge_pos=EdgePos.BOTTOM)
    res = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.5)

    data = res.model_dump()
    assert data["seg_id1"]["sheet_id"] == "A"
    assert data["similarity"] == 0.5

    res2 = MatchResult.model_validate(data)
    assert res2 == res
