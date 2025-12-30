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

## Plan

### Selected Approach: Option A - Greedy Best-Match Strategy

This plan implements a simple row-by-row assembly using greedy best-match selection. The solver leverages existing classes from the codebase for grid management and piece positioning.

### Phase 1: Core Solver Class

1. [ ] **Define `NaiveLinearSolver` Class**

   - Create `src/snap_fit/puzzle/naive_linear_solver.py`.
   - `__init__(self, manager: SheetManager, matcher: PieceMatcher, puzzle_config: PuzzleConfig)`:
     - Store references to manager, matcher, and puzzle_config.
     - Use `puzzle_config.tiles_x` and `puzzle_config.tiles_y` for grid dimensions.
   - Use `PuzzleGenerator`'s row/col positioning model internally:
     - `self.solution: dict[tuple[int, int], PieceId]` maps (row, col) → placed piece.
     - `self.available: set[PieceId]` tracks unplaced pieces.

2. [ ] **Implement Piece Type Identification**

   - `count_edge_segments(self, piece: Piece) -> int`:
     - Count segments where `segment.shape == SegmentShape.EDGE`.
     - Use `piece.segments` dict (keyed by `EdgePos`) from the `Piece` class.
   - `is_corner_piece(self, piece: Piece) -> bool`: Returns `True` if edge count == 2.
   - `is_edge_piece(self, piece: Piece) -> bool`: Returns `True` if edge count == 1.
   - `is_inner_piece(self, piece: Piece) -> bool`: Returns `True` if edge count == 0.

3. [ ] **Implement Position Validation**

   - `get_required_edge_count(self, row: int, col: int) -> int`:
     - Use `puzzle_config.tiles_x` and `puzzle_config.tiles_y` for bounds.
     - Corner positions: Return 2.
     - Edge positions: Return 1.
     - Inner positions: Return 0.
   - `is_valid_for_position(self, piece: Piece, row: int, col: int) -> bool`:
     - Check if `count_edge_segments(piece) == get_required_edge_count(row, col)`.

### Phase 2: Match Scoring

4. [ ] **Implement Neighbor Segment Retrieval**

   - `get_neighbor_segment_id(self, row: int, col: int, direction: EdgePos) -> SegmentId | None`:
     - Given current position and direction (LEFT or TOP), return the segment ID of the neighbor.
     - For LEFT neighbor: Get piece at (row, col-1), return its RIGHT segment.
     - For TOP neighbor: Get piece at (row-1, col), return its BOTTOM segment.
     - Use `SegmentId(piece_id=neighbor_piece_id, edge_pos=edge_pos)`.

5. [ ] **Implement Match Scoring for Position**

   - `score_piece_for_position(self, piece: Piece, row: int, col: int) -> float`:
     - If not `is_valid_for_position`, return `float('inf')` (poor match).
     - Collect neighbor scores:
       - If col > 0: Get LEFT neighbor's segment, query `matcher._lookup` for match with piece's LEFT segment.
       - If row > 0: Get TOP neighbor's segment, query `matcher._lookup` for match with piece's TOP segment.
     - Return average similarity of available neighbors (lower is better).
     - If no neighbors yet (first piece), return 0.0.

6. [ ] **Implement Best Piece Selection**

   - `find_best_piece_for_position(self, row: int, col: int) -> Piece | None`:
     - Iterate over `self.available` piece IDs.
     - Use `manager.get_piece(piece_id)` to retrieve each piece.
     - Score each using `score_piece_for_position`.
     - Return piece with lowest score (best match).

### Phase 3: Assembly Algorithm

7. [ ] **Implement Row-by-Row Assembly**

   - `solve(self) -> bool`:
     - **Step 1**: Randomly select a corner piece for position (0, 0):
       - Filter `available` pieces by `is_corner_piece`.
       - Select one randomly.
     - **Step 2**: Iterate positions row-major order (row 0 → tiles_y-1, col 0 → tiles_x-1):
       - Find best piece using `find_best_piece_for_position`.
       - If no valid piece found, return False (unsolvable).
       - Place piece: Update `self.solution[(row, col)]` and remove from `self.available`.
     - **Step 3**: Return True when all positions filled.

