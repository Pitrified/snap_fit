"""Tests for the PieceMatcher class."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from snap_fit.config.types import EdgePos
from snap_fit.data_models.match_result import MatchResult
from snap_fit.data_models.segment_id import SegmentId
from snap_fit.puzzle.piece_matcher import PieceMatcher
from snap_fit.puzzle.sheet_manager import SheetManager


@pytest.fixture
def mock_manager() -> MagicMock:
    """Create a mock SheetManager."""
    manager = MagicMock(spec=SheetManager)
    return manager


@pytest.fixture
def id1() -> SegmentId:
    """Create a test SegmentId."""
    return SegmentId(sheet_id="A", piece_id=1, edge_pos=EdgePos.TOP)


@pytest.fixture
def id2() -> SegmentId:
    """Create another test SegmentId."""
    return SegmentId(sheet_id="B", piece_id=2, edge_pos=EdgePos.BOTTOM)


def test_piece_matcher_init(mock_manager: MagicMock) -> None:
    """Test initialization of PieceMatcher."""
    matcher = PieceMatcher(mock_manager)
    assert matcher.manager == mock_manager
    assert matcher.results == []
    assert matcher._lookup == {}


def test_piece_matcher_match_pair_symmetry(
    mock_manager: MagicMock, id1: SegmentId, id2: SegmentId
) -> None:
    """Test that match_pair is symmetric and cached."""
    matcher = PieceMatcher(mock_manager)
    mock_manager.get_segment.return_value = MagicMock()

    with patch("snap_fit.puzzle.piece_matcher.SegmentMatcher") as mock_seg_matcher:
        mock_seg_matcher.return_value.compute_similarity.return_value = 0.1

        res1 = matcher.match_pair(id1, id2)
        res2 = matcher.match_pair(id2, id1)

        # Should return the same object
        assert res1 is res2
        assert len(matcher.results) == 1
        assert mock_seg_matcher.call_count == 1


def test_piece_matcher_match_pair_missing_segments(
    mock_manager: MagicMock, id1: SegmentId, id2: SegmentId
) -> None:
    """Test match_pair when segments are missing."""
    matcher = PieceMatcher(mock_manager)
    mock_manager.get_segment.return_value = None

    res = matcher.match_pair(id1, id2)
    assert res.similarity == 1e6
    assert len(matcher.results) == 1


def test_piece_matcher_match_all(
    mock_manager: MagicMock, id1: SegmentId, id2: SegmentId
) -> None:
    """Test match_all method."""
    matcher = PieceMatcher(mock_manager)
    mock_manager.get_segment_ids_all.return_value = [id1, id2]
    mock_manager.get_segment_ids_other_pieces.side_effect = (
        lambda x: [id2] if x == id1 else [id1]
    )
    mock_manager.get_segment.return_value = MagicMock()

    with patch("snap_fit.puzzle.piece_matcher.SegmentMatcher") as mock_seg_matcher:
        mock_seg_matcher.return_value.compute_similarity.return_value = 0.1
        matcher.match_all()

        assert len(matcher.results) == 1
        assert len(matcher._lookup) == 1


def test_piece_matcher_get_top_matches(
    mock_manager: MagicMock, id1: SegmentId, id2: SegmentId
) -> None:
    """Test get_top_matches method."""
    matcher = PieceMatcher(mock_manager)
    res1 = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.1)
    res2 = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.5)
    matcher.results.extend([res1, res2])

    assert matcher.get_top_matches(1) == [res1]
    assert matcher.get_top_matches(5) == [res1, res2]


def test_piece_matcher_get_matches_for_piece(
    mock_manager: MagicMock, id1: SegmentId, id2: SegmentId
) -> None:
    """Test get_matches_for_piece method."""
    matcher = PieceMatcher(mock_manager)
    id3 = SegmentId(sheet_id="C", piece_id=3, edge_pos=EdgePos.LEFT)
    res1 = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.1)
    res2 = MatchResult(seg_id1=id2, seg_id2=id3, similarity=0.2)
    matcher.results.extend([res1, res2])

    # Matches for piece A-1
    matches_a1 = matcher.get_matches_for_piece("A", 1)
    assert len(matches_a1) == 1
    assert matches_a1[0] == res1

    # Matches for piece B-2
    matches_b2 = matcher.get_matches_for_piece("B", 2)
    assert len(matches_b2) == 2
    assert res1 in matches_b2
    assert res2 in matches_b2
