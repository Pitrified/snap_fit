---
status: planned
---

# Phase 1 - Fix the interior over-crop

## Overview

`SheetAruco.load_sheet` crops 20 px too much from every side of the rectified
sheet, so the usable piece area is 280x300 where the board geometry says it
should be 320x340. On `greendemo_small` that is exactly what truncates sheet 0's
B2 contour into a straight line along the right border, on all four of its
captures. This is task 1.

Isolated from everything else in the effort: it is a bug fix in `src` with a
test, and it does not depend on the corpus or the annotation. It runs first
because every later phase measures contours, and measuring truncated ones is
wasted work.

Context: [`00_start.md`](00_start.md), sections "root cause of task 1" and
"which pieces are clipped".

## Goals

1. The cropped sheet equals the board's piece area, exactly, for any board
   geometry.
2. `crop_offset` keeps mapping cropped-sheet coordinates to board-image
   coordinates correctly after the change.
3. The geometry is covered by a test, so the next change to it cannot regress
   silently.
4. Sheet 0's B2 contour is no longer clipped.

## The arithmetic

Object coordinates start at the outer corner of the first marker and do **not**
include the board `margin`. In rectified space the ring's inner edge therefore
sits at `rect_margin + marker_length`, and that is exactly where the crop should
land:

```
current   crop_margin = marker_length + margin + rect_margin   = 170   (20 too many)
correct   crop_margin = marker_length + rect_margin            = 150

current   crop_offset = crop_margin - rect_margin + margin     = 140
correct   crop_offset = marker_length + margin = ring_start    = 120
```

Checked against `greendemo_small` (`marker_length=100`, `margin=20`,
`rect_margin=50`, board 560x700, `ring_start=120`):

| stage                  | current | correct | piece area |
| ---------------------- | ------- | ------- | ---------- |
| rectified              | 620x760 | 620x760 | -          |
| after symmetric crop   | 280x420 | 320x460 | -          |
| after QR strip crop    | 280x300 | 320x340 | 320x340    |

The QR strip crop of `ring_start` from the bottom is already correct in board
terms and does not change; it only lands on the right row once the symmetric
crop does.

## Plan

- Change the computed default in `SheetAruco.__init__`
  ([sheet_aruco.py:26-34](../../src/snap_fit/puzzle/sheet_aruco.py#L26-L34)) to
  `marker_length + rect_margin`.
- Change `crop_offset` in `load_sheet`
  ([sheet_aruco.py:70-74](../../src/snap_fit/puzzle/sheet_aruco.py#L70-L74)) to
  `marker_length + margin`, and note in a comment that this is `ring_start`, the
  same quantity `SlotGrid` uses for the interior origin.
- Add the geometry test. There is currently **no test at all** covering the crop
  arithmetic, which is why a 20 px error survived a prior investigation that
  found it. Assert, for a synthetic board config:
  - cropped sheet dimensions equal the `SlotGrid` piece area,
  - `crop_offset == margin + marker_length`,
  - a point at cropped `(0, 0)` maps to board-image `(ring_start, ring_start)`.
- Run the ArUco sliver check: ingest all 12 photos and confirm no new contour
  appears along any border. The prior rationale for the extra 20 px was a safety
  buffer against ring bleed, so it has to be shown unnecessary rather than
  assumed so.
- Verify sheet 0 B2 is no longer flush: its bbox right edge must sit strictly
  inside the sheet width on all four captures.
- Update the docs that hardcode the old numbers:
  [docs/guides/coordinate_spaces.md](../../docs/guides/coordinate_spaces.md)
  (the values table, the transformation chain, and the `crop_offset` formula at
  lines 37, 49-58, 66-72) and
  [docs/library/puzzle/sheet_aruco.md](../../docs/library/puzzle/sheet_aruco.md)
  line 51.

### On the safety buffer

D5 said the ring buffer should become an explicit named knob rather than a
coincidence of units. On reflection that overshoots: a config knob defaulting to
0 that no caller sets is exactly the speculative generality the repo guidance
warns against, and Q1 already established the piece does not overhang the ring
interior.

So the plan is the direct fix with **no new knob**, and the sliver check is what
justifies it. If slivers do appear, the buffer becomes a real need with a
measured reason attached, and it gets added then. This refines D5 rather than
contradicting it: the decision was "not smuggled in as `board.margin`", and
removing it entirely satisfies that.

## Out of scope

- The rectification output scale. Phase 6.
- `Contour.area` being bounding-box area rather than contour area. Noted as an
  incidental finding in `00_start.md`; not touched here.
- Any change to preprocessing, shape classification, or matching.
- Re-ingesting into a persistent corpus. Phase 2.

## Done when

- The geometry test passes and fails if either constant is reverted.
- All 12 photos ingest with no border contour introduced by the wider crop.
- Sheet 0's B2 bbox is strictly inside the sheet on all four captures.
- Both docs reflect the new numbers.
- `uv run pytest && uv run ruff check . && uv run pyright && uv run pre-commit run --all-files`
  passes.
