"""Support script for 16_sheet_cropping.md - coordinate verification.

Verifies the exact coordinate transformations through the pipeline stages:

  Board image space
    -> rect_margin shift (perspective warp output)
    -> crop_margin cut (ArUco ring removal)
    -> (planned) QR strip bottom cut

Demonstrates the coordinate mismatch bugs in their current form and the
expected corrected values.

Run with: uv run python scratch_space/20_piece_markers/16_support.py
"""

from __future__ import annotations

import cv2

from snap_fit.aruco.aruco_board import ArucoBoardGenerator
from snap_fit.aruco.slot_grid import SlotGrid
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig
from snap_fit.config.aruco.metadata_zone_config import SlotGridConfig

# ---------------------------------------------------------------------------
# Default config parameters (mirrors ArucoBoardConfig / ArucoDetectorConfig)
# ---------------------------------------------------------------------------
board_cfg = ArucoBoardConfig()
detector_cfg = ArucoDetectorConfig(board=board_cfg)
slot_grid_cfg = SlotGridConfig(cols=4, rows=3)

ml = board_cfg.marker_length  # 100 px
ms = board_cfg.marker_separation  # 100 px
margin = board_cfg.margin  # 20 px
rect_margin = detector_cfg.rect_margin  # 50 px

board_w, board_h = board_cfg.board_dimensions()

# ---------------------------------------------------------------------------
# Section 1: Key coordinate formulas
# ---------------------------------------------------------------------------
print("=" * 60)
print("SECTION 1: Key coordinate values (default config)")
print("=" * 60)
print(f"  board_w = {board_w},  board_h = {board_h}")
print(f"  marker_length = {ml},  margin = {margin},  rect_margin = {rect_margin}")

ring_start = margin + ml
print(f"\n  ring_start = margin + marker_length = {margin} + {ml} = {ring_start}")

# Board object point range (from GridBoard, before margin added to image)
# OpenCV GridBoard: marker at col i starts at x = i*(ml+ms), y = j*(ml+ms)
# Corner points: from (i*(ml+ms), j*(ml+ms)) to (i*(ml+ms)+ml, j*(ml+ms)+ml)
mx = board_cfg.markers_x
my = board_cfg.markers_y
obj_x_min = 0
obj_x_max = (mx - 1) * (ml + ms) + ml  # = (mx-1)*200 + 100
obj_y_min = 0
obj_y_max = (my - 1) * (ml + ms) + ml

board_obj_width = obj_x_max - obj_x_min
board_obj_height = obj_y_max - obj_y_min

print(f"\n  Board object coord range:")
print(f"    x: [{obj_x_min}, {obj_x_max}]  => board_obj_width = {board_obj_width}")
print(f"    y: [{obj_y_min}, {obj_y_max}]  => board_obj_height = {board_obj_height}")

# Rectified image dimensions (correct_perspective output)
out_w = board_obj_width + 2 * rect_margin
out_h = board_obj_height + 2 * rect_margin
print(f"\n  Rectified image: {out_w} x {out_h} px")

# Coordinate mapping: board_pixel <-> object_coord
# board_pixel = object_coord + margin
# rectified_pixel = object_coord + rect_margin
# => rectified_pixel = board_pixel - margin + rect_margin
shift_board_to_rectified = rect_margin - margin
print(f"\n  board_pixel -> rectified_pixel:  +{shift_board_to_rectified}")
print(
    f"    e.g. board (0,0) -> rectified ({shift_board_to_rectified},{shift_board_to_rectified})"
)
print(
    f"    e.g. board ({board_w},{board_h}) -> rectified ({board_w + shift_board_to_rectified},{board_h + shift_board_to_rectified})"
)

# crop_margin calculation (SheetAruco default)
crop_margin = ml + margin + rect_margin
print(f"\n  crop_margin = marker_length + margin + rect_margin")
print(f"    = {ml} + {margin} + {rect_margin} = {crop_margin}")

# Cropped image dimensions
cropped_w = out_w - 2 * crop_margin
cropped_h = out_h - 2 * crop_margin
print(f"\n  After symmetric crop: {cropped_w} x {cropped_h} px")

