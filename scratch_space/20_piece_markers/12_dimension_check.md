# Dimension check: slot grid and QR strip vs ArUco markers

Debug notebook: `scratch_space/20_piece_markers/00_sample.ipynb`, cell 35.

## 1. Board config (defaults)

| Parameter          | Value |
| ------------------ | ----- |
| markers_x          | 5     |
| markers_y          | 7     |
| marker_length      | 100   |
| marker_separation  | 100   |
| margin             | 20    |
| border_bits        | 1     |
| stride             | 200   |
| board_dimensions() | 920 x 1320 |

Formula:

```
w = markers_x * marker_length + (markers_x - 1) * marker_separation + margin
  = 5*100 + 4*100 + 20 = 920
h = markers_y * marker_length + (markers_y - 1) * marker_separation + margin
  = 7*100 + 6*100 + 20 = 1320
```

## 2. Region layout (as currently computed)

| Region         | x0  | y0   | x1  | y1   | W   | H    |
| -------------- | --- | ---- | --- | ---- | --- | ---- |
| Board          | 0   | 0    | 920 | 1320 | 920 | 1320 |
| Left ring band | 0   | 0    | 120 | 1320 | 120 | 1320 |
| Right ring band| 820 | 0    | 920 | 1320 | 100 | 1320 |
| Top ring band  | 0   | 0    | 920 | 120  | 920 | 120  |
| Bottom ring band| 0  | 1220 | 920 | 1320 | 920 | 100  |
| Interior       | 120 | 120  | 820 | 1220 | 700 | 1100 |
| Piece area     | 120 | 120  | 820 | 1100 | 700 | 980  |
| QR strip       | 120 | 1100 | 820 | 1220 | 700 | 120  |

Ring band width:
- Left/Top: `margin + marker_length` = 120 px
- Right/Bottom: `marker_length` = 100 px
- **20 px asymmetry** - margin is added only once in `board_dimensions()`.

## 3. Root cause: bilateral margin in OpenCV

`Board.generateImage(size, None, margin, border_bits)` treats `margin` as a **bilateral** margin (applied to BOTH sides). The board_dimensions formula only adds margin once (left/top), so the image is too small and OpenCV **scales down** the grid to fit.

### Measured scale factors

OpenCV fits object-space extent into `image_size - 2*margin`:

```
x_scale = (920 - 2*20) / (5*100 + 4*100) = 880 / 900 = 0.97778
y_scale = (1320 - 2*20) / (7*100 + 6*100) = 1280 / 1300 = 0.98462
```

### Marker position drift (verified from pixel scan)

| Grid row | Expected y-start | Actual y-start | Shift | Expected y-end | Actual y-end | Shift |
| -------- | ---------------- | -------------- | ----- | -------------- | ------------ | ----- |
| 1        | 220              | 217            | -3    | 320            | 315          | -5    |
| 3        | 620              | 611            | -9    | 720            | 709          | -11   |
| 5        | 1020             | 1005           | -15   | 1120           | 1103         | -17   |
| 6        | 1220             | 1202           | -18   | 1320           | 1300         | -20   |

The shift follows: `actual = margin + grid_pos * scale`, confirmed to sub-pixel accuracy:
- Row 6: `20 + 6*200*0.98462 = 1201.5` - actual 1202
- Row 5: `20 + 5*200*0.98462 = 1004.6` - actual 1005
- Row 3: `20 + 3*200*0.98462 = 610.8` - actual 611
- Row 1: `20 + 1*200*0.98462 = 216.9` - actual 217

Right-side markers (x-scale): col 4 expected x=820, actual x=802.
`20 + 4*200*0.97778 = 802.2` - actual 802.

Rendered marker size is `~98 px` instead of 100 (both x and y scaled).

## 4. Measured overlaps

### 4a. Marker pixels inside interior (13,226 total)

Side markers (cols 0, 4) at rows 1-5 bleed into the interior through the right boundary. The right-side marker at col 4 renders starting at x=802, which is 18 px inside the interior boundary (x=820).

At each side marker row, 13-18 marker pixels per scanline appear at x=[802, 820) inside the interior.

### 4b. Marker pixels inside piece area (7,796 total)

Same mechanism as 4a, affecting the piece area region at rows 1-4 side markers.

### 4c. Marker pixels inside QR strip (5,430 total)

