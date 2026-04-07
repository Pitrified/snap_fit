# `grid/placement_state`

> Module: `src/snap_fit/grid/placement_state.py`
> Related tests: `tests/grid/`

## Purpose

Mutable container tracking piece-to-position assignments on the grid. Maintains bidirectional mappings (position to piece and piece to position) for efficient lookups during solving.

## Usage

### Minimal example

```python
from snap_fit.grid import GridModel, PlacementState, GridPos, Orientation
from snap_fit.data_models import PieceId

grid = GridModel(rows=3, cols=3)
state = PlacementState(grid)

pid = PieceId(sheet_id="s1", piece_id=0)
state.place(pid, GridPos(ro=0, co=0), Orientation.DEG_0)

print(state.placed_count)   # 1
print(state.empty_count)    # 8
print(state.is_complete())  # False

# Lookup
pos = state.get_position(pid)             # GridPos(ro=0, co=0)
piece, orient = state.get_placement(pos)  # (pid, DEG_0)

# Clone for branching
branch = state.clone()

# Remove a piece
removed = state.remove(GridPos(ro=0, co=0))  # (pid, DEG_0)
```

## API Reference

### `PlacementState`

| Method | Description |
|--------|-------------|
| `place(piece_id, pos, orientation)` | Assign piece to slot (handles conflicts) |
| `remove(pos)` | Remove and return piece at position |
| `get_placement(pos)` | Get `(piece_id, orientation)` at position |
| `get_position(piece_id)` | Get position of a placed piece |
| `is_complete()` | All cells filled? |
| `clone()` | Shallow copy for branching |
| `empty_positions()` | List of unoccupied positions |
| `placed_pieces()` | List of placed piece IDs |

Conflict resolution: placing a piece that is already placed elsewhere moves it. Placing into an occupied slot removes the existing piece first.

## Related Modules

- [`grid/grid_model`](grid_model.md) - the grid structure being filled
- [`grid/scoring`](scoring.md) - scores placements using match data
- [`solver/naive_linear_solver`](../solver/naive_linear_solver.md) - populates placement state during solve
