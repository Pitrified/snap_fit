# Sheet crop and piece tracking

## Overview

Three related problems share the same root cause: the `crop_offset` between
board-image space and cropped-sheet space is not tracked or communicated.

Support script with coordinate verification: [16_support.py](16_support.py)
Generated annotated images: `16_board_annotated.png`, `16_after_aruco_crop.png`, `16_after_qr_crop.png`

---

## Coordinate spaces

There are four pixel coordinate spaces in the pipeline.

| Space         | Origin                                  | Size (defaults) | Usage                                               |
| ------------- | --------------------------------------- | --------------- | --------------------------------------------------- |
| Board image   | top-left of printed board PNG           | 940 x 1340      | `SlotGrid`, `BoardImageComposer`, ring_start coords |
| Object coord  | outer corner of first ArUco marker      | 900 x 1300      | OpenCV board, used inside `correct_perspective`     |
| Rectified     | top-left of perspective-corrected image | 1000 x 1400     | output of `aruco_detector.rectify()`                |
| Cropped sheet | top-left after ArUco ring crop          | 660 x 1060      | `sheet.img_orig`, piece centroids, contour coords   |

### Transformation between spaces (default config)

```
Default config:
  marker_length=100, margin=20, rect_margin=50
  board_w=940, board_h=1340
  ring_start = margin + marker_length = 120
  crop_margin = marker_length + margin + rect_margin = 170

board_pixel   <->  rectified_pixel    shift = +(rect_margin - margin) = +30
rectified_pixel <-> cropped_pixel    shift = -crop_margin = -170

crop_offset = crop_margin - (rect_margin - margin)
            = crop_margin - rect_margin + margin
            = 170 - 50 + 20 = 140 px
            = marker_length + 2*margin (invariant for the default formula)

board_pixel = cropped_pixel + crop_offset   (+140)
cropped_pixel = board_pixel - crop_offset   (-140)
```

### Interior and QR strip in each space

| Region          | Board image  | Cropped sheet |
| --------------- | ------------ | ------------- |
| Interior x      | [120, 820)   | [-20, 680)    |
| Interior y      | [120, 1220)  | [-20, 1080)   |
| Piece area y    | [120, 1100)  | [-20, 960)    |
| QR strip y      | [1100, 1220) | [960, 1080)   |
| QR strip height | 120 px       | 120 px        |

The negative values for interior start in cropped space confirm the entire
cropped image is usable (the ring was fully removed). But the QR strip rows
960-1080 are still present in the 660 x 1060 cropped image.

---

## Problem 1: QR strip not cropped out

### Where: `src/snap_fit/puzzle/sheet_aruco.py` - `SheetAruco.load_sheet()`

### What happens now

```python
# Lines 62-70 in sheet_aruco.py
if self.crop_margin > 0:
    h, w = img_final.shape[:2]
    img_final = img_final[
        self.crop_margin : h - self.crop_margin,
        self.crop_margin : w - self.crop_margin,
    ]
    lg.info(f"Cropped margin of {self.crop_margin} pixels.")
```

The symmetric crop removes `crop_margin = 170 px` from all four sides. This
strips the ArUco ring (100px marker + 20px margin + 50px rect_margin buffer)
but leaves the bottom metadata zone (QR codes + text) intact.

After the crop:

- Image size: 660 x 1060 px
- Piece area: y = 0..960 (960 px of content)
- QR strip: y = 960..1080 (120 px still present)
- Bottom gap: y = 1080..1060 - wait, no: 1080 > 1060 is impossible.

Actually: the piece-area bottom is at board y=1100, which maps to cropped y=960.
The interior bottom (ring_start from bottom) is at board y=1220, cropped y=1080.
But cropped image height is only 1060, so the last 20 px (ring gap) is already
trimmed. The QR strip (board y=1100..1220 -> cropped y=960..1080) partly extends
beyond the 1060 px image but the first 100px of it (y=960..1060) are visible.

Summary: the QR/text strip occupies roughly the bottom 100px of the current
cropped image and needs to be removed.

### Plan - add a conditional bottom-only crop

When `self.config.metadata_zone is not None`, after the symmetric crop add:

```python
if self.config.metadata_zone is not None:
    board_config = self.config.detector.board
    qr_strip_h = board_config.margin + board_config.marker_length  # = ring_start
    h_now = img_final.shape[0]
    img_final = img_final[:h_now - qr_strip_h, :]
    lg.info(f"Cropped QR strip ({qr_strip_h} px from bottom).")
```

Result: the final sheet image becomes 660 x 940 px, containing only the slot/piece area.

### Impact on crop_offset

