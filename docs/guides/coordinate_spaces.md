# Coordinate Spaces and Image Cropping

> Type: `technical`
> Audience: developers working on piece image cropping, slot assignment, or visualization

## Overview

The snap_fit pipeline processes photos through several stages, each producing a
different pixel coordinate space. Understanding these spaces is essential when
working on piece image cropping, slot grid assignment, piece image endpoints, or
debug overlays. Mismatches between spaces are the root cause of wrong crops and
off-by-one slot errors.

## Prerequisites

- Familiarity with [puzzle/sheet_aruco](../library/puzzle/sheet_aruco.md) (ArUco rectification)
- Familiarity with [puzzle/piece](../library/puzzle/piece.md) (`from_contour()` and `sheet_origin`)
- Familiarity with [image/utils](../library/image/index.md) (`pad_rect`, `cut_rect_from_image`)

## The Four Coordinate Spaces

| Space | Origin | Size (defaults) | Where used |
|-------|--------|-----------------|------------|
| **Board image** | Top-left of the printed board PNG | 940 x 1340 | `SlotGrid` boundaries, `BoardImageComposer`, ring-start coords |
| **Object coord** | Outer corner of first ArUco marker | 900 x 1300 | OpenCV board, used inside `correct_perspective` |
| **Rectified** | Top-left of perspective-corrected image | 1000 x 1400 | Output of `aruco_detector.rectify()` |
| **Cropped sheet** | Top-left after symmetric crop + QR strip crop | 660 x 940 | `sheet.img_orig`, piece centroids, contour detection |

### Default Configuration Values

```
marker_length = 100
margin = 20
rect_margin = 50
board_w = 940, board_h = 1340
ring_start = margin + marker_length = 120
crop_margin = marker_length + margin + rect_margin = 170
```

## Transformation Chain

```
Original Photo (arbitrary resolution, perspective-distorted)
    |
    v  [aruco_detector.rectify() - perspective correction]
Rectified Image (board_w + 2*rect_margin  x  board_h + 2*rect_margin)
    |          e.g. 1040 x 1440 with rect_margin=50
    |
    v  [symmetric crop: remove crop_margin from all 4 sides]
Cropped Sheet Image (660 x 1060)
    |
    v  [QR strip crop: remove ring_start from bottom, if metadata_zone set]
Final Cropped Sheet (660 x 940)
    |
    v  [Contour detection operates in this space]
    |
    v  [Piece.from_contour() - pad_rect + cut_rect_from_image]
Piece-Local Image (padded bounding box around contour)
```

## Key Offset: `crop_offset`

The `crop_offset` bridges **board-image** and **cropped-sheet** pixel coordinates:

```
crop_offset = crop_margin - rect_margin + margin
            = marker_length + 2 * margin
            = 140 px  (with defaults)

board_pixel   = cropped_pixel + crop_offset
cropped_pixel = board_pixel - crop_offset
```

`crop_offset` is stored on `Sheet.crop_offset` and is computed in
`SheetAruco.load_sheet()`. It is used in `Sheet.build_pieces()` to convert
contour centroids from cropped-sheet space to board-image space before passing
them to `SlotGrid.slot_for_centroid()`.

## Piece Image Cropping Pipeline

When a piece is created from a contour via `Piece.from_contour()`:

```python
region = contour.region                       # (x, y, w, h) in cropped-sheet space
region_pad = pad_rect(region, pad, full_img_bw)  # padded rect in cropped-sheet space
img_orig_cut = cut_rect_from_image(sheet_img, region_pad)
contour_cut = contour.translate(-region_pad[0], -region_pad[1])
sheet_origin = (region_pad[0], region_pad[1])  # top-left of padded rect
```

Three coordinate values are persisted in `PieceRecord`:

| Field | Space | Meaning |
|-------|-------|---------|
| `sheet_origin` | Cropped sheet | Top-left `(x, y)` of the padded bounding box |
| `contour_region` | Piece-local | Bounding box `(x, y, w, h)` of the contour within the piece image |
| `padded_size` | N/A (dimensions) | `(width, height)` of the padded piece image |

### Reconstructing the Crop from Stored Data

To re-extract a piece image from the cropped sheet image:

```python
x0, y0 = piece_record.sheet_origin
pw, ph = piece_record.padded_size
crop = sheet_img[y0 : y0 + ph, x0 : x0 + pw]
```

**Important:** The sheet image used here must be the **processed** (rectified
and cropped) sheet image, NOT the original photo. The original photo is in a
completely different coordinate space (un-rectified, un-cropped). The processed
sheet images are saved at ingest time to `cache/{tag}/sheets/{sheet_id}.jpg`.

### Why Not Use `2 * cx + cw` for Width?

The formula `padded_w = 2 * contour_region.x + contour_region.w` only works when
`pad_rect` applies symmetric padding without clamping. For pieces near the sheet
edges, `pad_rect` clamps the origin to `(0, 0)` without reducing the width,
producing asymmetric padding. In those cases the formula gives the wrong
dimensions.

## SlotGrid and Coordinate Conversion

`SlotGrid` always works in **board-image** space. When assigning pieces to slots
in `Sheet.build_pieces()`, contour centroids (in cropped-sheet space) must be
converted first:

```python
cx, cy = contour.centroid                  # cropped-sheet space
cx_board = cx + sheet.crop_offset          # board-image space
cy_board = cy + sheet.crop_offset
slot = slot_grid.slot_for_centroid(cx_board, cy_board)
```

For visualization on the cropped sheet image, slot centers must be converted
the other way:

```python
for bx, by in slot_grid.slot_centers():    # board-image space
    cv2.circle(sheet_img, (bx - crop_offset, by - crop_offset), 14, ...)
```

## Pitfalls

- **Loading the original photo instead of the processed sheet:** The original
  photo has a different resolution and perspective. Coordinates from the
  cropping pipeline cannot be applied to it. Always load the processed sheet
  image from cache when serving piece crops.
- **Symmetric crop assumption:** `crop_offset` is a single scalar. It only
  works when the symmetric crop margin is the same on all sides. If
  `crop_margin` is ever made asymmetric, `crop_offset` needs to become a
  per-side tuple.
- **Edge clamping in `pad_rect`:** When a piece's bounding box is near the
  sheet edge, `pad_rect` clamps the origin but does not reduce the width (it
  only clamps the right/bottom via `min(w, img_w - x)`). This produces
  asymmetric padding for edge pieces.

## Related

- [puzzle/sheet_aruco](../library/puzzle/sheet_aruco.md) - rectification and cropping
- [puzzle/piece](../library/puzzle/piece.md) - `from_contour()` and `sheet_origin`
- [puzzle/sheet](../library/puzzle/sheet.md) - `build_pieces()` and `crop_offset`
- [image/contour](../library/image/contour.md) - `Contour`, `region`, `centroid`
