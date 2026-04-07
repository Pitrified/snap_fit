# `puzzle/puzzle_config`

> Module: `src/snap_fit/puzzle/puzzle_config.py`
> Related tests: `tests/puzzle/`

## Purpose

Pydantic configuration models for synthetic jigsaw puzzle generation and sheet layout. `PuzzleConfig` defines the puzzle geometry (dimensions, grid, tabs, jitter, labeling), while `SheetLayout` defines how generated pieces are arranged onto printable sheets.

## Usage

### Minimal example

```python
from snap_fit.puzzle.puzzle_config import PuzzleConfig, SheetLayout

config = PuzzleConfig(
    width=300.0,    # mm
    height=200.0,   # mm
    tiles_x=15,
    tiles_y=10,
    tab_size=0.2,
    seed=42,
)

print(f"Piece size: {config.piece_width:.1f} x {config.piece_height:.1f} mm")
print(f"Font size: {config.auto_font_size:.1f} mm")

layout = SheetLayout(sheet_width=297.0, sheet_height=210.0, dpi=300)
per_row, per_col = layout.pieces_per_sheet(config.piece_width, config.piece_height)
print(f"Fits {per_row}x{per_col} pieces per sheet")
```

## API Reference

### `PuzzleConfig`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `width` | `float` | `300.0` | Puzzle width in mm |
| `height` | `float` | `200.0` | Puzzle height in mm |
| `tiles_x` | `int` | `15` | Number of columns (min 2) |
| `tiles_y` | `int` | `10` | Number of rows (min 2) |
| `tab_size` | `float` | `0.2` | Tab size as fraction of piece (0.1-0.3) |
| `jitter` | `float` | `0.04` | Random edge jitter (0.0-0.25) |
| `seed` | `int` | `42` | Random seed for deterministic generation |

Computed fields: `piece_width`, `piece_height`, `letter_digits`, `number_digits`, `auto_font_size`.

### `PieceStyle`

Rendering style: `fill`, `stroke`, `stroke_width`, `label_color`.

### `SheetLayout`

A4-oriented layout config: `sheet_width`, `sheet_height`, `margin`, `piece_spacing`, `dpi`. Key method: `pieces_per_sheet(piece_width, piece_height)`.

## Related Modules

- [`puzzle/puzzle_generator`](puzzle_generator.md) - consumes `PuzzleConfig` to generate geometry
- [`puzzle/puzzle_rasterizer`](puzzle_rasterizer.md) - uses `SheetLayout.dpi` for rasterization
