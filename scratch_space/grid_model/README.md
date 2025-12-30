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

## changes requested:

1. `EdgeSide` should not exists, desired edge orientation can be expressed via `Orientation` directly,
   after deciding which is a canonical side for each piece type (eg flat on top for edge pieces, flats on top+left for corner pieces).
2. keep `PieceType` enum but remove `PlaceType`, as they are redundant.
3. create a more complex `OrientedPieceType` (base model) that has as attributes both `PieceType` and the `Orientation` for that photographed piece or grid slot.
4. in orientation utils for the grid, the dict mapping grid positions to desired orientations should map to `OrientedPieceType` instead of `EdgeSide`. Only one dict is needed, mapping (row,col) to desired `OrientedPieceType`.
5. during `Piece` init, derive and store its `OrientedPieceType` based on flat edge count and detected flat edge sides.
6. `compute_rotation` should take two `OrientedPieceType` instead of `EdgeSide`, then compute the rotation (as orientation) needed to align the piece's base orientation to the target orientation.
7. `rotate_segments` should not exist, instead provide either
  - a method on `Piece` that returns the requested segment (as `EdgePos`) considering a target orientation
  - a segment id builder that computes the right EdgePos based on target orientation and requested EdgePos in original orientation.
8. exclude `swap` and `swap_and_reorient(pos1, pos2)` from `PlacementState`

## Plan

### Phase 1: Core Enums & Types

1. [ ] Create `Orientation` enum (0, 90, 180, 270) with rotation arithmetic (`__add__`, `__sub__`)
2. [ ] Create `PlaceType` enum (CORNER, EDGE, INNER)
3. [ ] Create `EdgeSide` enum (TOP, RIGHT, BOTTOM, LEFT) for desired edge orientation on grid boundary
4. [ ] Create `PieceType` enum mirroring `PlaceType` (derived from flat-edge count)

### Phase 2: Orientation Utilities (`orientation_utils.py`)

5. [ ] `get_piece_type(flat_edge_count: int) -> PieceType` – classify piece
6. [ ] `get_base_edge_orientation(piece: Piece) -> EdgeSide` – detect which side has the flat edge(s)
7. [ ] `compute_rotation(base: EdgeSide, target: EdgeSide) -> Orientation` – rotation needed to align
8. [ ] `rotate_segments(segments: list[SegID], orientation: Orientation) -> list[SegID]` – reorder segment list for rotated piece (index shift)

### Phase 3: Grid Structure (`GridModel`)

9. [ ] `GridModel.__init__(rows: int, cols: int)` – store dimensions
10. [ ] Internal structures:
    - `_place_types: dict[tuple[int,int], PlaceType]` – computed once from position
    - `_edge_sides: dict[tuple[int,int], EdgeSide | None]` – boundary cells only
    - Pre-built lists: `corners`, `edges`, `inners` for fast iteration
11. [ ] `get_place_type(row, col) -> PlaceType`
12. [ ] `get_required_edge_side(row, col) -> EdgeSide | None` – which side must be flat (for edge/corner cells)
13. [ ] `neighbors(row, col) -> list[tuple[int,int]]` – adjacent positions (up to 4)
14. [ ] `neighbor_pairs() -> Iterator[((r1,c1),(r2,c2))]` – all adjacent pairs for scoring

### Phase 4: Placement State (`PlacementState`)

Mutable container optimized for swaps.

15. [ ] `PlacementState.__init__(grid: GridModel)`
16. [ ] Internal structures:
    - `_grid: GridModel` (reference)
    - `_placements: dict[tuple[int,int], tuple[PieceID, Orientation]]` – position → (piece, rot)
    - `_positions: dict[PieceID, tuple[int,int]]` – piece → position (reverse lookup)
17. [ ] `place(piece_id, row, col, orientation)` – assign piece
18. [ ] `remove(row, col) -> tuple[PieceID, Orientation] | None`
19. [ ] `swap(pos1, pos2)` – swap two placements in O(1), keep orientations
20. [ ] `swap_and_reorient(pos1, pos2)` – swap and auto-compute new orientations for boundary fit
21. [ ] `get_placement(row, col) -> tuple[PieceID, Orientation] | None`
22. [ ] `get_position(piece_id) -> tuple[int,int] | None`
23. [ ] `is_complete() -> bool` – all cells filled
24. [ ] `clone() -> PlacementState` – shallow copy for branching (if needed)

### Phase 5: Scoring Integration

Leverage existing `PieceMatcher._lookup` cache.

25. [ ] Add `PieceMatcher.get_cached_score(seg_a: SegID, seg_b: SegID) -> float | None` – public getter for cached pair score
26. [ ] `score_edge(state, pos1, pos2, piece_registry, matcher) -> float` – score one adjacency using rotated segments
27. [ ] `score_grid(state, piece_registry, matcher) -> float` – sum over all neighbor pairs
28. [ ] Optional: `ScoreCache` wrapper to memoize per-placement scores and invalidate on swap

### Phase 6: Prototype Notebook

29. [ ] `01_grid_model.ipynb` – build & validate `GridModel`, `PlacementState`
30. [ ] `02_scoring.ipynb` – end-to-end scoring with real pieces

### Phase 7: Promote to `src/`

31. [ ] Move validated modules to `src/snap_fit/grid/`
32. [ ] Add unit tests in `tests/grid/`

---

## Open Questions

- **Orientation storage:** Store rotation per piece, or store already-rotated segment order? (Propose: store rotation, compute segments on demand)
  answer: store rotation, compute segments on demand
- **Flat-edge detection:** Is flat-edge info already on `Piece`/`Segment`, or needs derivation from contour? (Need to check existing code)
  answer: already derived during piece processing
- **Score invalidation:** On swap, only two rows of edges change. Worth tracking dirty pairs, or just recompute full grid? (Depends on grid size; start simple, optimize later)
  answer: start simple, optimize later

---

Let me know if you'd like to refine any tasks or add detail to specific phases.