The QR strip bottom crop is asymmetric (bottom only). It does NOT change the
crop_offset used to convert between board-image and cropped-sheet coordinates
for the X axis or the top of the image. The `crop_offset` remains 140 px for X
and for the Y top. Only the height of the image changes.

---

## Problem 2: Piece has no sheet-space origin

### Where: `src/snap_fit/puzzle/piece.py` - `Piece.from_contour()` and `Piece.__init__()`

### What happens now

```python
# In Piece.from_contour() (lines 101-115):
region = contour.region                            # (x, y, w, h) in SHEET space
region_pad = pad_rect(region, pad, full_img_bw)    # padded rect in SHEET space
img_orig_cut = cut_rect_from_image(full_img_orig, region_pad)
img_bw_cut   = cut_rect_from_image(full_img_bw, region_pad)

# Contour is translated to PIECE-LOCAL space:
contour_cut  = contour.translate(-region_pad[0], -region_pad[1])

c = cls(piece_id=piece_id, img_fp=img_fp,
        img_orig=img_orig_cut, img_bw=img_bw_cut, contour=contour_cut)
```

`region_pad[0:2]` = `(x, y)` (origin of padded rect in sheet space) is used
to translate the contour but is never stored on the resulting `Piece` object.

After construction:

- `piece.contour.centroid` returns `(local_cx, local_cy)` in piece-local coords
- There is no way to recover the sheet-space centroid `(local_cx + x, local_cy + y)`

In `Sheet.build_pieces()`, slot assignment correctly uses the original
`contour.centroid` (pre-translation, still in sheet space). But for debugging
and visualisation, the piece needs to exposing its own centroid in sheet space.

### What's lost

- Cannot draw piece centroids on the sheet image using `piece.contour.centroid`
  (notebook bug in `01_print_read_board.ipynb` Step 10, with UPDATE comment)
- Cannot compute board-image coords from a piece without external bookkeeping

### Plan - add `sheet_origin` to Piece

`sheet_origin` is always available when a piece is built from a real image via
`from_contour()`. Old cached databases are not a concern. Make it mandatory.

1. Change `Piece.__init__()` to accept `sheet_origin: tuple[int, int]` (required,
   no default) and store it as `self.sheet_origin = sheet_origin`.

2. In `Piece.from_contour()`, compute and pass it:

   ```python
   sheet_origin = (region_pad[0], region_pad[1])
   c = cls(..., sheet_origin=sheet_origin)
   ```

3. Add a `centroid_in_sheet` property:
   ```python
   @property
   def centroid_in_sheet(self) -> tuple[int, int]:
       cx, cy = self.contour.centroid
       return (cx + self.sheet_origin[0], cy + self.sheet_origin[1])
   ```

4. Add `sheet_origin: tuple[int, int]` to `PieceRecord` as a required field.
   Update `PieceRecord.from_piece(piece)` to read it and `to_piece()` / any
   reconstruction path to pass it. This makes debug overlays reproducible from
   the cache without reprocessing images.

---

## Problem 3: SlotGrid uses board-image coords; piece centroids are in cropped-sheet coords

### Where: `src/snap_fit/aruco/slot_grid.py` + `src/snap_fit/puzzle/sheet.py` + `src/snap_fit/puzzle/sheet_aruco.py`

### What happens now

**`SlotGrid.__init__()` computes boundaries in board-image space:**

```python
ring_start = board_config.margin + board_config.marker_length  # = 120
self._interior_x0 = ring_start   # 120  (board image)
self._interior_y0 = ring_start   # 120  (board image)
...
self._piece_area_y1 = self._interior_y1 - qr_strip_h  # 1100  (board image)
```

**`Sheet.build_pieces()` passes centroids in cropped-sheet space:**

```python
cx, cy = contour.centroid   # cropped-sheet coords, e.g. (242, 470)
slot = self.slot_grid.slot_for_centroid(cx, cy)
```

**`slot_for_centroid` compares cropped coords against board-image boundaries:**

```python
if not (self._interior_x0 <= cx < self._interior_x1):  # 120 <= 242 < 820 -> passes
    return None
col = int((cx - self._interior_x0) / self._slot_w)     # (242 - 120) / 175 = 0 (WRONG)
```

A piece in slot (1,1) at board-image (382, 610) appears as cropped (242, 470).
Current code assigns it to slot **(0, 1)**. Correct slot is **(1, 1)**.
The error is `crop_offset / slot_w = 140 / 175 ≈ 0.8` columns off, up to 1 slot wrong.

**`slot_centers()` returns board-image coords; notebook draws them on the cropped image:**

```python
# In 01_print_read_board.ipynb, visualise_sheet():
for x, y in grid.slot_centers():           # x, y in board-image space (e.g. 382, 610)
    cv2.circle(img, (x, y), 14, ...)       # img is sheet.img_orig = CROPPED space
    # -> dot drawn 140px to SE of correct position
```

