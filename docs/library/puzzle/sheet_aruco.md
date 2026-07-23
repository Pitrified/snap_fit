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

The `crop_margin` is automatically computed from board parameters (marker_length + rect_margin) unless explicitly set in the config. It deliberately excludes the board `margin`: the rectified image is in object coordinates, which already start at the first marker's outer corner, so the ring's inner edge is at `rect_margin + marker_length`. See [coordinate_spaces](../../guides/coordinate_spaces.md).

`SheetAruco.crop_offset` exposes the shift from cropped-sheet to board-image coordinates; with the computed `crop_margin` it equals `SlotGrid`'s ring_start.

`load_sheet()` passes `config.preprocess` through to the `Sheet` it builds, so preprocessing
parameters and the optional background mask travel inside the same config object. `SheetAruco`
never reads JSON from disk itself; the driver supplies a fully resolved config.

### Resolving the config from the photo

For sheets carrying QR metadata, the driver can resolve the config instead of hardcoding a path:

```python
from snap_fit.aruco.board_config_resolver import load_sheet_config_by_id
from snap_fit.aruco.sheet_metadata import SheetMetadataDecoder

metadata = SheetMetadataDecoder().decode(load_image(photo_fp))
config = load_sheet_config_by_id(metadata.board_config_id)
sheet = SheetAruco(config).load_sheet(photo_fp)
```

## Common Pitfalls

- **Fallback to original**: If ArUco detection fails (e.g., markers obscured), the original uncorrected image is used with a warning. Piece detection may be less accurate.
- **Config JSON naming convention**: Config files are expected at `data/{tag}/{tag}_SheetArucoConfig.json`. Board folders instead use `data/aruco_boards/{id}/{id}_SheetArucoConfig.json`, which is what `load_sheet_config_by_id` reads.
- **min_area travels with the config**: the `80_000` default filters out every piece on a rectified board sheet, where pieces measure roughly 10k-16k px². Set it on the saved config for that board.

## Related Modules

- [`puzzle/sheet`](sheet.md) - the `Sheet` produced by `load_sheet()`
- [`aruco/detector`](../aruco/detector.md) - the underlying ArUco detection and rectification
- [`aruco`](../aruco/index.md) - `board_config_resolver` for resolving a config from a decoded QR
- [`config`](../config/index.md) - `SheetArucoConfig`, `SheetPreprocessConfig`, `BackgroundMaskConfig`
- [Green background boards](../../guides/green_background.md) - colored-board capture workflow
