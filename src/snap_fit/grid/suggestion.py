"""Suggestion engine for interactive puzzle solving."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from snap_fit.data_models.segment_id import SegmentId
from snap_fit.grid.orientation_utils import get_original_edge_pos
from snap_fit.grid.scoring import get_facing_edges

if TYPE_CHECKING:
    from snap_fit.data_models.piece_id import PieceId
    from snap_fit.grid.orientation import Orientation
    from snap_fit.grid.placement_state import PlacementState
    from snap_fit.grid.types import GridPos
    from snap_fit.puzzle.piece_matcher import PieceMatcher

# Penalty score for uncached or unscored pairs.
_NO_SCORE: float = 1e6


@dataclass
class RawCandidate:
    """Scored result for a single candidate piece at a grid slot."""

    piece_id: PieceId
    orientation: Orientation
    score: float
    neighbor_scores: dict[str, float]


def pick_next_slot(
    state: PlacementState,
    override_pos: GridPos | None = None,
) -> GridPos | None:
    """Pick the most-constrained open slot.

    Most constrained = empty slot with the most placed neighbors.
    Ties broken by top-left ordering (row first, then column).

    Args:
        state: Current placement state.
        override_pos: If provided, return this slot instead of auto-picking.

    Returns:
        GridPos to fill next, or None if the grid is complete.

    Raises:
        ValueError: If override_pos is already occupied.
    """
    if override_pos is not None:
        if state.get_placement(override_pos) is not None:
            msg = f"Slot {override_pos} is already occupied"
            raise ValueError(msg)
        return override_pos

    empty = state.empty_positions()
    if not empty:
        return None

    def _key(pos: GridPos) -> tuple[int, int, int]:
        neighbor_count = sum(
            1 for n in state.grid.neighbors(pos) if state.get_placement(n) is not None
        )
        return (-neighbor_count, pos.ro, pos.co)

    return min(empty, key=_key)


def score_candidates(
    state: PlacementState,
    target_pos: GridPos,
    matcher: PieceMatcher,
    available_pieces: list[PieceId],
    rejected: set[PieceId],
    top_k: int = 5,
) -> list[RawCandidate]:
    """Score and rank candidate pieces for a target slot.

    For each candidate:

    1. Determine the required orientation from the GridModel slot type.
    2. Score against all placed neighbors using cached similarity scores.
    3. Sum neighbor scores as the total candidate score.

    Pieces with no placed neighbors receive score ``1e6``.
    Uncached segment pairs are penalized with score ``1e6``.

    Args:
        state: Current placement state.
        target_pos: The slot to fill.
        matcher: PieceMatcher with precomputed cached scores.
        available_pieces: Unplaced pieces of the appropriate type.
        rejected: Piece IDs already rejected for this slot (excluded).
        top_k: Number of top candidates to return.

    Returns:
        Ranked list of RawCandidate (lowest score first), at most ``top_k``.
    """
    orientation = state.grid.get_slot_type(target_pos).orientation
    candidates: list[RawCandidate] = []

    for piece_id in available_pieces:
        if piece_id in rejected:
            continue

        neighbor_scores: dict[str, float] = {}
        total_score = 0.0
        scored_count = 0

        for neighbor_pos in state.grid.neighbors(target_pos):
            placed = state.get_placement(neighbor_pos)
            if placed is None:
                continue

            facing = get_facing_edges(target_pos, neighbor_pos)
            if facing is None:
                continue

            neighbor_pid, neighbor_orient = placed
            original_new = get_original_edge_pos(facing[0], orientation)
            original_nbr = get_original_edge_pos(facing[1], neighbor_orient)

            seg_new = SegmentId(piece_id=piece_id, edge_pos=original_new)
            seg_nbr = SegmentId(piece_id=neighbor_pid, edge_pos=original_nbr)

            cached = matcher.get_cached_score(seg_new, seg_nbr)
            edge_score = cached if cached is not None else _NO_SCORE
            pos_key = f"{neighbor_pos.ro},{neighbor_pos.co}"
            neighbor_scores[pos_key] = edge_score
            total_score += edge_score
            scored_count += 1

        if scored_count == 0:
            total_score = _NO_SCORE

        candidates.append(
            RawCandidate(
                piece_id=piece_id,
                orientation=orientation,
                score=total_score,
                neighbor_scores=neighbor_scores,
            )
        )

    candidates.sort(key=lambda c: c.score)
    return candidates[:top_k]


def get_scored_segment_pairs(
    state: PlacementState,
    target_pos: GridPos,
    piece_id: PieceId,
    orientation: Orientation,
) -> list[tuple[SegmentId, SegmentId]]:
    """Get the segment pairs scored for a hypothetical placement.

    Returns the ``(new_seg, neighbor_seg)`` pairs that would be evaluated if
    ``piece_id`` were placed at ``target_pos`` with ``orientation``.
    Only already-placed neighbors are considered.

    Args:
        state: Current placement state.
        target_pos: The slot being filled.
        piece_id: The piece being scored.
        orientation: The orientation the piece would be placed at.

    Returns:
        List of ``(new_segment_id, neighbor_segment_id)`` pairs.
    """
    pairs: list[tuple[SegmentId, SegmentId]] = []
    for neighbor_pos in state.grid.neighbors(target_pos):
        placed = state.get_placement(neighbor_pos)
        if placed is None:
            continue
        facing = get_facing_edges(target_pos, neighbor_pos)
        if facing is None:
            continue

        neighbor_pid, neighbor_orient = placed
        original_new = get_original_edge_pos(facing[0], orientation)
        original_nbr = get_original_edge_pos(facing[1], neighbor_orient)

        seg_new = SegmentId(piece_id=piece_id, edge_pos=original_new)
        seg_nbr = SegmentId(piece_id=neighbor_pid, edge_pos=original_nbr)
        pairs.append((seg_new, seg_nbr))

    return pairs
