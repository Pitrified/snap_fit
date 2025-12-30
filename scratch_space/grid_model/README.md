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

### Phase 1: Core Enums & Types ✅

1. [x] Create `Orientation` enum (0, 90, 180, 270) with rotation arithmetic (`__add__`, `__sub__`, modular)
2. [x] Create `PieceType` enum (CORNER, EDGE, INNER) – used for both pieces and grid slots
3. [x] Create `GridPos` Pydantic model with:
   - `ro: int` (row)
   - `co: int` (column)
4. [x] Create `OrientedPieceType` Pydantic model with:
   - `piece_type: PieceType`
   - `orientation: Orientation` (canonical flat-side orientation)

### Phase 2: Orientation Utilities (`orientation_utils.py`) ✅

5. [x] `get_piece_type(flat_edge_count: int) -> PieceType` – classify piece (0 flat → INNER, 1 flat → EDGE, 2 flat → CORNER)
6. [x] `detect_base_orientation(flat_edge_positions: list[EdgePos]) -> Orientation` – determine piece's photographed orientation relative to canonical
7. [x] `compute_rotation(piece: OrientedPieceType, target: OrientedPieceType) -> Orientation` – rotation needed to align piece's base orientation to target slot orientation
8. [x] `get_rotated_edge_pos(original_pos: EdgePos, rotation: Orientation) -> EdgePos` – compute effective edge position after rotation
   - Also added `get_original_edge_pos()` for inverse operation

### Phase 3: Piece Integration ✅

9. [x] During `Piece` init (or post-processing), derive and store `OrientedPieceType`:
   - Count flat edges → `PieceType`
   - Detect flat edge positions → base `Orientation`
   - Added `flat_edges` property for direct access
10. [x] Add method `Piece.get_segment_at(edge_pos: EdgePos, rotation: Orientation) -> Segment` – returns segment considering rotation

### Phase 4: Grid Structure (`GridModel`) ✅

11. [x] `GridModel.__init__(rows: int, cols: int)` – store dimensions
12. [x] Internal structures:
    - `_slot_types: dict[GridPos, OrientedPieceType]` – computed once from position
    - Pre-built position lists: `corners: list[GridPos]`, `edges: list[GridPos]`, `inners: list[GridPos]`
13. [x] `get_slot_type(pos: GridPos) -> OrientedPieceType` – returns required piece type and orientation for slot
14. [x] `neighbors(pos: GridPos) -> list[GridPos]` – adjacent positions (up to 4)
15. [x] `neighbor_pairs() -> Iterator[tuple[GridPos, GridPos]]` – all adjacent pairs for scoring
    - Also added `all_positions()`, `total_cells`, `total_edges`

### Phase 5: Placement State (`PlacementState`) ✅

Mutable container for piece assignments.

16. [x] `PlacementState.__init__(grid: GridModel)`
17. [x] Internal structures:
    - `_grid: GridModel` (reference)
    - `_placements: dict[GridPos, tuple[PieceID, Orientation]]` – position → (piece, rotation)
    - `_positions: dict[PieceID, GridPos]` – piece → position (reverse lookup)
18. [x] `place(piece_id: PieceID, pos: GridPos, orientation: Orientation)` – assign piece to slot
19. [x] `remove(pos: GridPos) -> tuple[PieceID, Orientation] | None` – remove and return placement
20. [x] `get_placement(pos: GridPos) -> tuple[PieceID, Orientation] | None`
21. [x] `get_position(piece_id: PieceID) -> GridPos | None`
22. [x] `is_complete() -> bool` – all cells filled
23. [x] `clone() -> PlacementState` – shallow copy for branching (if needed)
    - Also added `placed_count`, `empty_count`, `empty_positions()`, `placed_pieces()`

### Phase 6: Scoring Integration ✅

Leverage existing `PieceMatcher._lookup` cache.

24. [x] Add `PieceMatcher.get_cached_score(seg_a: SegID, seg_b: SegID) -> float | None` – public getter for cached pair score
25. [x] `score_edge(state: PlacementState, pos1: GridPos, pos2: GridPos, matcher) -> float` – score one adjacency using rotated segment access
26. [x] `score_grid(state: PlacementState, matcher) -> float` – sum over all neighbor pairs
    - Also added `score_grid_with_details()` for per-edge breakdown
27. [ ] Optional: `ScoreCache` wrapper to memoize per-placement scores and invalidate on changes

### Phase 7: Prototype Notebook

28. [ ] `01_grid_model.ipynb` – build & validate `Orientation`, `GridPos`, `OrientedPieceType`, `GridModel`, `PlacementState`
29. [ ] `02_scoring.ipynb` – end-to-end scoring with real pieces

### Phase 8: Promote to `src/` ✅

30. [x] Move validated modules to `src/snap_fit/grid/`
31. [x] Add unit tests in `tests/grid/` (71 tests passing)

---

## Resolved Questions

- **Orientation storage:** Store rotation per placement, compute segment access on demand ✓
- **Flat-edge detection:** Already derived during piece processing ✓
- **Score invalidation:** Start simple (recompute full grid), optimize later ✓