# crop_offset: how many board-image pixels correspond to the cropped image origin
# cropped_pixel = rectified_pixel - crop_margin
#               = (board_pixel + shift_b2r) - crop_margin
#               = board_pixel - (crop_margin - shift_b2r)
crop_offset = crop_margin - shift_board_to_rectified
print(f"\n  crop_offset (board_pixel = cropped_pixel + crop_offset):")
print(f"    = crop_margin - (rect_margin - margin)")
print(f"    = {crop_margin} - ({rect_margin} - {margin})")
print(
    f"    = {crop_offset} px  (= marker_length + 2*margin = {ml} + 2*{margin} = {ml + 2 * margin})"
)

# ---------------------------------------------------------------------------
# Section 2: Interior and QR strip in each coordinate space
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("SECTION 2: Interior and QR strip (all coordinate spaces)")
print("=" * 60)

interior_x0 = ring_start
interior_y0 = ring_start
interior_x1 = board_w - ring_start
interior_y1 = board_h - ring_start
qr_strip_h = ring_start  # SlotGrid sets qr_strip_h = ring_start
piece_area_y1 = interior_y1 - qr_strip_h

print("\n  In board image space:")
print(
    f"    interior:    x=[{interior_x0}, {interior_x1}),  y=[{interior_y0}, {interior_y1})"
)
print(f"    piece area:  y=[{interior_y0}, {piece_area_y1})")
print(f"    QR strip:    y=[{piece_area_y1}, {interior_y1})")


def to_rectified(v: int) -> int:
    return v + shift_board_to_rectified


def to_cropped(v_board: int) -> int:
    return v_board - crop_offset


print("\n  In rectified space:")
print(
    f"    interior:    x=[{to_rectified(interior_x0)}, {to_rectified(interior_x1)}),  y=[{to_rectified(interior_y0)}, {to_rectified(interior_y1)})"
)
print(
    f"    piece area:  y=[{to_rectified(interior_y0)}, {to_rectified(piece_area_y1)})"
)
print(
    f"    QR strip:    y=[{to_rectified(piece_area_y1)}, {to_rectified(interior_y1)})"
)

print("\n  In cropped sheet space (CURRENT, after symmetric ArUco crop):")
print(
    f"    interior:    x=[{to_cropped(interior_x0)}, {to_cropped(interior_x1)}),  y=[{to_cropped(interior_y0)}, {to_cropped(interior_y1)})"
)
print(f"    piece area:  y=[{to_cropped(interior_y0)}, {to_cropped(piece_area_y1)})")
print(f"    QR strip:    y=[{to_cropped(piece_area_y1)}, {to_cropped(interior_y1)})")
print(f"    image dims:  {cropped_w} x {cropped_h}")
print(
    f"    => QR strip is still present in cropped image! (rows {to_cropped(piece_area_y1)}-{to_cropped(interior_y1)} of {cropped_h})"
)

extra_bottom_crop = qr_strip_h
print(
    f"\n  After ADDITIONAL bottom crop of {extra_bottom_crop} px (margin + marker_length):"
)
final_h = cropped_h - extra_bottom_crop
print(f"    piece-only image dims: {cropped_w} x {final_h}")
print(
    f"    piece area exactly fills: y=[0, {final_h}) (with {-to_cropped(interior_y0)} px overlap at top/bottom)"
)

# ---------------------------------------------------------------------------
# Section 3: Slot grid coordinate mismatch (the bug)
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("SECTION 3: SlotGrid coordinate mismatch bug")
print("=" * 60)

slot_w = (interior_x1 - interior_x0) / slot_grid_cfg.cols
slot_h = (piece_area_y1 - interior_y0) / slot_grid_cfg.rows
print(f"\n  SlotGrid (4 cols x 3 rows):")
print(f"    slot_w = {slot_w:.1f} px (board image),  slot_h = {slot_h:.1f} px")

# Pick an example: piece at slot (col=1, row=1) centre in board image space
example_col, example_row = 1, 1
cx_board = interior_x0 + (example_col + 0.5) * slot_w
cy_board = interior_y0 + (example_row + 0.5) * slot_h
cx_cropped = cx_board - crop_offset
cy_cropped = cy_board - crop_offset
print(f"\n  Example: piece physically in slot ({example_col}, {example_row})")
print(f"    Centre in board image:  ({cx_board:.0f}, {cy_board:.0f})")
print(f"    Centre in cropped sheet: ({cx_cropped:.0f}, {cy_cropped:.0f})")