8. [ ] **Implement Result Access**

   - `get_solution(self) -> dict[tuple[int, int], PieceId]`: Return copy of solution dict.
   - `get_solution_grid(self) -> list[list[PieceId | None]]`:
     - Return 2D list representation for visualization.
     - Consistent with `PuzzleGenerator`'s row/col indexing.

### Phase 4: Validation & Testing

9. [ ] **Create Prototype Notebook**

   - Create `scratch_space/naive_linear_solver/01_naive_solver.ipynb`:
     - Generate synthetic puzzle using `PuzzleGenerator` with known solution.
     - Use `PuzzleRasterizer` to rasterize pieces to images.
     - Load pieces into `SheetManager`.
     - Compute matches using `PieceMatcher.match_all()`.
     - Initialize solver with `PuzzleConfig` from generator.
     - Run `solve()` and compare with ground truth.
     - Report accuracy metrics.

10. [ ] **Create Usage Notebook**

    - Create `scratch_space/naive_linear_solver/02_usage.ipynb`:
      - End-to-end demonstration with photographed puzzle sheets.
      - Load using `SheetAruco` → `SheetManager`.
      - Estimate puzzle dimensions (or accept as input).
      - Run solver and visualize results.

11. [ ] **Add Unit Tests**

    - Create `tests/puzzle/test_naive_linear_solver.py`:
      - Test piece type identification using mock pieces with varying edge counts.
      - Test position validation logic.
      - Test small 2×2 puzzle with perfect match data.
      - Test failure handling when no valid pieces remain.

### Phase 5: Integration & Documentation

12. [ ] **Integration with Existing Models**

    - Leverages `PuzzleConfig` for grid dimensions and piece sizing.
    - Uses `PuzzlePiece.row` and `PuzzlePiece.col` for reference positioning.
    - Integrates with `SheetManager` for piece access via `PieceId`.
    - Uses `PieceMatcher` precomputed results via `_lookup` dict.
    - Respects `EdgePos` enum for direction handling.

13. [ ] **Add Usage Documentation**

    - Document constructor parameters and their purpose.
    - Provide example showing full pipeline from generation to solving.
    - Note assumptions: requires `PuzzleConfig` matching actual puzzle dimensions.
    - Document limitations of greedy approach.

---

## Expected File Structure

```
src/snap_fit/puzzle/
└── naive_linear_solver.py    # Greedy row-by-row solver

scratch_space/naive_linear_solver/
├── README.md                  # This file
├── 01_naive_solver.ipynb     # Prototype with synthetic puzzles
└── 02_usage.ipynb            # Real puzzle solving workflow

tests/puzzle/
└── test_naive_linear_solver.py
```

## Integration Points

**Reuses Existing Classes:**

- `PuzzleConfig`: Provides `tiles_x`, `tiles_y` for grid dimensions
- `PuzzleGenerator`: Reference model for row/col positioning
- `PuzzlePiece`: Has `row`, `col` attributes for ground truth comparison
- `SheetManager`: Provides piece access and segment retrieval
- `PieceMatcher`: Supplies precomputed match scores via `_lookup`
- `Piece`: Has `segments` dict with `EdgePos` → `Segment` mapping
- `SegmentShape.EDGE`: Identifies border segments
- `EdgePos`: Enum for directional navigation (LEFT, RIGHT, TOP, BOTTOM)

**Key Design Decisions:**

- Grid coordinates match `PuzzleGenerator` convention: (0, 0) is top-left
- Edge identification uses `SegmentShape.EDGE` from existing `Segment` class
- Match scores retrieved from `PieceMatcher._lookup` (frozenset-based symmetry)
- Solution representation uses (row, col) tuples for consistency

## Implementation Notes

- **Greedy Nature**: Makes irrevocable placement decisions without backtracking.
- **Match Quality Dependency**: Success depends on `PieceMatcher` accuracy.
- **Failure Mode**: May fail to complete if wrong pieces placed early.
- **Performance**: O(n²) for n pieces—each position evaluates remaining pieces once.
- **Baseline Purpose**: Establishes performance baseline for Options B and C.
- **Ground Truth Validation**: Can compare solution to `PuzzlePiece.row`, `PuzzlePiece.col` when using generated puzzles.
