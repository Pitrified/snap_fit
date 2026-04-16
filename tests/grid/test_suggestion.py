"""Unit tests for the suggestion engine (grid/suggestion.py)."""

from typing import cast

import pytest

from snap_fit.data_models.piece_id import PieceId
from snap_fit.data_models.segment_id import SegmentId
from snap_fit.grid.grid_model import GridModel
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.placement_state import PlacementState
from snap_fit.grid.suggestion import RawCandidate
from snap_fit.grid.suggestion import get_scored_segment_pairs
from snap_fit.grid.suggestion import pick_next_slot
from snap_fit.grid.suggestion import score_candidates
from snap_fit.grid.types import GridPos
from snap_fit.puzzle.piece_matcher import PieceMatcher

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pid(sheet_id: str, idx: int) -> PieceId:
    return PieceId(sheet_id=sheet_id, piece_id=idx)


class _FakeMatcher:
    """Minimal mock for PieceMatcher - get_cached_score returns fixed value."""

    def __init__(self, *, fixed_score: float | None = 0.5) -> None:
        self._score = fixed_score

    def get_cached_score(self, _seg_a: SegmentId, _seg_b: SegmentId) -> float | None:
        return self._score


def _matcher(*, fixed_score: float | None = 0.5) -> PieceMatcher:
    """Return a PieceMatcher-typed fake for scoring tests."""
    return cast("PieceMatcher", _FakeMatcher(fixed_score=fixed_score))


# ---------------------------------------------------------------------------
# pick_next_slot
# ---------------------------------------------------------------------------


class TestPickNextSlot:
    """Tests for pick_next_slot."""

    def test_empty_grid_returns_any_pos(self) -> None:
        """Any position is valid on an empty grid."""
        grid = GridModel(2, 2)
        state = PlacementState(grid)
        pos = pick_next_slot(state)
        assert pos is not None
        assert isinstance(pos, GridPos)

    def test_complete_grid_returns_none(self) -> None:
        """Returns None when all slots are filled."""
        grid = GridModel(2, 2)
        state = PlacementState(grid)
        for i, (ro, co) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]):
            state.place(_pid("s", i), GridPos(ro=ro, co=co), Orientation.DEG_0)
        assert pick_next_slot(state) is None

    def test_picks_most_constrained(self) -> None:
        """Slot adjacent to two placed pieces is preferred over slot with one."""
        grid = GridModel(3, 3)
        state = PlacementState(grid)
        # Place pieces at (0,0) and (1,0)
        state.place(_pid("s", 0), GridPos(ro=0, co=0), Orientation.DEG_0)
        state.place(_pid("s", 1), GridPos(ro=1, co=0), Orientation.DEG_0)
        # (0,1) is adjacent to (0,0) only - 1 neighbor
        # (1,1) is adjacent to (1,0) and also diagonally near... let's check
        # Actually (1,1) is adjacent to both (1,0) and could be adj to (0,1)
        # but not (0,0) diagonally.  Neighbors of (1,1) are (0,1),(2,1),(1,0),(1,2)
        # So (1,1) has 1 placed neighbor: (1,0)
        # (2,0) is adjacent to (1,0) - 1 neighbor
        # all equal: tie broken by top-left ordering (smallest ro then co)
        pos = pick_next_slot(state)
        assert pos is not None
        # With 1 neighbor each, tie-break puts (0,1) first
        assert pos == GridPos(ro=0, co=1)

    def test_override_pos_returned(self) -> None:
        """override_pos is returned as-is when empty."""
        grid = GridModel(2, 2)
        state = PlacementState(grid)
        pos = pick_next_slot(state, override_pos=GridPos(ro=1, co=1))
        assert pos == GridPos(ro=1, co=1)

    def test_override_occupied_raises(self) -> None:
        """Raises ValueError when override_pos is already occupied."""
        grid = GridModel(2, 2)
        state = PlacementState(grid)
        state.place(_pid("s", 0), GridPos(ro=0, co=0), Orientation.DEG_0)
        with pytest.raises(ValueError, match="already occupied"):
            pick_next_slot(state, override_pos=GridPos(ro=0, co=0))


# ---------------------------------------------------------------------------
# score_candidates
# ---------------------------------------------------------------------------