### Root cause

`crop_offset = 140 px` (the shift between board-image and cropped-sheet coords)
is computed in `SheetAruco.load_sheet()` but is never stored anywhere or passed
to components that need it.

### Plan - propagate crop_offset

**Step A: Compute and store `crop_offset` on `Sheet`**

In `SheetAruco.load_sheet()`, after computing `crop_margin`:

```python
if self.crop_margin > 0:
    # ... existing symmetric crop ...
    crop_offset = int(self.crop_margin)  - (detector_cfg.rect_margin - board_cfg.margin)
    # = crop_margin - rect_margin + margin = marker_length + 2*margin = 140
else:
    crop_offset = 0
sheet = Sheet(..., crop_offset=crop_offset)
```

**Step B: Add `crop_offset: int` to `Sheet`**

`Sheet.__init__()` accepts and stores `self.crop_offset: int = crop_offset`.

**Step C: Fix `Sheet.build_pieces()` centroid lookup**

```python
if self.slot_grid is not None:
    cx, cy = contour.centroid              # cropped-sheet space
    cx_board = cx + self.crop_offset       # board-image space
    cy_board = cy + self.crop_offset       # board-image space
    slot = self.slot_grid.slot_for_centroid(cx_board, cy_board)
```

No changes to `SlotGrid` itself - it keeps working in board-image space.

**Step D: Fix notebook `slot_centers()` visualisation**

In `01_print_read_board.ipynb` `visualise_sheet()`:

```python
crop_off = sheet.crop_offset
for x, y in grid.slot_centers():
    cv2.circle(img, (x - crop_off, y - crop_off), 14, ...)  # shifted to cropped space
```

Or add a helper method `SlotGrid.slot_centers_in_cropped(crop_offset)` that does this
conversion once and returns ready-to-use pixel coords.

### Where crop_offset should live

- `Sheet.crop_offset: int` - natural owner; Sheet is already the handle for the
  cropped image, so knowing its own coordinate offset is appropriate.
- `SlotGrid` stays pure board-image-space; callers translate before/after.
- `Piece.sheet_origin` (from Problem 2) is also in cropped-sheet space and is
  consistent with `Sheet.crop_offset` being the bridge to board-image space
  for that piece: `board_cx = piece.sheet_origin[0] + piece.contour.centroid[0] + sheet.crop_offset`.

---

## Implementation order

1. **Problem 3A-B**: Add `crop_offset` to `Sheet` and `SheetAruco.load_sheet()` - no visible behaviour change yet.
2. **Problem 1**: Add QR strip bottom crop in `SheetAruco.load_sheet()` (conditional on `metadata_zone`).
3. **Problem 3C**: Fix `Sheet.build_pieces()` centroid lookup using `crop_offset`.
4. **Problem 2**: Add `sheet_origin` + `centroid_in_sheet` to `Piece.from_contour()`.
5. **Problem 3D**: Update notebook `visualise_sheet()` to subtract `crop_offset` from slot centres.
6. Add/update tests for each step.

---

## Open questions

- The `crop_offset` formula assumes a symmetric crop. If a user sets `crop_margin` manually to an asymmetric value, a single scalar offset is insufficient. For now, keep scalar (symmetric crop only); document the assumption.
- After Problem 1, the piece-area image is 660 x 940 for defaults. Does any downstream code assume a specific sheet image height? Verify via tests.

### Why does the piece area start at cropped y = -20?

This is not a legacy error. It is a direct consequence of the `crop_margin` formula:

```
In rectified space, the ring's inner edge is atscratch_space/20_piece_markers/16_sheet_cropping.md:
  ring_end_in_rectified = rect_margin + marker_length = 50 + 100 = 150 px

But crop_margin = marker_length + margin + rect_margin = 100 + 20 + 50 = 170 px

=> interior_start_in_cropped = ring_end_in_rectified - crop_margin
                              = 150 - 170 = -margin = -20 px
```

The `crop_margin` formula deliberately includes the board `margin` (20 px) as an extra
buffer to guarantee the ArUco ring is fully removed even accounting for the gap between
the edge of the image and the first marker. The cost is that the crop overshoots the
ring interior by exactly `margin` pixels on every side.

The same applies at the bottom after the QR strip crop: the piece-area bottom lands at
cropped y = 960, but the image height after the QR crop is 940, so the bottom 20 px of
the piece area are also clipped.

In practice this means pieces placed in the outermost `margin`-wide ring of the slot
grid could have their bounding contour clipped. With `margin = 20 px` and slot dimensions
of ~175 x 327 px this is negligible. Document this in `SheetAruco.load_sheet()` with a
comment. No code change needed.
