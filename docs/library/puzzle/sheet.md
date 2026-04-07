# `puzzle/sheet`

> Module: `src/snap_fit/puzzle/sheet.py`
> Related tests: `tests/puzzle/`

## Purpose

A `Sheet` represents a single photograph containing multiple puzzle pieces. On initialization, it loads the image, preprocesses it (blur, grayscale, threshold, erosion, dilation), finds contours, filters by area, and builds `Piece` objects.

## Usage

### Minimal example

```python
from pathlib import Path
from snap_fit.puzzle.sheet import Sheet

sheet = Sheet(img_fp=Path("data/sample/sheet_01.jpg"), min_area=80_000)

print(f"Found {len(sheet.pieces)} pieces")
for piece in sheet.pieces:
    print(f"  {piece.piece_id}: area={piece.contour.area}")
```

### With a pre-loaded image

```python
import cv2
from snap_fit.puzzle.sheet import Sheet

img = cv2.imread("photo.jpg")
sheet = Sheet(img_fp=Path("photo.jpg"), image=img, sheet_id="my_sheet")
```

## API Reference

### `Sheet`

Processes a photograph into a list of `Piece` objects.

Constructor parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `img_fp` | `Path` | required | Path to the image file |
| `min_area` | `int` | `80_000` | Minimum contour area to keep |
| `image` | `np.ndarray \| None` | `None` | Pre-loaded image (skips file load) |
| `sheet_id` | `str \| None` | `None` | Custom ID (defaults to filename stem) |

Key attributes:

- `pieces: list[Piece]` - detected pieces
- `img_orig` - original color image
- `img_bw` - preprocessed binary image
- `threshold` - binary threshold value (default 130)
- `regions` - bounding rectangles of all pieces

## Common Pitfalls

- **Processing happens in `__init__`**: The entire pipeline (load, preprocess, find pieces) runs during construction. For large images this can be slow.
- **Threshold is hard-coded**: The default threshold of 130 works well for white-background puzzle photos but may need adjustment for different lighting conditions.
- **min_area filtering**: Pieces with contour area below `min_area` are silently discarded. If you are missing pieces, try lowering this value.

## Related Modules

- [`puzzle/piece`](piece.md) - the `Piece` objects created by `Sheet.build_pieces()`
- [`puzzle/sheet_aruco`](sheet_aruco.md) - perspective-corrected sheet loading via ArUco markers
- [`puzzle/sheet_manager`](sheet_manager.md) - manages collections of sheets
- [`image/process`](../image/process.md) - image preprocessing functions used by `Sheet.preprocess()`
