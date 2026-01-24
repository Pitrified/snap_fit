"""Tests for the MatchResult data model."""

import pytest

from snap_fit.config.types import EdgePos
from snap_fit.data_models.match_result import MatchResult
from snap_fit.data_models.piece_id import PieceId
from snap_fit.data_models.segment_id import SegmentId


@pytest.fixture
def pid1() -> PieceId:
    """Fixture for piece ID 1."""
    return PieceId(sheet_id="A", piece_id=1)


@pytest.fixture
def pid2() -> PieceId:
    """Fixture for piece ID 2."""
    return PieceId(sheet_id="B", piece_id=2)


@pytest.fixture
def id1(pid1: PieceId) -> SegmentId:
    """Fixture for segment ID 1."""
    return SegmentId(piece_id=pid1, edge_pos=EdgePos.TOP)


@pytest.fixture
def id2(pid2: PieceId) -> SegmentId:
    """Fixture for segment ID 2."""
    return SegmentId(piece_id=pid2, edge_pos=EdgePos.BOTTOM)


@pytest.fixture
def match_result(id1: SegmentId, id2: SegmentId) -> MatchResult:
    """Fixture for a basic match result."""
    return MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.5)


def test_match_result_pair_symmetry(id1: SegmentId, id2: SegmentId) -> None:
    """Test that the pair property is symmetric."""
    res1 = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.5)
    res2 = MatchResult(seg_id1=id2, seg_id2=id1, similarity=0.5)

    assert res1.pair == res2.pair
    assert isinstance(res1.pair, frozenset)
    assert len(res1.pair) == 2


def test_match_result_get_other(
    match_result: MatchResult, id1: SegmentId, id2: SegmentId
) -> None:
    """Test the get_other method."""
    pid3 = PieceId(sheet_id="C", piece_id=3)
    id3 = SegmentId(piece_id=pid3, edge_pos=EdgePos.LEFT)

    assert match_result.get_other(id1) == id2
    assert match_result.get_other(id2) == id1

    with pytest.raises(ValueError, match="not in this match result"):
        match_result.get_other(id3)


def test_match_result_serialization(match_result: MatchResult) -> None:
    """Test serialization and deserialization."""
    data = match_result.model_dump()
    assert data["seg_id1"]["piece_id"]["sheet_id"] == "A"
    assert data["similarity"] == 0.5

    res2 = MatchResult.model_validate(data)
    assert res2 == match_result


def test_similarity_manual_default(match_result: MatchResult) -> None:
    """Test that similarity_manual defaults to similarity when not set."""
    assert match_result.similarity_manual == 0.5


def test_similarity_manual_set(match_result: MatchResult) -> None:
    """Test setting similarity_manual to a new value."""
    match_result.similarity_manual = 0.8
    assert match_result.similarity_manual == 0.8


def test_similarity_manual_init(id1: SegmentId, id2: SegmentId) -> None:
    """Test initializing MatchResult with similarity_manual set."""
    res = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.5, similarity_manual=0.7)
    assert res.similarity_manual == 0.7


def test_similarity_manual_reset(match_result: MatchResult) -> None:
    """Test resetting similarity_manual to None falls back to similarity."""
    match_result.similarity_manual = 0.8
    assert match_result.similarity_manual == 0.8
    match_result.similarity_manual = None
    assert match_result.similarity_manual == 0.5
