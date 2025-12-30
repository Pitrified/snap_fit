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

This plan implements a simple row-by-row assembly using greedy best-match selection. The solver will make locally optimal choices at each position without backtracking.

### Phase 1: Core Solver Class

1. [ ] **Define `NaiveLinearSolver` Class**

   - Create `src/snap_fit/puzzle/naive_linear_solver.py`.
   - `__init__(self, manager: SheetManager, matcher: PieceMatcher)`: Store references to manager and matcher.
   - Store puzzle dimensions: `self.rows`, `self.cols` (inferred from piece count or configured).
   - Track placement state: `self.grid: dict[tuple[int, int], PieceId]` for (row, col) → placed piece.
   - Track available pieces: `self.available: set[PieceId]` (initially all pieces from manager).

2. [ ] **Implement Piece Selection Methods**

   - `get_corner_pieces(self) -> list[PieceId]`: Return pieces with 2 edge segments.
   - `get_edge_pieces(self) -> list[PieceId]`: Return pieces with 1 edge segment.
   - `get_inner_pieces(self) -> list[PieceId]`: Return pieces with 0 edge segments.
   - Use `SheetManager` to query segment information for each piece.

3. [ ] **Implement Position Constraint Checking**

   - `is_valid_for_position(self, piece_id: PieceId, row: int, col: int) -> bool`:
     - Check if piece has correct number of edges for the position (corner/edge/inner).
     - Corner positions (0,0), (0, cols-1), (rows-1, 0), (rows-1, cols-1): Need 2 edge segments.
     - Edge positions (row=0, row=rows-1, col=0, col=cols-1): Need 1 edge segment.
     - Inner positions: Need 0 edge segments.

### Phase 2: Match Scoring

4. [ ] **Implement Match Scoring for Position**

   - `score_piece_for_position(self, piece_id: PieceId, row: int, col: int) -> float`:
     - If piece doesn't satisfy position constraints, return -inf.
     - Calculate combined similarity score considering:
       - **Left neighbor**: If col > 0, get match score between piece's left segment and placed neighbor's right segment.
       - **Top neighbor**: If row > 0, get match score between piece's top segment and placed neighbor's bottom segment.
     - Return average of available neighbor scores (or 0.0 if no neighbors yet).
   - Use `PieceMatcher.get_match(seg_id1, seg_id2)` to retrieve precomputed scores.

5. [ ] **Implement Best Piece Selection**

   - `find_best_piece_for_position(self, row: int, col: int) -> PieceId | None`:
     - Iterate over all `self.available` pieces.
     - Score each piece using `score_piece_for_position`.
     - Return piece with highest score (or None if no valid pieces).

### Phase 3: Assembly Algorithm

6. [ ] **Implement Row-by-Row Assembly**

   - `solve(self) -> bool`:
     - **Step 1**: Randomly select a corner piece for position (0, 0).
     - **Step 2**: For each position in row-major order (row 0 → rows-1, col 0 → cols-1):
       - Find best piece using `find_best_piece_for_position`.
       - If no valid piece found, return False (failure).
       - Place piece: Update `self.grid[(row, col)]` and remove from `self.available`.
     - **Step 3**: Return True when all positions filled.

7. [ ] **Implement Result Retrieval**

   - `get_solution(self) -> dict[tuple[int, int], PieceId]`: Return copy of `self.grid`.
   - `get_solution_as_list(self) -> list[list[PieceId]]`: Return 2D list representation of solution.

### Phase 4: Validation & Testing

8. [ ] **Create Prototype Notebook**

   - Create `scratch_space/naive_linear_solver/01_naive_solver.ipynb`:
     - Load test puzzle sheets using `SheetManager`.
     - Compute matches using `PieceMatcher`.
     - Initialize and run `NaiveLinearSolver`.
     - Visualize solution grid.
     - Report success rate and quality metrics.

9. [ ] **Create Usage Notebook**

   - Create `scratch_space/naive_linear_solver/02_usage.ipynb`:
     - End-to-end workflow demonstration.
     - Load puzzle from generated sheets.
     - Run solver and display results.
     - Compare with ground truth if available.

10. [ ] **Add Unit Tests**
    - Create `tests/puzzle/test_naive_linear_solver.py`:
      - Test piece type identification (corner/edge/inner).
      - Test position constraint validation.
      - Test scoring logic with mock matches.
      - Test small puzzle (3×3) with perfect match data.
      - Test failure handling when no valid pieces available.

### Phase 5: Integration

11. [ ] **Document Dependencies**

    - Depends on `SheetManager` for piece access.
    - Depends on `PieceMatcher` for precomputed match scores.
    - Uses `SegmentId` and `PieceId` for identification.

12. [ ] **Add Example Usage to README**
    - Include code snippet showing typical usage pattern.
    - Document expected inputs and outputs.
    - Note limitations of greedy approach.

---

## Expected File Structure

```
src/snap_fit/puzzle/
└── naive_linear_solver.py    # Greedy row-by-row solver

scratch_space/naive_linear_solver/
├── README.md                  # This file
├── 01_naive_solver.ipynb     # Prototype and testing
└── 02_usage.ipynb            # End-to-end demonstration

tests/puzzle/
└── test_naive_linear_solver.py
```

## Implementation Notes

- **Greedy Nature**: This solver makes irrevocable placement decisions. Once a piece is placed, it's never reconsidered.
- **Match Quality Dependency**: Success heavily depends on `PieceMatcher` producing accurate similarity scores.
- **Failure Mode**: If the greedy approach places wrong pieces early, it may be unable to complete the puzzle (no valid pieces for later positions).
- **Performance**: Fast execution - O(n²) for n pieces (each position evaluates remaining pieces once).
- **Baseline**: This serves as a baseline to compare against more sophisticated solvers (Options B and C).
