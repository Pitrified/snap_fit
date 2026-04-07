# `grid/grid_model`

> Module: `src/snap_fit/grid/grid_model.py`
> Related tests: `tests/grid/`

## Purpose

Represents the puzzle grid structure. Pre-computes slot types (corner, edge, inner) and their required orientations for every position based on grid dimensions. Provides neighbor iteration for scoring.

## Usage

### Minimal example

```python
from snap_fit.grid.grid_model import GridModel
from snap_fit.grid.types import GridPos

grid = GridModel(rows=4, cols=6)

# Inspect slot types
slot = grid.get_slot_type(GridPos(ro=0, co=0))
print(slot)  # "CORNER@0deg"

# Pre-computed position lists
print(f"{len(grid.corners)} corners")   # 4
print(f"{len(grid.edges)} edges")       # 14
print(f"{len(grid.inners)} inners")     # 6

# Iterate neighbors
neighbors = grid.neighbors(GridPos(ro=1, co=1))  # up to 4 adjacent positions

# Iterate all adjacent pairs (each pair yielded once)
for pos1, pos2 in grid.neighbor_pairs():
    print(f"{pos1} <-> {pos2}")
```

## API Reference

### `GridModel`

Constructor: `GridModel(rows, cols)` - minimum 2x2.

| Method/Property | Description |
|----------------|-------------|
| `get_slot_type(pos)` | Required `OrientedPieceType` for a position |
| `neighbors(pos)` | Adjacent positions (up, right, down, left) |
| `neighbor_pairs()` | Iterator of all adjacent `(pos1, pos2)` tuples |
| `all_positions()` | Iterator of all `GridPos` in row-major order |
| `corners` | List of corner `GridPos` |
| `edges` | List of edge `GridPos` |
| `inners` | List of inner `GridPos` |
| `total_cells` | `rows * cols` |
| `total_edges` | Number of internal adjacencies |

### Orientation conventions

| Position | Piece Type | Orientation |
|----------|-----------|-------------|
| (0, 0) top-left | CORNER | DEG_0 (flats: TOP + LEFT) |
| (0, cols-1) top-right | CORNER | DEG_90 (flats: TOP + RIGHT) |
| (rows-1, cols-1) bottom-right | CORNER | DEG_180 (flats: BOTTOM + RIGHT) |
| (rows-1, 0) bottom-left | CORNER | DEG_270 (flats: BOTTOM + LEFT) |
| Top row (non-corner) | EDGE | DEG_0 (flat: TOP) |
| Right col | EDGE | DEG_90 (flat: RIGHT) |
| Bottom row | EDGE | DEG_180 (flat: BOTTOM) |
| Left col | EDGE | DEG_270 (flat: LEFT) |
| Interior | INNER | DEG_0 |

## Common Pitfalls

- **Minimum size**: Grid must be at least 2x2. A 1xN or Nx1 grid raises `ValueError`.

## Related Modules

- [`grid/orientation`](orientation.md) - `OrientedPieceType`, `Orientation`, `PieceType`
- [`grid/placement_state`](placement_state.md) - tracks which pieces are placed on this grid
- [`grid/types`](types.md) - `GridPos` model