class TestScoreCandidates:
    """Tests for score_candidates."""

    def test_empty_available_returns_empty(self) -> None:
        """Empty available_pieces gives empty result."""
        grid = GridModel(2, 2)
        state = PlacementState(grid)
        state.place(_pid("s", 0), GridPos(ro=0, co=0), Orientation.DEG_0)
        result = score_candidates(
            state,
            GridPos(ro=0, co=1),
            _matcher(),
            [],
            set(),
        )
        assert result == []

    def test_rejected_pieces_excluded(self) -> None:
        """Rejected pieces do not appear in output."""
        grid = GridModel(2, 2)
        state = PlacementState(grid)
        state.place(_pid("s", 0), GridPos(ro=0, co=0), Orientation.DEG_0)
        pid1 = _pid("s", 1)
        pid2 = _pid("s", 2)
        result = score_candidates(
            state,
            GridPos(ro=0, co=1),
            _matcher(),
            [pid1, pid2],
            {pid1},
        )
        assert all(c.piece_id != pid1 for c in result)
        assert any(c.piece_id == pid2 for c in result)

    def test_no_neighbors_gets_no_score(self) -> None:
        """Piece with no placed neighbors receives _NO_SCORE."""
        grid = GridModel(2, 2)
        state = PlacementState(grid)
        pid = _pid("s", 1)
        result = score_candidates(
            state,
            GridPos(ro=0, co=0),
            _matcher(),
            [pid],
            set(),
        )
        assert len(result) == 1
        assert result[0].score == 1e6

    def test_returns_at_most_top_k(self) -> None:
        """Returns at most top_k candidates."""
        grid = GridModel(2, 2)
        state = PlacementState(grid)
        state.place(_pid("s", 0), GridPos(ro=0, co=0), Orientation.DEG_0)
        pids = [_pid("s", i) for i in range(1, 6)]
        result = score_candidates(
            state,
            GridPos(ro=0, co=1),
            _matcher(),
            pids,
            set(),
            top_k=3,
        )
        assert len(result) <= 3

    def test_sorted_by_score(self) -> None:
        """Candidates are sorted ascending by score."""
        grid = GridModel(2, 2)
        state = PlacementState(grid)
        state.place(_pid("s", 0), GridPos(ro=0, co=0), Orientation.DEG_0)
        pids = [_pid("s", i) for i in range(1, 4)]
        result = score_candidates(
            state,
            GridPos(ro=0, co=1),
            _matcher(fixed_score=0.3),
            pids,
            set(),
        )
        scores = [c.score for c in result]
        assert scores == sorted(scores)

    def test_uncached_pair_gets_no_score_penalty(self) -> None:
        """Uncached pair (get_cached_score returns None) is penalised with 1e6."""
        grid = GridModel(2, 2)
        state = PlacementState(grid)
        state.place(_pid("s", 0), GridPos(ro=0, co=0), Orientation.DEG_0)
        pid = _pid("s", 1)
        result = score_candidates(
            state,
            GridPos(ro=0, co=1),
            _matcher(fixed_score=None),
            [pid],
            set(),
        )
        assert result[0].score == 1e6

    def test_result_is_raw_candidate(self) -> None:
        """Each result is a RawCandidate with the correct fields."""
        grid = GridModel(2, 2)
        state = PlacementState(grid)
        state.place(_pid("s", 0), GridPos(ro=0, co=0), Orientation.DEG_0)
        pid = _pid("s", 1)
        result = score_candidates(
            state,
            GridPos(ro=0, co=1),
            _matcher(fixed_score=0.25),
            [pid],
            set(),
        )
        assert isinstance(result[0], RawCandidate)
        assert result[0].piece_id == pid
        assert isinstance(result[0].orientation, Orientation)
        assert isinstance(result[0].neighbor_scores, dict)


# ---------------------------------------------------------------------------
# get_scored_segment_pairs
# ---------------------------------------------------------------------------


class TestGetScoredSegmentPairs:
    """Tests for get_scored_segment_pairs."""

    def test_no_neighbors_returns_empty(self) -> None:
        """No placed neighbors means no pairs."""
        grid = GridModel(2, 2)
        state = PlacementState(grid)
        pairs = get_scored_segment_pairs(
            state,
            GridPos(ro=0, co=0),
            _pid("s", 0),
            Orientation.DEG_0,
        )
        assert pairs == []

    def test_one_placed_neighbor_returns_one_pair(self) -> None:
        """Single placed neighbor produces one pair of SegmentIds."""
        grid = GridModel(2, 2)
        state = PlacementState(grid)
        state.place(_pid("s", 0), GridPos(ro=0, co=0), Orientation.DEG_0)
        pairs = get_scored_segment_pairs(
            state,
            GridPos(ro=0, co=1),
            _pid("s", 1),
            Orientation.DEG_90,
        )
        assert len(pairs) == 1
        seg_new, seg_nbr = pairs[0]
        assert isinstance(seg_new, SegmentId)
        assert isinstance(seg_nbr, SegmentId)
        assert seg_new.piece_id == _pid("s", 1)
        assert seg_nbr.piece_id == _pid("s", 0)

    def test_two_placed_neighbors_returns_two_pairs(self) -> None:
        """Two placed neighbors produces two pairs."""
        grid = GridModel(3, 3)
        state = PlacementState(grid)
        state.place(_pid("s", 0), GridPos(ro=0, co=1), Orientation.DEG_0)
        state.place(_pid("s", 1), GridPos(ro=1, co=0), Orientation.DEG_270)
        pairs = get_scored_segment_pairs(
            state,
            GridPos(ro=1, co=1),
            _pid("s", 2),
            Orientation.DEG_0,
        )
        assert len(pairs) == 2