Two sources:
1. **Row 5 side markers** (col 4): 18 px/row at y=1100-1102, x=[802, 820). These markers end at y=1103 instead of expected y=1120, overlapping the QR strip top by 3 rows.
2. **Row 6 bottom markers** (cols 1-4): Starting at y=1202 (18 px early), present at y=1202-1219 inside the QR strip bottom. 264-312 marker pixels per row.

Specific bottom marker bleeding into QR strip:

```
y=1202-1214: 312 marker px/row (full marker borders of bottom row cols 1-4)
y=1215-1219: 264 marker px/row (inner pattern bits)
```

Marker x-runs at y=1270 inside QR strip:
- x=[216, 314] (bottom marker col 1)
- x=[411, 509] (bottom marker col 2)
- x=[607, 705] (bottom marker col 3)
- x=[802, 820] (right side marker col 4)

### 4d. Text line position

- Text baseline: y=1096
- Piece area bottom: y=1100
- Text top approx: y=1084
- Text is safely inside the gap between piece area and QR strip. **No overlap.**

## 5. Dimension computation chain

```
board_dimensions()
  w = markers_x * ml + (markers_x-1) * ms + margin          # 920 - WRONG: should be + 2*margin
  h = markers_y * ml + (markers_y-1) * ms + margin          # 1320

generateImage((w, h), None, margin, border_bits)
  actual_scale_x = (w - 2*margin) / grid_extent_x           # 0.978 (not 1.0!)
  actual_scale_y = (h - 2*margin) / grid_extent_y           # 0.985 (not 1.0!)

SlotGrid.__init__()
  ring_start = margin + ml                                   # 120
  interior_x0 = ring_start                                   # 120
  interior_x1 = board_w - ml                                 # 820 - WRONG: should account for right margin
  interior_y1 = board_h - ml                                 # 1220
  qr_strip_h = ring_start                                    # 120
  piece_area_y1 = interior_y1 - qr_strip_h                  # 1100

SheetMetadataEncoder._strip_region()
  x1 = board_w - ml                                          # 820 - same issue
  y1 = board_h - ml                                          # 1220
  y0 = y1 - ring_start                                       # 1100
```

Every consumer of `board_dimensions()` assumes the right/bottom edge of the outermost marker is at `board_size - marker_length`, but the actual rendered position is shifted inward by the missing margin.

## 6. Fix plan

### Option A: Fix `board_dimensions()` to use bilateral margin (recommended)

Change `ArucoBoardConfig.board_dimensions()`:

```python
w = markers_x * marker_length + (markers_x - 1) * marker_separation + 2 * margin
h = markers_y * marker_length + (markers_y - 1) * marker_separation + 2 * margin
# New: 940 x 1340
```

This makes `scale = 1.0` in both axes. Markers render exactly where the arithmetic predicts. No bleeding.

Updated interior bounds (SlotGrid + SheetMetadataEncoder):

```python
ring_start = margin + marker_length              # 120
interior_x0 = ring_start                          # 120
interior_x1 = board_w - ring_start                # 940 - 120 = 820
interior_y1 = board_h - ring_start                # 1340 - 120 = 1220
```

The formula for `_interior_x1` and `_interior_y1` must change to `board_w - ring_start` (instead of `board_w - marker_length`) so that the right/bottom ring bands are symmetric with the left/top.

Files to edit:
1. `src/snap_fit/config/aruco/aruco_board_config.py` - `board_dimensions()`
2. `src/snap_fit/aruco/slot_grid.py` - `_interior_x1`, `_interior_y1`
3. `src/snap_fit/aruco/sheet_metadata.py` - `_strip_region()` x1 and y1

### Option B: Shrink interior bounds to dodge actual marker pixels

Add a safety inset to the interior boundaries (e.g., 20 px inward from each side). Avoids changing board size but wastes 20 px on two sides.

**Not recommended** - fragile and doesn't fix the fundamental dimension mismatch.

### After fix: verify

- Re-run cell 35 with the updated code
- Confirm: 0 marker pixels in interior, piece area, and QR strip
- Confirm: scale_x = scale_y = 1.0
- Run full test suite: `uv run pytest && uv run ruff check . && uv run pyright`

## 7. Impact analysis

Changing `board_dimensions()` affects:
- Board image size (920x1320 to 940x1340)
- All code that uses `board_dimensions()` downstream
- Cached board images and ArUco calibration data (would need regeneration)
- Physical print dimensions (slightly larger board)
- Tests that assert specific pixel coordinates
