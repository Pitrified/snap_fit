# Grid Model Feature

## Overview

A grid model to represent puzzle piece placement with positions, orientations, and scoring.

### Key Requirements

- **Grid structure:** Rows × columns with typed positions (corner, edge, inner)
- **Piece classification:** Type derived from flat edge count; base edge orientation stored
- **Orientation math:** Compute rotation needed to place a piece in a target grid cell
- **Scoring:** Total grid score with cached segment-pair match lookups
- **Dynamic size:** Grid dimensions set at init (total pieces known, actual rows/cols configurable)

---

### Option A: Single Monolithic `GridModel` Class

A single class holding grid state, piece placements, orientation logic, and scoring.

**Pros:**

- Simple API surface; everything in one place
- Fewer files to maintain initially
- Easy to prototype in a notebook

**Cons:**

- Can grow unwieldy as complexity increases
- Harder to unit-test individual responsibilities
- Orientation math mixed with grid state management

---

### Option B: Layered Composition (Grid + PiecePlacement + OrientationUtils)

Separate concerns into:

1. `GridModel` – grid structure, position types, neighbor lookups
2. `PiecePlacement` – piece ↔ position assignments, orientations
3. `orientation_utils` – pure functions for rotation math
4. Scoring logic kept in `PieceMatcher` or a thin wrapper

**Pros:**

- Each unit is small and testable
- Orientation math reusable elsewhere
- Clearer boundaries for future extensions (e.g., solvers)

**Cons:**

- More files / imports to manage
- Slightly higher initial setup cost

---

### Option C: Data-Class-First Approach with Functional Scoring

Lean on Pydantic models for `GridCell`, `PlacedPiece`, `GridState`. Keep mutation minimal; scoring is a pure function over the state.

**Pros:**

- Immutable-friendly; easy to snapshot states for backtracking
- Pydantic validation for grid dimensions, orientations, etc.
- Functional scoring simplifies caching strategies

**Cons:**

- May require more boilerplate for state updates
- Less idiomatic if heavy mutation is expected during solving

---

**Selected: Option B** – Layered composition optimized for heavy pairwise swapping during solving.

---

## Design Decisions

1. **No `EdgeSide` enum** – desired edge orientation expressed via `Orientation` directly, using canonical flat-side conventions:
   - Edge pieces: flat on TOP (canonical)
   - Corner pieces: flats on TOP + LEFT (canonical)
2. **No `PlaceType` enum** – redundant with `PieceType`; use `PieceType` for both pieces and grid slots.
3. **`OrientedPieceType` model** – combines `PieceType` + `Orientation` to describe both photographed pieces and grid slot requirements.
4. **Single grid dict** – maps `(row, col)` → `OrientedPieceType` (desired type & orientation for that slot).
5. **Piece stores its `OrientedPieceType`** – derived at init from flat edge count and detected flat edge positions.
6. **Segment access via rotation** – no `rotate_segments` function; instead provide:
   - Method on `Piece` to get segment at a given `EdgePos` considering a target orientation, OR
   - Segment ID builder that computes the correct `EdgePos` given target orientation and requested position.
7. **No swap helpers on `PlacementState`** – swapping logic handled externally by solver.

---

## Plan

### Phase 1: Core Enums & Types

1. [ ] Create `Orientation` enum (0, 90, 180, 270) with rotation arithmetic (`__add__`, `__sub__`, modular)
2. [ ] Create `PieceType` enum (CORNER, EDGE, INNER) – used for both pieces and grid slots
3. [ ] Create `OrientedPieceType` Pydantic model with:
   - `piece_type: PieceType`
   - `orientation: Orientation` (canonical flat-side orientation)

### Phase 2: Orientation Utilities (`orientation_utils.py`)

4. [ ] `get_piece_type(flat_edge_count: int) -> PieceType` – classify piece (0 flat → INNER, 1 flat → EDGE, 2 flat → CORNER)
5. [ ] `detect_base_orientation(flat_edge_positions: list[EdgePos]) -> Orientation` – determine piece's photographed orientation relative to canonical
6. [ ] `compute_rotation(piece: OrientedPieceType, target: OrientedPieceType) -> Orientation` – rotation needed to align piece's base orientation to target slot orientation
7. [ ] `get_rotated_edge_pos(original_pos: EdgePos, rotation: Orientation) -> EdgePos` – compute effective edge position after rotation

### Phase 3: Piece Integration

8. [ ] During `Piece` init (or post-processing), derive and store `OrientedPieceType`:
   - Count flat edges → `PieceType`
   - Detect flat edge positions → base `Orientation`
9. [ ] Add method `Piece.get_segment_at(edge_pos: EdgePos, rotation: Orientation) -> Segment` – returns segment considering rotation

### Phase 4: Grid Structure (`GridModel`)

10. [ ] `GridModel.__init__(rows: int, cols: int)` – store dimensions
11. [ ] Internal structures:
    - `_slot_types: dict[tuple[int,int], OrientedPieceType]` – computed once from position
    - Pre-built position lists: `corners: list[tuple[int,int]]`, `edges: list[...]`, `inners: list[...]`
12. [ ] `get_slot_type(row, col) -> OrientedPieceType` – returns required piece type and orientation for slot
13. [ ] `neighbors(row, col) -> list[tuple[int,int]]` – adjacent positions (up to 4)
14. [ ] `neighbor_pairs() -> Iterator[tuple[tuple[int,int], tuple[int,int]]]` – all adjacent pairs for scoring

### Phase 5: Placement State (`PlacementState`)

Mutable container for piece assignments.

15. [ ] `PlacementState.__init__(grid: GridModel)`
16. [ ] Internal structures:
    - `_grid: GridModel` (reference)
    - `_placements: dict[tuple[int,int], tuple[PieceID, Orientation]]` – position → (piece, rotation)
    - `_positions: dict[PieceID, tuple[int,int]]` – piece → position (reverse lookup)
17. [ ] `place(piece_id: PieceID, row: int, col: int, orientation: Orientation)` – assign piece to slot
18. [ ] `remove(row: int, col: int) -> tuple[PieceID, Orientation] | None` – remove and return placement
19. [ ] `get_placement(row, col) -> tuple[PieceID, Orientation] | None`
20. [ ] `get_position(piece_id) -> tuple[int,int] | None`
21. [ ] `is_complete() -> bool` – all cells filled
22. [ ] `clone() -> PlacementState` – shallow copy for branching (if needed)

### Phase 6: Scoring Integration

Leverage existing `PieceMatcher._lookup` cache.

23. [ ] Add `PieceMatcher.get_cached_score(seg_a: SegID, seg_b: SegID) -> float | None` – public getter for cached pair score
24. [ ] `score_edge(state, pos1, pos2, piece_registry, matcher) -> float` – score one adjacency using rotated segment access
25. [ ] `score_grid(state, piece_registry, matcher) -> float` – sum over all neighbor pairs
26. [ ] Optional: `ScoreCache` wrapper to memoize per-placement scores and invalidate on changes

### Phase 7: Prototype Notebook

27. [ ] `01_grid_model.ipynb` – build & validate `Orientation`, `OrientedPieceType`, `GridModel`, `PlacementState`
28. [ ] `02_scoring.ipynb` – end-to-end scoring with real pieces

### Phase 8: Promote to `src/`

29. [ ] Move validated modules to `src/snap_fit/grid/`
30. [ ] Add unit tests in `tests/grid/`

---

## Resolved Questions

- **Orientation storage:** Store rotation per placement, compute segment access on demand ✓
- **Flat-edge detection:** Already derived during piece processing ✓
- **Score invalidation:** Start simple (recompute full grid), optimize later ✓
