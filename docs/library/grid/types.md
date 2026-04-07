# `grid/types`

> Module: `src/snap_fit/grid/types.py`
> Related tests: `tests/grid/`

## Purpose

Defines `GridPos`, a frozen Pydantic model representing a row/column position in the puzzle grid. Hashable for use as dict keys and set members.

## Usage

```python
from snap_fit.grid.types import GridPos

pos = GridPos(ro=2, co=3)
print(pos)       # "(2, 3)"
print(pos.ro)    # 2
print(pos.co)    # 3

# Hashable - can be used as dict key
grid_map = {pos: "some_value"}
```

## API Reference

### `GridPos`

Frozen Pydantic model. Fields: `ro: int` (row, 0-based), `co: int` (column, 0-based).

## Related Modules

- [`grid/grid_model`](grid_model.md) - uses `GridPos` for all position references
- [`grid/placement_state`](placement_state.md) - maps `GridPos` to placed pieces
