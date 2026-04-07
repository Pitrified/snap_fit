# `grid`

> Module: `src/snap_fit/grid/`
> Related tests: `tests/grid/`

## Purpose

Models the puzzle grid structure: slot types (corner, edge, inner), orientations, piece placement tracking, and scoring. The grid layer bridges the gap between detected pieces and solved puzzles.

## Submodule Overview

| Module | Description |
|--------|-------------|
| [`grid_model`](grid_model.md) | Grid dimensions, slot type computation, neighbor iteration |
| [`orientation`](orientation.md) | `Orientation`, `PieceType`, `OrientedPieceType` enums and models |
| [`placement_state`](placement_state.md) | Mutable piece-to-position assignment tracker |
| [`scoring`](scoring.md) | Computes match quality for placed pieces |
| [`types`](types.md) | `GridPos` model for row/column positions |

## Key Concepts

- **Slot type**: Each grid position has a required `OrientedPieceType` (CORNER/EDGE/INNER + rotation)
- **Orientation**: Rotation in 90-degree steps (0, 90, 180, 270). Pieces must be rotated so their flat edges align with grid boundaries.
- **Scoring**: Sums pairwise similarity scores between adjacent placed pieces. Lower is better.

## Usage

```python
from snap_fit.grid import GridModel, PlacementState, GridPos, Orientation

grid = GridModel(rows=4, cols=6)
print(f"Corners: {grid.corners}")  # 4 corner positions
print(f"Edges: {grid.edges}")      # boundary non-corner positions
print(f"Total internal edges: {grid.total_edges}")

state = PlacementState(grid)
state.place(piece_id, GridPos(ro=0, co=0), Orientation.DEG_0)
```

## Related Modules

- [`puzzle/piece`](../puzzle/piece.md) - pieces have `OrientedPieceType` determined by flat edges
- [`solver`](../solver/index.md) - uses GridModel, PlacementState, and scoring to solve
- [`config`](../config/index.md) - `EdgePos` used for orientation mapping