# Current buggy slot assignment (slot_for_centroid gets cropped coords but uses board formulas)
slot_grid = SlotGrid(slot_grid_cfg, board_cfg)
result_buggy = slot_grid.slot_for_centroid(int(cx_cropped), int(cy_cropped))
print(
    f"\n  slot_for_centroid({int(cx_cropped)}, {int(cy_cropped)}) [BUGGY - cropped coords passed]:"
)
print(f"    => slot {result_buggy}  (WRONG - expected ({example_col}, {example_row}))")

# Correct: pass board image coords
result_correct = slot_grid.slot_for_centroid(int(cx_board), int(cy_board))
print(
    f"\n  slot_for_centroid({int(cx_board)}, {int(cy_board)}) [CORRECT - board image coords]:"
)
print(f"    => slot {result_correct}  (correct)")

# Show the offset needed
print(
    f"\n  Fix: add crop_offset={crop_offset} to each centroid before calling slot_for_centroid"
)
result_fixed = slot_grid.slot_for_centroid(
    int(cx_cropped) + crop_offset, int(cy_cropped) + crop_offset
)
print(
    f"  slot_for_centroid({int(cx_cropped) + crop_offset}, {int(cy_cropped) + crop_offset}) => slot {result_fixed}  (correct)"
)

# ---------------------------------------------------------------------------
# Section 4: SlotGrid slot_centers mismatch (visualisation bug in notebook)
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("SECTION 4: SlotGrid.slot_centers() in notebook visualisation")
print("=" * 60)

centers = slot_grid.slot_centers()
print(f"\n  slot_centers() returns {len(centers)} centres in BOARD IMAGE space.")
example_center = centers[example_col + example_row * slot_grid_cfg.cols]
print(f"  Slot ({example_col},{example_row}) centre in board image: {example_center}")
print(
    f"  Slot ({example_col},{example_row}) centre in CROPPED image: ({example_center[0] - crop_offset}, {example_center[1] - crop_offset})"
)
print(
    f"\n  In the notebook, cv2.circle(sheet.img_orig, center, ...) draws in CROPPED space."
)
print(f"  Drawing the board-image centre ({example_center}) on a cropped image")
print(f"  places the dot {crop_offset}px to the SE of the correct position.")

# ---------------------------------------------------------------------------
# Section 5: Piece tracking - sheet_origin (what's missing from Piece)
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("SECTION 5: Piece.from_contour() - missing sheet_origin")
print("=" * 60)

# Simulate a contour bounding rect for a piece in the example slot
pad = 30
# Piece occupies roughly a slot-sized box at the example position
piece_x = int(cx_cropped - slot_w / 2)
piece_y = int(cy_cropped - slot_h / 2)
piece_region = (piece_x, piece_y, int(slot_w), int(slot_h))
print(f"\n  Simulated piece bounding rect in sheet space: {piece_region}  (x, y, w, h)")

# pad_rect: pad by 30, clamp to image
region_x = max(0, piece_x - pad)
region_y = max(0, piece_y - pad)
region_pad = (region_x, region_y, int(slot_w) + 2 * pad, int(slot_h) + 2 * pad)
print(f"  After pad_rect(pad={pad}): {region_pad}")

# The origin that should be stored on Piece
sheet_origin = (region_pad[0], region_pad[1])
print(f"\n  sheet_origin (origin of piece image in sheet coords): {sheet_origin}")
print(f"  This is NOT currently stored on Piece objects.")

# Piece-local centroid after contour.translate(...)
local_cx = int(cx_cropped - region_pad[0])
local_cy = int(cy_cropped - region_pad[1])
print(
    f"\n  Piece-local centroid (what piece.contour.centroid returns): ({local_cx}, {local_cy})"
)
print(
    f"  Sheet-space centroid (sheet_origin + local): ({local_cx + sheet_origin[0]}, {local_cy + sheet_origin[1]})"
)
print(
    f"  Expected: ({int(cx_cropped)}, {int(cy_cropped)})  - matches: {(local_cx + sheet_origin[0]) == int(cx_cropped) and (local_cy + sheet_origin[1]) == int(cy_cropped)}"
)

# ---------------------------------------------------------------------------
# Section 6: Generate a real board image and visually verify the crop
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("SECTION 6: Board image crop visualisation")
print("=" * 60)

generator = ArucoBoardGenerator(board_cfg)
board_img = generator.generate_image()

