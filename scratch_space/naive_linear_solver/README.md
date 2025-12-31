# Naive Linear Solver Implementation Plan

## Overview

The Naive Linear Solver will implement a straightforward row-by-row puzzle assembly strategy. Starting from a randomly selected top-left corner piece, it will build the puzzle systematically by filling each row from left to right before moving to the next row.

### Key Requirements

- Start with a randomly selected corner piece (top-left position)
- Fill the first row (row 0) completely from left to right until the top-right corner is placed
- For subsequent rows:
  - Place the leftmost edge piece first
  - Fill inner pieces by finding the best match considering:
    - The previous piece in the current row (left neighbor)
    - The piece from the row above in the same column (top neighbor)

### Implementation Approaches

**Option A: Greedy Best-Match Strategy**

- **Description**: For each position, evaluate all available unplaced pieces and select the one with the best combined similarity score.
- **Pros**:
  - Simple to implement and understand
  - Fast execution (no backtracking)
  - Good baseline for comparison with more sophisticated solvers
- **Cons**:
  - May make suboptimal choices early that cascade into poor overall solutions
  - No recovery mechanism if a wrong piece is placed
  - Relies heavily on match quality of `PieceMatcher`
- **Best for**: Initial prototyping and establishing baseline performance

**Option B: Limited Lookahead with Scoring**

- **Description**: For each position, evaluate the top N candidate pieces and look ahead 1-2 positions to see which choice leads to better subsequent matches.
- **Pros**:
  - Can avoid obvious mistakes by considering future implications
  - Still relatively fast with small lookahead depth
  - More robust than pure greedy approach
- **Cons**:
  - More complex implementation
  - Slower than pure greedy (N × lookahead_positions evaluations)
  - May still get stuck in local optima
- **Best for**: Improved accuracy with reasonable computational cost

**Option C: Backtracking with Early Termination**

- **Description**: Use greedy placement but keep track of decision history. If similarity scores drop below a threshold, backtrack and try the next-best option.
- **Pros**:
  - Can recover from bad decisions
  - Most likely to find correct solution
  - Threshold tuning allows controlling compute vs accuracy tradeoff
- **Cons**:
  - Most complex to implement and maintain
  - Potentially much slower (exponential worst case)
  - Requires careful threshold tuning
  - May need maximum backtrack depth to prevent infinite loops
- **Best for**: Production use where accuracy is critical

---

## Selected Approach: Option A – Greedy Best-Match Strategy

Option A was chosen for initial implementation due to its simplicity and suitability as a baseline solver.

---

## Plan

### Dependencies (Existing Classes to Leverage)

| Class            | Module                            | Purpose                                                                          |
| ---------------- | --------------------------------- | -------------------------------------------------------------------------------- |
| `GridModel`      | `snap_fit.grid.grid_model`        | Defines puzzle structure, slot types (corner/edge/inner), canonical orientations |
| `PlacementState` | `snap_fit.grid.placement_state`   | Mutable state tracking piece-to-position assignments with bidirectional lookups  |
| `PieceMatcher`   | `snap_fit.puzzle.piece_matcher`   | Computes and caches segment-pair similarity scores                               |
| `SheetManager`   | `snap_fit.puzzle.sheet_manager`   | Provides access to all pieces and segments across sheets                         |
| `score_edge`     | `snap_fit.grid.scoring`           | Scores match quality between two adjacent placed pieces                          |
| `Orientation`    | `snap_fit.grid.orientation`       | Rotation enum (DEG_0, DEG_90, DEG_180, DEG_270)                                  |
| `GridPos`        | `snap_fit.grid.types`             | Immutable (ro, co) position on the grid                                          |
| `PieceId`        | `snap_fit.data_models.piece_id`   | Unique identifier for a puzzle piece                                             |
| `SegmentId`      | `snap_fit.data_models.segment_id` | Identifies a specific edge segment (piece_id + edge_pos)                         |

### Algorithm Outline

