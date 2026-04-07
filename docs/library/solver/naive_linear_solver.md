# `solver/naive_linear_solver`

> Module: `src/snap_fit/solver/naive_linear_solver.py`
> Related tests: `tests/solver/`

## Purpose

Greedy row-by-row puzzle solver. Places pieces starting from the top-left corner, filling each row left-to-right before moving to the next. At each position, it selects the best-matching piece from the appropriate pool (corners, edges, or inners) based on similarity scores with already-placed neighbors.

## Usage

### Minimal example

```python
from snap_fit.solver import NaiveLinearSolver, partition_pieces_by_type
from snap_fit.grid import GridModel

corners, edges, inners = partition_pieces_by_type(manager)
grid = GridModel(rows=4, cols=6)

solver = NaiveLinearSolver(grid, matcher, manager, corners, edges, inners)
state = solver.solve()

print(f"Placed: {state.placed_count}/{grid.total_cells}")
print(f"Score: {solver.score_solution():.2f}")
```

## API Reference

### `NaiveLinearSolver`

Constructor takes: `grid`, `matcher`, `manager`, `corners`, `edges`, `inners` (piece ID lists).

| Method | Description |
|--------|-------------|
| `solve()` | Execute greedy solve, returns `PlacementState` |
| `score_solution(state=None)` | Compute total score (defaults to internal state) |

### Algorithm details

1. **Row 0**: Random corner at (0,0), then greedily fill edges using left-neighbor score, then corner at (0, cols-1)
2. **Subsequent rows**: Left edge/corner first (scored against top neighbor), then inner pieces (scored against top + left neighbors), then right edge/corner
3. **Fallback**: If a pool is empty (e.g., no corner pieces left), falls back to any remaining piece type with a warning
4. **Orientation**: Edge/corner pieces are automatically rotated so flat edges align with grid boundaries using detected `oriented_piece_type`

## Common Pitfalls

- **Greedy limitations**: The solver does not backtrack. A poor early choice can cascade through the solution. Run multiple times with different seeds for better results.
- **Misclassified pieces**: If shape detection classifies a corner as an edge (or vice versa), the solver falls back to alternative pools. This is logged as a warning.
- **First corner is random**: The top-left corner is chosen randomly from the corner pool, introducing non-determinism.

## Related Modules

- [`grid/grid_model`](../grid/grid_model.md) - defines the grid structure
- [`grid/placement_state`](../grid/placement_state.md) - tracks piece assignments
- [`grid/scoring`](../grid/scoring.md) - scores piece matches for selection
- [`solver/utils`](index.md) - `partition_pieces_by_type()`, `infer_grid_size()`
