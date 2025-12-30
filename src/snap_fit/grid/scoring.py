"""Scoring functions for grid placements."""

from __future__ import annotations

from typing import TYPE_CHECKING

from snap_fit.config.types import EdgePos
from snap_fit.data_models.segment_id import SegmentId
from snap_fit.grid.orientation_utils import get_original_edge_pos

if TYPE_CHECKING:
    from snap_fit.grid.placement_state import PlacementState
    from snap_fit.grid.types import GridPos
    from snap_fit.puzzle.piece_matcher import PieceMatcher


# Map from relative position to the edge that faces the neighbor
# If neighbor is to the RIGHT, our RIGHT edge faces them
_NEIGHBOR_DIRECTION_TO_EDGE: dict[tuple[int, int], EdgePos] = {
    (-1, 0): EdgePos.TOP,  # neighbor above
    (1, 0): EdgePos.BOTTOM,  # neighbor below
    (0, -1): EdgePos.LEFT,  # neighbor to left
    (0, 1): EdgePos.RIGHT,  # neighbor to right
}


def _get_facing_edges(pos1: GridPos, pos2: GridPos) -> tuple[EdgePos, EdgePos] | None:
    """Determine which edges face each other between two adjacent positions.

    Args:
        pos1: First grid position.
        pos2: Second grid position.

    Returns:
        Tuple of (edge_from_pos1, edge_from_pos2) that face each other,
        or None if positions are not adjacent.
    """
    dro = pos2.ro - pos1.ro
    dco = pos2.co - pos1.co

    if (dro, dco) not in _NEIGHBOR_DIRECTION_TO_EDGE:
        return None

    edge1 = _NEIGHBOR_DIRECTION_TO_EDGE[(dro, dco)]
    edge2 = _NEIGHBOR_DIRECTION_TO_EDGE[(-dro, -dco)]
    return (edge1, edge2)


def score_edge(
    state: PlacementState,
    pos1: GridPos,
    pos2: GridPos,
    matcher: PieceMatcher,
) -> float | None:
    """Score the match between two adjacent pieces.

    Args:
        state: The current placement state.
        pos1: First grid position.
        pos2: Second grid position.
        matcher: Piece matcher for scoring.

    Returns:
        Match similarity score (lower is better), or None if either
        position is empty or positions are not adjacent.
    """
    # Get placements
    placement1 = state.get_placement(pos1)
    placement2 = state.get_placement(pos2)

    if placement1 is None or placement2 is None:
        return None

    # Determine facing edges
    facing = _get_facing_edges(pos1, pos2)
    if facing is None:
        return None

    piece_id1, orientation1 = placement1
    piece_id2, orientation2 = placement2
    rotated_edge1, rotated_edge2 = facing

    # Get the original edge positions (before rotation was applied)
    # If piece is rotated 90° and we want the edge that's now at TOP,
    # we need the edge that was originally at LEFT
    original_edge1 = get_original_edge_pos(rotated_edge1, orientation1)
    original_edge2 = get_original_edge_pos(rotated_edge2, orientation2)

    # Build segment IDs
    seg_id1 = SegmentId(piece_id=piece_id1, edge_pos=original_edge1)
    seg_id2 = SegmentId(piece_id=piece_id2, edge_pos=original_edge2)

    # Get score from matcher (uses cache)
    result = matcher.match_pair(seg_id1, seg_id2)
    return result.similarity


def score_grid(
    state: PlacementState,
    matcher: PieceMatcher,
) -> float:
    """Compute total score for all adjacent pairs in the grid.

    Args:
        state: The current placement state.
        matcher: Piece matcher for scoring.

    Returns:
        Sum of all edge scores. Lower is better.
        Edges with missing pieces are skipped (not penalized).
    """
    total = 0.0

    for pos1, pos2 in state.grid.neighbor_pairs():
        edge_score = score_edge(state, pos1, pos2, matcher)
        if edge_score is not None:
            total += edge_score

    return total


def score_grid_with_details(
    state: PlacementState,
    matcher: PieceMatcher,
) -> tuple[float, dict[tuple[GridPos, GridPos], float]]:
    """Compute total score with per-edge breakdown.

    Args:
        state: The current placement state.
        matcher: Piece matcher for scoring.

    Returns:
        Tuple of (total_score, edge_scores_dict).
        edge_scores_dict maps (pos1, pos2) -> score for each scored edge.
    """
    total = 0.0
    edge_scores: dict[tuple[GridPos, GridPos], float] = {}

    for pos1, pos2 in state.grid.neighbor_pairs():
        edge_score = score_edge(state, pos1, pos2, matcher)
        if edge_score is not None:
            total += edge_score
            edge_scores[(pos1, pos2)] = edge_score

    return total, edge_scores
