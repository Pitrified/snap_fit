# `puzzle/puzzle_generator`

> Module: `src/snap_fit/puzzle/puzzle_generator.py`
> Related tests: `tests/puzzle/`

## Purpose

Generates jigsaw puzzle geometry as SVG. Ported from a JavaScript implementation. Produces deterministic puzzles with interlocking tab/slot edges defined as cubic Bezier curves.

## Usage

### Minimal example

```python
from snap_fit.puzzle.puzzle_config import PuzzleConfig
from snap_fit.puzzle.puzzle_generator import PuzzleGenerator

config = PuzzleConfig(tiles_x=5, tiles_y=4, seed=42)
gen = PuzzleGenerator(config)

pieces = gen.generate()
print(f"Generated {len(pieces)} pieces")

# Get full puzzle SVG
svg = gen.to_svg()

# Get SVG for a single piece
piece_svg = gen.piece_to_svg(row=0, col=0, include_label=True)
```

## API Reference

### `PuzzleGenerator`

Creates puzzle pieces with Bezier-curve edges.

- `generate()` - returns `list[PuzzlePiece]` (cached after first call)
- `to_svg()` - full puzzle as one SVG string
- `piece_to_svg(row, col, ...)` - individual piece SVG

### Supporting models

- `PuzzlePiece` - Pydantic model with row, col, label, four `BezierEdge` objects, and bounds
- `BezierEdge` - list of `BezierSegment` objects and an `EdgeType` (FLAT, TAB_IN, TAB_OUT)
- `BezierSegment` - four control points defining a cubic Bezier curve
- `SeededRandom` - deterministic RNG matching the original JS implementation

## Related Modules

- [`puzzle/puzzle_config`](puzzle_config.md) - `PuzzleConfig` that drives generation
- [`puzzle/puzzle_rasterizer`](puzzle_rasterizer.md) - converts SVG output to numpy arrays
- [`puzzle/puzzle_sheet`](puzzle_rasterizer.md) - composes pieces onto printable sheets
