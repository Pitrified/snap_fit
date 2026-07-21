# `puzzle/sheet`

> Module: `src/snap_fit/puzzle/sheet.py`
> Related tests: `tests/puzzle/`

## Purpose

A `Sheet` represents a single photograph containing multiple puzzle pieces. On initialization, it loads the image, preprocesses it (blur, grayscale, threshold, erosion, dilation), finds contours, filters by area, and builds `Piece` objects.

Preprocessing parameters live in a `SheetPreprocessConfig`, which also carries an optional HSV background mask for colored (green) boards.

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

### Tuning preprocessing, or masking a green background

```python
from snap_fit.config.aruco.sheet_aruco_config import BackgroundMaskConfig
from snap_fit.config.aruco.sheet_aruco_config import SheetPreprocessConfig

# Override any previously hardcoded parameter
preprocess = SheetPreprocessConfig(threshold=140, blur_kernel_size=15)

# Or mask out a green board background instead of thresholding on brightness
preprocess = SheetPreprocessConfig(
    background_mask=BackgroundMaskConfig(enabled=True)
)
sheet = Sheet(img_fp=photo_fp, min_area=5_000, preprocess=preprocess)
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
| `slot_grid` | `SlotGrid \| None` | `None` | Assigns slot labels to piece centroids |
| `crop_offset` | `int` | `0` | Offset from board space to cropped-sheet space |
| `preprocess` | `SheetPreprocessConfig \| None` | `None` | Preprocess parameters; `None` uses behavior-preserving defaults |

Key attributes:

- `pieces: list[Piece]` - detected pieces
- `img_orig` - original color image
- `img_bw` - preprocessed binary image
- `preprocess_config` - the `SheetPreprocessConfig` in use
- `regions` - bounding rectangles of all pieces

### Preprocess pipeline

`preprocess()` runs blur, then a binarization step, then erosion, dilation, and a color flip
producing `img_bw` (pieces white, background black).

The binarization step is where the background mask applies. With no mask it is
grayscale plus a fixed threshold. With `background_mask.enabled`, an HSV in-range mask replaces
it, in one of two modes:

| Mode | Behavior |
|------|----------|
| `as_threshold` (default) | The in-range mask is used directly as the binary |
| `flatten_to_white` | Masked pixels are painted white, then the normal grayscale + threshold runs |

Both keep the same polarity, so the surrounding steps are unchanged.

## Common Pitfalls

- **Processing happens in `__init__`**: The entire pipeline (load, preprocess, find pieces) runs during construction. For large images this can be slow.
- **The default threshold assumes a bright background**: 130 works for white-background photos. On a green board the background luminance sits near that threshold and the whole sheet can merge into one contour, so a green board needs `background_mask` enabled rather than a threshold tweak.
- **min_area filtering**: Pieces with contour area below `min_area` are silently discarded. If you are missing pieces, try lowering this value. The `80_000` default suits full-resolution datasets; pieces on a rectified board sheet are far smaller (roughly 10k-16k px²).
- **A mask value floor that is too low erodes pieces quietly**: pieces lit by a colored background reflect its light and share its hue, so only brightness separates them. Too low a `lower_hsv` value floor keeps piece counts plausible while shrinking every piece. See [Green background boards](../../guides/green_background.md).

## Related Modules

- [`puzzle/piece`](piece.md) - the `Piece` objects created by `Sheet.build_pieces()`
- [`puzzle/sheet_aruco`](sheet_aruco.md) - perspective-corrected sheet loading via ArUco markers
- [`puzzle/sheet_manager`](sheet_manager.md) - manages collections of sheets
- [`image/process`](../image/process.md) - image preprocessing functions used by `Sheet.preprocess()`
