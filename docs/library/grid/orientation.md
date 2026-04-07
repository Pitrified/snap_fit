# `grid/orientation`

> Module: `src/snap_fit/grid/orientation.py`
> Related tests: `tests/grid/`

## Purpose

Defines orientation and piece type enums used throughout the grid and solver layers. Supports rotation arithmetic for composing and inverting orientations.

## Usage

### Orientation arithmetic

```python
from snap_fit.grid.orientation import Orientation

r1 = Orientation.DEG_90
r2 = Orientation.DEG_180
combined = r1 + r2          # DEG_270
inverse = -r1               # DEG_270
diff = r2 - r1              # DEG_90
steps = r1.steps             # 1
from_steps = Orientation.from_steps(3)  # DEG_270
```

## API Reference

### `Orientation`

IntEnum: `DEG_0 (0)`, `DEG_90 (90)`, `DEG_180 (180)`, `DEG_270 (270)`.

Supports `+`, `-`, and negation with modular arithmetic (mod 360). The `steps` property returns 0-3 (number of 90-degree increments).

### `PieceType`

IntEnum: `INNER (0)`, `EDGE (1)`, `CORNER (2)`. Based on the number of flat edges.

### `OrientedPieceType`

Frozen Pydantic model combining `piece_type: PieceType` and `orientation: Orientation`. Used for both detected piece classification and grid slot requirements.

Canonical conventions:

- CORNER: flat edges on TOP + LEFT at DEG_0
- EDGE: flat edge on TOP at DEG_0
- INNER: no flat edges, orientation is arbitrary

## Related Modules

- [`grid/orientation_utils`](orientation.md) - utility functions for detection and rotation
- [`grid/grid_model`](grid_model.md) - computes `OrientedPieceType` per slot
- [`puzzle/piece`](../puzzle/piece.md) - stores detected `OrientedPieceType`
