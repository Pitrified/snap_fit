# `puzzle/sheet_aruco`

> Module: `src/snap_fit/puzzle/sheet_aruco.py`
> Related tests: `tests/puzzle/`

## Purpose

`SheetAruco` wraps ArUco marker detection and perspective correction into a single loader that produces a rectified `Sheet`. When photographed puzzle sheets have ArUco markers on the border, this class detects them, computes a homography, warps the image to remove perspective distortion, and crops the marker margins.

## Usage

### Minimal example

```python
from pathlib import Path
from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig
from snap_fit.puzzle.sheet_aruco import SheetAruco

# Load config from JSON
config = SheetArucoConfig.model_validate_json(
    Path("data/oca/oca_SheetArucoConfig.json").read_text()
)
aruco = SheetAruco(config)

# Load and rectify a single sheet
sheet = aruco.load_sheet(Path("data/oca/sheets/photo_01.jpg"))
print(f"Detected {len(sheet.pieces)} pieces after rectification")
```

### As a loader function for SheetManager

```python
manager = SheetManager()
manager.add_sheets(
    folder_path=Path("data/oca/sheets/"),
    pattern="*.jpg",
    loader_func=aruco.load_sheet,
)
```

## API Reference

### `SheetAruco`

Perspective-correcting sheet loader.

Constructor: `SheetAruco(config: SheetArucoConfig)` - the config embeds detector and board parameters.

Key method: `load_sheet(img_fp: Path) -> Sheet` - loads, rectifies, crops, and returns a `Sheet` with the corrected image.

The `crop_margin` is automatically computed from board parameters (marker_length + margin + rect_margin) unless explicitly set in the config.

## Common Pitfalls

- **Fallback to original**: If ArUco detection fails (e.g., markers obscured), the original uncorrected image is used with a warning. Piece detection may be less accurate.
- **Config JSON naming convention**: Config files are expected at `data/{tag}/{tag}_SheetArucoConfig.json`.

## Related Modules

- [`puzzle/sheet`](sheet.md) - the `Sheet` produced by `load_sheet()`
- [`aruco/detector`](../aruco/detector.md) - the underlying ArUco detection and rectification
- [`config`](../config/index.md) - `SheetArucoConfig`, `ArucoDetectorConfig`, `ArucoBoardConfig`
