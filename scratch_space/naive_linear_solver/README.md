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

_To be filled after approach selection_
