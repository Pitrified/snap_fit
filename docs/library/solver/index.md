# `solver`

> Module: `src/snap_fit/solver/`
> Related tests: `tests/solver/`

## Purpose

Puzzle solving algorithms. Currently provides `NaiveLinearSolver`, a greedy row-by-row solver that places pieces by selecting the best match at each position.

## Submodule Overview

| Module | Description |
|--------|-------------|
| [`naive_linear_solver`](naive_linear_solver.md) | Greedy solver filling the grid left-to-right, top-to-bottom |

## Usage

```python
from snap_fit.solver import NaiveLinearSolver, partition_pieces_by_type
from snap_fit.grid import GridModel

# Partition pieces by type
corners, edges, inners = partition_pieces_by_type(manager)

# Infer or specify grid size
grid = GridModel(rows=4, cols=6)

# Solve
solver = NaiveLinearSolver(grid, matcher, manager, corners, edges, inners)
result = solver.solve()
score = solver.score_solution()

print(f"Placed {result.placed_count}/{grid.total_cells} pieces, score={score:.2f}")
```

### Utility functions

```python
from snap_fit.solver.utils import partition_pieces_by_type, infer_grid_size, get_factor_pairs

corners, edges, inners = partition_pieces_by_type(manager)
grid_size = infer_grid_size(corners, edges, inners)
factors = get_factor_pairs(24)  # [(4, 6)]
```

## Related Modules

- [`grid`](../grid/index.md) - `GridModel`, `PlacementState`, scoring functions
- [`puzzle/piece_matcher`](../puzzle/piece_matcher.md) - provides cached similarity scores
- [`puzzle/sheet_manager`](../puzzle/sheet_manager.md) - provides piece metadata for orientation
