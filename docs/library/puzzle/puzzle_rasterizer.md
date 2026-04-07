# `puzzle/puzzle_rasterizer`

> Module: `src/snap_fit/puzzle/puzzle_rasterizer.py`
> Related tests: `tests/puzzle/`

## Purpose

Converts SVG puzzle drawings into OpenCV-compatible BGR numpy arrays using cairosvg. Handles DPI scaling, RGBA-to-BGR conversion, and background compositing.

## Usage

### Minimal example

```python
from snap_fit.puzzle.puzzle_rasterizer import PuzzleRasterizer

rasterizer = PuzzleRasterizer(dpi=300)

# Rasterize an SVG string
img = rasterizer.rasterize(svg_string)
print(f"Output shape: {img.shape}")  # (height, width, 3) BGR

# Save to file
rasterizer.save(img, "output.png")
```

## API Reference

### `PuzzleRasterizer`

- `rasterize(svg, background_color="white")` - SVG string to BGR numpy array
- `save(img, filepath)` - save image to disk via OpenCV

The `scale` attribute (pixels per mm) is computed from DPI: `dpi / 25.4`.

## Related Modules

- [`puzzle/puzzle_generator`](puzzle_generator.md) - produces the SVG input
- [`puzzle/puzzle_config`](puzzle_config.md) - `SheetLayout.dpi` controls rasterization resolution
