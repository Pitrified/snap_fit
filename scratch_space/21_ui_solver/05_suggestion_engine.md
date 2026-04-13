# 05 - Suggestion Engine

> **Status:** not started
> **Depends on:** 04 (session CRUD), 06 (run matching)
> **Main plan ref:** Phase 3

---

## Objective

Implement the suggestion engine that proposes candidate pieces for the next open
slot in a solve session. This is the core intelligence of the interactive solver:
it picks the best slot to fill, scores candidates against placed neighbors, and
returns a ranked list for the user to accept or reject.

---

## Current state

- `NaiveLinearSolver` already implements greedy row-by-row solving with scoring.
  It uses `scoring.score_edge()` to evaluate each candidate. We reuse the scoring
  primitives but not the solver's rigid ordering.
- `scoring.score_edge(state, pos1, pos2, matcher)` returns a float similarity
  (lower is better) or None if either position is empty / not adjacent.
- `scoring.score_grid(state, matcher)` sums all edge scores.
- `PieceMatcher.get_matches_for_piece(piece_id)` returns `list[MatchResult]`
  sorted by similarity.
- `PieceMatcher.get_cached_score(seg_a, seg_b)` returns cached similarity or None.
- `GridModel.get_slot_type(pos)` returns `OrientedPieceType` (piece_type + orientation).
- `PlacementState.empty_positions()` returns unoccupied positions.
- `get_original_edge_pos(rotated_edge, orientation)` maps rotated edges back to
  original edge positions.
- `partition_pieces_by_type(manager)` splits pieces into corners, edges, inners.

---

## Plan

### Step 1: Slot selection - most constrained first

```python
def pick_next_slot(
    state: PlacementState,
    override_pos: GridPos | None = None,
) -> GridPos | None:
    """Pick the most-constrained open slot.

    Most constrained = empty slot with the most placed neighbors.
    Ties broken by top-left ordering (row first, then column).

    Args:
        state: Current placement state.
        override_pos: If provided, use this slot instead of auto-picking.

    Returns:
        GridPos to fill next, or None if grid is complete.
    """
    if override_pos is not None:
        if state.get_placement(override_pos) is not None:
            raise ValueError(f"Slot {override_pos} is already occupied")
        return override_pos

    empty = state.empty_positions()
    if not empty:
        return None

    def constraint_key(pos: GridPos) -> tuple[int, int, int]:
        neighbor_count = sum(
            1 for n in state.grid.neighbors(pos)
            if state.get_placement(n) is not None
        )
        return (-neighbor_count, pos.ro, pos.co)  # most neighbors first

    return min(empty, key=constraint_key)
```

### Step 2: Candidate scoring

For a given open slot, score all unplaced pieces of the correct type:

```python
def score_candidates(
    state: PlacementState,
    target_pos: GridPos,
    matcher: PieceMatcher,
    available_pieces: list[PieceId],
    rejected: set[PieceId],
    top_k: int = 5,
) -> list[SuggestionCandidate]:
    """Score and rank candidate pieces for a target slot.

    For each candidate:
    1. Determine the required orientation from GridModel slot type
    2. Temporarily place the candidate
    3. Score against all placed neighbors using score_edge()
    4. Sum neighbor scores as the total candidate score

    Args:
        state: Current placement state.
        target_pos: The slot to fill.
        matcher: PieceMatcher with precomputed match scores.
        available_pieces: Unplaced pieces of the correct type.
        rejected: Pieces rejected for this slot (excluded).
        top_k: Number of candidates to return.

    Returns:
        Ranked list of SuggestionCandidate (lowest score = best).
    """
    slot_type = state.grid.get_slot_type(target_pos)
    candidates = []

    for piece_id in available_pieces:
        if piece_id in rejected:
            continue

        # Determine orientation for this piece at this slot
        # The slot_type.orientation tells us what orientation the slot expects
        orientation = slot_type.orientation

        # Temporarily place
        temp_state = state.clone()
        temp_state.place(piece_id, target_pos, orientation)

        # Score against neighbors
        neighbor_scores = {}
        total_score = 0.0
        scored_count = 0

        for neighbor_pos in state.grid.neighbors(target_pos):
            edge_score = score_edge(temp_state, target_pos, neighbor_pos, matcher)
            if edge_score is not None:
                pos_key = f"{neighbor_pos.ro},{neighbor_pos.co}"
                neighbor_scores[pos_key] = edge_score
                total_score += edge_score
                scored_count += 1

        if scored_count == 0:
            total_score = 1e6  # no neighbors to score against

        candidates.append(SuggestionCandidate(
            piece_id=str(piece_id),
            piece_label=...,  # look up from PieceRecord
            orientation=orientation.value,
            score=total_score,
            neighbor_scores=neighbor_scores,
        ))

    candidates.sort(key=lambda c: c.score)
    return candidates[:top_k]
```