```
1. INITIALIZATION
   - Create GridModel(rows, cols)
   - Create PlacementState(grid)
   - Build PieceMatcher from SheetManager
   - Pre-compute match_all() to populate similarity cache
   - Partition available pieces by type: corners, edges, inners

2. PLACE TOP-LEFT CORNER (0, 0)
   - Select a random corner piece from available corners
   - Place with Orientation.DEG_0 (flats on TOP + LEFT)
   - Remove from available corners

3. FILL ROW 0 (left to right)
   For col in 1..cols-2 (edge slots):
       - Get required orientation from grid.get_slot_type(pos)
       - For each candidate edge piece:
           - Compute score vs left neighbor using score_edge()
       - Select piece with lowest (best) score
       - Place with required orientation
       - Remove from available edges

4. PLACE TOP-RIGHT CORNER (0, cols-1)
   - For each remaining corner piece:
       - Compute score vs left neighbor
   - Select best match
   - Place with Orientation.DEG_90 (flats on TOP + RIGHT)
   - Remove from available corners

5. FILL REMAINING ROWS (row 1 to rows-1)
   For each row:
       a. PLACE LEFT EDGE (row, 0)
          - Get required orientation (DEG_270 for left column)
          - Score candidates against top neighbor
          - Select best, place, remove from available

       b. FILL INNER SLOTS (row, 1..cols-2)
          - For each position:
              - For each candidate inner piece:
                  - For each orientation in [DEG_0, DEG_90, DEG_180, DEG_270]:
                      - Temporarily place piece at position with this orientation
                      - Compute score_left + score_top using score_edge()
                      - Track (piece, orientation, combined_score)
              - Select (piece, orientation) with lowest combined score
              - Place with the winning orientation
              - Remove from available inners

       c. PLACE RIGHT EDGE (row, cols-1)
          - Score against left and top neighbors
          - Select best, place with DEG_90

       d. IF LAST ROW: place corners at (rows-1, 0) and (rows-1, cols-1)
          with DEG_270 and DEG_180 respectively

6. RETURN
   - PlacementState with all pieces placed
   - Total grid score via score_grid(state, matcher)
```

### Class Design

```python
class NaiveLinearSolver:
    """Greedy row-by-row puzzle solver."""

    def __init__(
        self,
        grid: GridModel,
        matcher: PieceMatcher,
        pieces: list[PieceId],
    ) -> None: ...

    def solve(self) -> PlacementState:
        """Execute the greedy solver and return final state."""

    def _find_best_piece(
        self,
        candidates: list[PieceId],
        pos: GridPos,
        neighbors: list[GridPos],
        orientations: list[Orientation] | None = None,
    ) -> tuple[PieceId, Orientation, float]:
        """Score all candidates (and orientations) against placed neighbors.

        Args:
            candidates: Available pieces to try.
            pos: Target grid position.
            neighbors: Adjacent positions with already-placed pieces.
            orientations: List of orientations to try. If None, uses the
                          canonical orientation from grid.get_slot_type(pos).
                          For inner pieces, pass all 4 orientations.

        Returns:
            Tuple of (best_piece_id, best_orientation, best_score).
        """

    def _place_row_zero(self) -> None:
        """Place first row: corner → edges → corner."""

    def _place_subsequent_row(self, row: int) -> None:
        """Place a row using top and left neighbor constraints."""
```

### Output

- `PlacementState` object with all pieces placed
- Total score (sum of all edge similarities; lower = better)
- Optional: per-edge score breakdown via `score_grid_with_details()`

### Testing Strategy

1. **Unit tests** for `_find_best_piece` with mock matcher scores
2. **Integration test** with a small 3×3 puzzle (known solution)
3. **Regression test** comparing solver output against hand-verified placements

### Success Criteria

- Solver completes without errors on valid input
- All grid positions filled exactly once
- Each piece used exactly once
- Score is computed and returned
- Baseline accuracy established for comparison with future solvers
