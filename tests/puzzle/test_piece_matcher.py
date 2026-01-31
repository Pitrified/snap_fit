"""Tests for the PieceMatcher class."""

import json
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from snap_fit.config.types import EdgePos
from snap_fit.data_models.match_result import MatchResult
from snap_fit.data_models.piece_id import PieceId
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
    pid = PieceId(sheet_id="A", piece_id=1)
    return SegmentId(piece_id=pid, edge_pos=EdgePos.TOP)


@pytest.fixture
def id2() -> SegmentId:
    """Create another test SegmentId."""
    pid = PieceId(sheet_id="B", piece_id=2)
    return SegmentId(piece_id=pid, edge_pos=EdgePos.BOTTOM)


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
    pid3 = PieceId(sheet_id="C", piece_id=3)
    id3 = SegmentId(piece_id=pid3, edge_pos=EdgePos.LEFT)
    res1 = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.1)
    res2 = MatchResult(seg_id1=id2, seg_id2=id3, similarity=0.2)
    matcher.results.extend([res1, res2])

    # Matches for piece A-1
    matches_a1 = matcher.get_matches_for_piece(id1.piece_id)
    assert len(matches_a1) == 1
    assert matches_a1[0] == res1

    # Matches for piece B-2
    matches_b2 = matcher.get_matches_for_piece(id2.piece_id)
    assert len(matches_b2) == 2
    assert res1 in matches_b2
    assert res2 in matches_b2


# -----------------------------------------------------------------------------
# Persistence Tests
# -----------------------------------------------------------------------------


def test_piece_matcher_save_matches_json(
    mock_manager: MagicMock, id1: SegmentId, id2: SegmentId, tmp_path: Path
) -> None:
    """Test saving matches to JSON."""
    matcher = PieceMatcher(mock_manager)
    res1 = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.1)
    res2 = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.5)
    matcher.results.extend([res1, res2])

    output_path = tmp_path / "matches.json"
    matcher.save_matches_json(output_path)

    assert output_path.exists()
    data = json.loads(output_path.read_text())
    assert len(data) == 2
    assert data[0]["similarity"] == 0.1


def test_piece_matcher_load_matches_json(
    mock_manager: MagicMock, id1: SegmentId, id2: SegmentId, tmp_path: Path
) -> None:
    """Test loading matches from JSON."""
    # Create a JSON file with match data
    match_data = [
        {
            "seg_id1": {
                "piece_id": {"sheet_id": "A", "piece_id": 1},
                "edge_pos": "top",
            },
            "seg_id2": {
                "piece_id": {"sheet_id": "B", "piece_id": 2},
                "edge_pos": "bottom",
            },
            "similarity": 0.25,
            "similarity_manual": None,
        },
        {
            "seg_id1": {
                "piece_id": {"sheet_id": "A", "piece_id": 1},
                "edge_pos": "left",
            },
            "seg_id2": {
                "piece_id": {"sheet_id": "B", "piece_id": 2},
                "edge_pos": "right",
            },
            "similarity": 0.75,
            "similarity_manual": 0.5,
        },
    ]
    input_path = tmp_path / "matches.json"
    input_path.write_text(json.dumps(match_data))

    # Load into matcher
    matcher = PieceMatcher(mock_manager)
    matcher.load_matches_json(input_path)

    assert len(matcher.results) == 2
    assert len(matcher._lookup) == 2
    assert matcher.results[0].similarity == 0.25
    assert matcher.results[1].similarity_manual_ == 0.5


def test_piece_matcher_save_load_round_trip(
    mock_manager: MagicMock, id1: SegmentId, id2: SegmentId, tmp_path: Path
) -> None:
    """Test round-trip save and load."""
    matcher1 = PieceMatcher(mock_manager)
    res1 = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.123)
    res1.similarity_manual = 0.05
    matcher1.results.append(res1)
    matcher1._lookup[res1.pair] = res1

    output_path = tmp_path / "matches.json"
    matcher1.save_matches_json(output_path)

    matcher2 = PieceMatcher(mock_manager)
    matcher2.load_matches_json(output_path)

    assert len(matcher2.results) == 1
    loaded = matcher2.results[0]
    assert loaded.seg_id1 == id1
    assert loaded.seg_id2 == id2
    assert loaded.similarity == 0.123
    assert loaded.similarity_manual_ == 0.05


def test_piece_matcher_get_matched_pair_keys(
    mock_manager: MagicMock, id1: SegmentId, id2: SegmentId
) -> None:
    """Test get_matched_pair_keys method."""
    matcher = PieceMatcher(mock_manager)

    assert matcher.get_matched_pair_keys() == set()

    res = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.1)
    matcher.results.append(res)
    matcher._lookup[res.pair] = res

    keys = matcher.get_matched_pair_keys()
    assert len(keys) == 1
    assert frozenset({id1, id2}) in keys


def test_piece_matcher_match_incremental(mock_manager: MagicMock) -> None:
    """Test incremental matching."""
    matcher = PieceMatcher(mock_manager)

    # Setup: existing piece and match
    pid_existing = PieceId(sheet_id="A", piece_id=0)
    pid_new = PieceId(sheet_id="B", piece_id=0)

    id_existing = SegmentId(piece_id=pid_existing, edge_pos=EdgePos.TOP)
    id_new = SegmentId(piece_id=pid_new, edge_pos=EdgePos.BOTTOM)

    # Mock the manager to return segment IDs
    def get_other_pieces(seg_id: SegmentId) -> list[SegmentId]:
        if seg_id.piece_id == pid_new:
            return [SegmentId(piece_id=pid_existing, edge_pos=ep) for ep in EdgePos]
        return [SegmentId(piece_id=pid_new, edge_pos=ep) for ep in EdgePos]

    mock_manager.get_segment_ids_other_pieces.side_effect = get_other_pieces
    mock_manager.get_segment.return_value = MagicMock()

    with patch("snap_fit.puzzle.piece_matcher.SegmentMatcher") as mock_seg_matcher:
        mock_seg_matcher.return_value.compute_similarity.return_value = 0.2

        new_count = matcher.match_incremental([pid_new])

        # 4 edges on new piece × 4 edges on existing piece = 16 comparisons
        assert new_count == 16
        assert len(matcher.results) == 16


def test_piece_matcher_clear(
    mock_manager: MagicMock, id1: SegmentId, id2: SegmentId
) -> None:
    """Test clear method."""
    matcher = PieceMatcher(mock_manager)
    res = MatchResult(seg_id1=id1, seg_id2=id2, similarity=0.1)
    matcher.results.append(res)
    matcher._lookup[res.pair] = res

    assert len(matcher.results) == 1
    assert len(matcher._lookup) == 1

    matcher.clear()

    assert len(matcher.results) == 0
    assert len(matcher._lookup) == 0