**Design note on orientation:** The naive approach uses the slot's expected
orientation. But pieces may have been misclassified (wrong piece type detected).
A more robust approach tries all 4 orientations and picks the best. Start with
the simple approach; add "try all orientations" as a flag later.

### Step 3: `suggest_next()` in InteractiveService

```python
def suggest_next(
    self,
    dataset_tag: str,
    session_id: str,
    override_pos: str | None = None,
    top_k: int = 5,
) -> SuggestionBundle:
    """Generate suggestions for the next slot.

    1. Load session from SQLite
    2. Reconstruct PlacementState from session.placement
    3. Pick next slot (most-constrained or override)
    4. Load PieceMatcher (lazy, cached per dataset)
    5. Partition unplaced pieces by type
    6. Score candidates for the target slot
    7. Return SuggestionBundle
    """
```

This requires loading a `PieceMatcher` with match data. The service needs to:
- Load match data from `DatasetStore.load_matches()` into a `PieceMatcher`
- Cache the matcher per dataset tag (expensive to rebuild)
- Also need a `SheetManager` to get piece objects for type classification

Consider a `_load_matcher(tag)` method with `@lru_cache` or an instance-level
dict cache.

### Step 4: Accept endpoint

```python
@router.post("/sessions/{session_id}/accept", summary="Accept suggestion")
async def accept_suggestion(
    session_id: str,
    dataset_tag: str,
    service: ...,
) -> SolveSessionResponse:
    """Accept the current top suggestion.

    - Places the piece from pending_suggestion.candidates[current_index]
    - Updates similarity_manual to 0 (confirmed match) for all scored edges
    - Clears pending_suggestion
    - Persists to SQLite
    """
```

### Step 5: Reject endpoint

```python
@router.post("/sessions/{session_id}/reject", summary="Reject suggestion")
async def reject_suggestion(
    session_id: str,
    dataset_tag: str,
    service: ...,
) -> SuggestionBundle:
    """Reject the current candidate.

    - Adds piece_id to session.rejected[slot]
    - Updates similarity_manual to 1e6 (confirmed mismatch) for scored edges
    - Advances current_index in the suggestion bundle
    - If all candidates exhausted, picks next slot and starts fresh
    - Returns updated SuggestionBundle
    """
```

### Step 6: Manual similarity updates

When the user accepts a match, update `MatchResult.similarity_manual_` to 0 for
each scored edge pair. When they reject, set it to 1e6. This persists the user's
judgment for future sessions / re-runs.

```python
def _update_manual_scores(
    self,
    store: DatasetStore,
    neighbor_scores: dict[str, float],
    piece_id: PieceId,
    target_pos: GridPos,
    state: PlacementState,
    value: float,  # 0 for accept, 1e6 for reject
) -> None:
    """Update similarity_manual for the scored edge pairs."""
    # For each neighbor that was scored, find the segment pair
    # and update its manual score in the matches table
    ...
```

This requires `DatasetStore` to support updating individual match records.
Add `update_match_manual_score(seg_id1, seg_id2, similarity_manual)` to
`DatasetStore`.

---

## Implementation note: PieceMatcher loading

The suggestion engine needs a live `PieceMatcher` loaded with match data.
Current `PieceMatcher` can load from SQLite via `load_matches_db()`. But it also
needs a `SheetManager` reference (for `match_pair()` calls that access segment
data).

For the suggestion engine we do NOT need to call `match_pair()` - we only need
cached scores. So we can:
1. Create a `PieceMatcher(manager=None)` (manager is optional)
2. Call `load_matches_db(db_path)` to populate the cache
3. Use `get_cached_score(seg_a, seg_b)` for lookups

This avoids loading all sheet images just for scoring.

---

## File touchmap

| File | Change |
|------|--------|
| `src/snap_fit/webapp/services/interactive_service.py` | Add `suggest_next()`, `accept()`, `reject()` |
| `src/snap_fit/webapp/routers/interactive.py` | Add `POST .../next_suggestion`, `POST .../accept`, `POST .../reject` |
| `src/snap_fit/webapp/schemas/interactive.py` | Add `SuggestionRequest` (already planned in 04) |
| `src/snap_fit/persistence/sqlite_store.py` | Add `update_match_manual_score()` |
| `src/snap_fit/grid/suggestion.py` | **NEW** - `pick_next_slot()`, `score_candidates()` |

---

## Test strategy

- Unit test: `pick_next_slot()` - empty grid returns corner; grid with one corner returns adjacent edge
- Unit test: `pick_next_slot()` with `override_pos` - returns that pos; raises if occupied
- Unit test: `score_candidates()` - returns sorted candidates; rejects are excluded
- Unit test: accept/reject update manual scores in SQLite
- Integration test: create session, suggest, accept, suggest again (different slot)
- Integration test: reject all candidates for a slot, auto-advance to next slot
