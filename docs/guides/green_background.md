# `Green background boards`

> Type: `functional`
> Audience: operators capturing puzzle sheets, contributors touching preprocessing

## Overview

Puzzle pieces are hard to separate from a white background when the pieces themselves are pale.
A board can instead be rendered with a **green background**, and sheet preprocessing can mask that
green out, leaving the pieces as clean foreground regardless of their own brightness.

Boards are **displayed on a screen and photographed**, never printed.
The screen background is bright and saturated, which is what makes the mask reliable.
Each board carries a QR code with its sheet identity and a labelled slot grid (`A1`, `B3`, ...),
so an operator can photograph a sheet and record "piece X was in B3 of sheet 7" by hand.

## Prerequisites

- A generated board set (see step 1) under `data/aruco_boards/{board_config_id}/`
- A screen to display the board and a camera to photograph it
- [`puzzle/sheet_aruco`](../library/puzzle/sheet_aruco.md) for the ingest side

## Steps

### 1. Generate the board set

Board generation is the operator entry point. `background_preset="green"` switches the render, and
the saved ingest config picks up the matching background mask automatically.

```python
from snap_fit.aruco.board_config_resolver import derive_background_mask
from snap_fit.aruco.board_image_composer import BoardImageComposer
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig
from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig

board_config = ArucoBoardConfig(background_preset="green")
sheet_config = SheetArucoConfig(
    min_area=5_000,  # match the piece scale of your board, see Pitfalls
    detector=ArucoDetectorConfig(board=board_config),
    metadata_zone=metadata_zone,
)
# Green/blue presets auto-enable the mask, so the saved JSON carries it.
sheet_config = derive_background_mask(sheet_config)

composer = BoardImageComposer(board_config, metadata_zone)
img = composer.compose(metadata)  # one SheetMetadata per sheet
```

A runnable end-to-end version lives in
`scratch_space/23_green_background/generate_green_board.py`. It writes the sheet PNGs plus both
config JSONs and verifies the QR round-trips:

```bash
python scratch_space/23_green_background/generate_green_board.py
```

Set `TOTAL_SHEETS` to the number of boards you need. Each sheet gets its own `sheet_index` inside
the QR payload, which is what makes a photo traceable later. A 4x3 slot grid holds 12 pieces per
sheet, so a 1500-piece puzzle needs on the order of 125 sheets.

### 2. Display and photograph

Open a sheet PNG full screen and photograph it with the pieces placed on the slots. Angle and zoom
are forgiving: the ArUco ring is what rectifies the image, and it has been verified to detect all
20 markers at 1x/2x/5x zoom, straight on and from the side.

### 3. Ingest by decoding the QR

The ingest driver never rebuilds the config by hand. It decodes the QR, resolves the stored config
by `board_config_id`, and loads the sheet:

```python
from snap_fit.aruco.board_config_resolver import load_sheet_config_by_id
from snap_fit.aruco.sheet_metadata import SheetMetadataDecoder
from snap_fit.image.utils import load_image
from snap_fit.puzzle.sheet_aruco import SheetAruco

metadata = SheetMetadataDecoder().decode(load_image(photo_fp))
config = load_sheet_config_by_id(metadata.board_config_id)  # mask already enabled
sheet = SheetAruco(config).load_sheet(photo_fp)
```

A runnable version is `scratch_space/23_green_background/ingest_green_sheet.py`:

```bash
python scratch_space/23_green_background/ingest_green_sheet.py path/to/photo.jpg
```

### 4. Read the tracking key

Each detected piece carries the slot label derived from its centroid, and the sheet carries the
decoded identity. Together they are the manual annotation key:

```python
print(sheet.metadata.sheet_index)          # which board this photo shows
for piece in sheet.pieces:
    print(piece.label)                     # "A1", "B3", ...
```

## Verification

Run the green pipeline tests, which cover detection on a green board and piece extraction under
both mask modes:

```bash
python -m pytest tests/aruco/test_green_board_pipeline.py tests/puzzle/test_sheet_preprocess.py -q
```

On a real capture, a correct ingest reports one piece per occupied slot, each with a distinct
label. Measured on the reference `greendemo` captures: 12 pieces, labels `A1`-`D3`, on every photo.

## Pitfalls

- **`min_area` is the usual reason for zero pieces**: the global default is `80_000`, tuned for
  older full-resolution datasets. On a rectified board sheet the pieces measure roughly
  10k-16k px², so everything is filtered out. Set `min_area` on the board's saved config
  (the reference board uses `5_000`). If pieces are missing, lower it first.
- **The value floor of the mask matters more than the hue**: pieces resting on a lit screen reflect
  board light, so they share the background *hue* (70-81). Only brightness separates them: the
  background reads V 186-212 while glare-lit pieces reach V 42-61. The default `lower_hsv` value
  floor of `100` sits between them. Lowering it toward 40 does not fail loudly, it silently erodes
  every piece by roughly 60% of its area and can drop one entirely. Raising it past ~140 lets dim
  background regions merge into the pieces. Verified safe band: 60-120.
- **Without the mask a green sheet collapses**: green's grayscale luminance sits near the default
  threshold of 130, so a plain threshold merges the whole sheet into a single contour. A green
  board is not usable with the mask disabled.
- **Mask modes are usually equivalent**: `as_threshold` (default) and `flatten_to_white` produce
  identical output when the pieces are dark. `flatten_to_white` only diverges for pale pieces,
  where repainting the background white keeps the normal threshold path meaningful.
- **A board folder may have no stored ingest config**: older folders hold only an
  `_ArucoBoardConfig.json`. `load_sheet_config_by_id` raises `BoardConfigNotFoundError` so the
  driver can fall back rather than silently guess.

## Related

- [`puzzle/sheet`](../library/puzzle/sheet.md) - preprocessing and the background mask
- [`puzzle/sheet_aruco`](../library/puzzle/sheet_aruco.md) - rectifying loader used at ingest
- [`aruco/board`](../library/aruco/board.md) - board generation and the background preset
- [`config`](../library/config/index.md) - `SheetPreprocessConfig`, `BackgroundMaskConfig`
- [Coordinate spaces](coordinate_spaces.md) - how slot labels map to piece centroids