print(f"\n  Generated board image: {board_img.shape[1]} x {board_img.shape[0]} px")

# Simulate the perspective-correct crop that SheetAruco does
# (on the already-rectified image, board_img is already in board image space;
# we apply the same pixel offsets to simulate what would happen on a
# perfectly-rectified photo)
board_bgr = cv2.cvtColor(board_img, cv2.COLOR_GRAY2BGR)

# Draw interior boundary (board image space)
cv2.rectangle(
    board_bgr, (interior_x0, interior_y0), (interior_x1, interior_y1), (0, 255, 0), 2
)
# Draw piece area boundary
cv2.rectangle(
    board_bgr, (interior_x0, interior_y0), (interior_x1, piece_area_y1), (0, 0, 255), 2
)
# Draw QR strip
cv2.rectangle(
    board_bgr, (interior_x0, piece_area_y1), (interior_x1, interior_y1), (255, 0, 0), 2
)

# Annotate
font = cv2.FONT_HERSHEY_SIMPLEX
cv2.putText(
    board_bgr,
    "PIECE AREA (red)",
    (interior_x0 + 10, interior_y0 + 30),
    font,
    0.8,
    (0, 0, 255),
    2,
)
cv2.putText(
    board_bgr,
    "QR STRIP (blue)",
    (interior_x0 + 10, piece_area_y1 + 30),
    font,
    0.8,
    (255, 0, 0),
    2,
)

out_path = "scratch_space/20_piece_markers/16_board_annotated.png"
cv2.imwrite(out_path, board_bgr)
print(f"  Saved annotated board image to: {out_path}")
print(f"  Green: full interior border, Red: piece area, Blue: QR strip")

# Simulate symmetric crop (in board image space, offset by crop_offset)
# crop_margin in rectified space = crop_offset + rect_margin - margin = 140 + 30 = 170
# In board image space: crop 140 from top/left/right, keep bottom to board_h - 140
crop_in_board = crop_offset
cropped_region = board_img[
    crop_in_board : board_h - crop_in_board,
    crop_in_board : board_w - crop_in_board,
]
print(
    f"\n  After symmetric ArUco crop (applied in board image space using crop_offset):"
)
print(f"    Cropped image: {cropped_region.shape[1]} x {cropped_region.shape[0]} px")
print(f"    (expected: {cropped_w} x {cropped_h})")

cropped_bgr = cv2.cvtColor(cropped_region, cv2.COLOR_GRAY2BGR)
# QR strip in cropped space
qr_y0_cropped = to_cropped(piece_area_y1)
qr_y1_cropped = to_cropped(interior_y1)
cv2.rectangle(
    cropped_bgr, (0, qr_y0_cropped), (cropped_w, qr_y1_cropped), (255, 0, 0), 3
)
cv2.putText(
    cropped_bgr,
    "QR STRIP still here!",
    (10, qr_y0_cropped + 30),
    font,
    0.8,
    (255, 0, 0),
    2,
)

cv2.imwrite("scratch_space/20_piece_markers/16_after_aruco_crop.png", cropped_bgr)
print(f"  Saved to: scratch_space/20_piece_markers/16_after_aruco_crop.png")

# After extra bottom crop
extra_crop_in_board = qr_strip_h
piece_only = cropped_region[: cropped_h - extra_crop_in_board, :]
cv2.imwrite("scratch_space/20_piece_markers/16_after_qr_crop.png", piece_only)
print(f"\n  After additional bottom QR crop ({extra_crop_in_board} px):")
print(f"    Piece-only image: {piece_only.shape[1]} x {piece_only.shape[0]} px")
print(f"    Saved to: scratch_space/20_piece_markers/16_after_qr_crop.png")

print("\n" + "=" * 60)
print("SECTION 7: Proposed crop_offset formula (general)")
print("=" * 60)
print(f"""
  # At the end of SheetAruco.load_sheet(), after computing crop_margin:
  #
  #   crop_margin = marker_length + margin + rect_margin  [default]
  #   crop_offset = crop_margin - rect_margin + margin
  #               = marker_length + 2 * margin
  #               = {ml} + 2*{margin} = {ml + 2 * margin}  (for defaults)
  #
  # This offset converts ANY cropped-sheet coordinate to board-image coordinate:
  #   board_coord = cropped_coord + crop_offset
  #   cropped_coord = board_coord - crop_offset
""")
