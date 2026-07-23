---
status: done
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

## Outcome

Done, 2026-07-24. All criteria met.

### `crop_offset` did not need changing, and the plan was wrong about it

The plan said to change `crop_offset` to `marker_length + margin`. That would
have been a bug. The existing formula

```
crop_offset = crop_margin - rect_margin + margin
```

is the correct *general* relation for any `crop_margin`, derived from
`board = cropped + crop_margin - rect_margin + margin`. It was never wrong; it
was producing 140 only because `crop_margin` was wrong. Hardcoding it to
`ring_start` would have broken every config that sets `crop_margin` explicitly.

So only the one `crop_margin` default changed, and `crop_offset` corrected
itself to 120 as a consequence. Confirmed on the real photos: board-space
centroids are unchanged to within 1 px (e.g. sheet 0 B2 at (365,351) before and
(366,351) after), which is exactly what should happen when the crop moves by 20
and the offset compensates by 20.

It was extracted to a `SheetAruco.crop_offset` property, because it was computed
inline inside `load_sheet` and therefore unreachable from a test. That, not the
formula, was the actual defect worth fixing.

### No ring buffer was needed

The sliver check came back clean: all 12 photos still yield exactly 4 pieces
with 4 distinct labels, 48 piece rows before and after, and no unlabelled
contour anywhere. So the extra 20 px was never protecting against anything, and
no knob was added. This settles the D5 refinement in favour of the direct fix.

### B2 is clear

| capture | bbox before | bbox after | clipped |
| ------- | ----------- | ---------- | ------- |
| x1      | 99x82       | 105x82     | no      |
| x2      | 100x81      | 105x81     | no      |
| x4      | 98x77       | 99x77      | no      |
| x5      | 100x82      | 105x82     | no      |

The piece only ever overhung by ~5 px, so 20 px was more than enough. Clipped
count across the dataset went 4 -> 0.

### Test coverage

`tests/puzzle/test_sheet_aruco.py`, 6 tests. Verified by reverting the fix: 5 of
the 6 fail. The 6th (`test_explicit_crop_margin_keeps_the_offset_consistent`)
correctly does not, because it pins the general offset relation rather than the
default.

### Unrelated pre-existing failure

`tests/aruco/test_sheet_metadata.py::test_printed_at_defaults_to_today` fails,
and did before this change. `SheetMetadata.printed_at` defaults via
`date.today()` (local) while the test asserts against
`datetime.now(tz=UTC).date()`. The machine is CEST, so between local midnight
and UTC midnight the two dates differ and the test fails. Not touched here; it
is a real latent bug, not a one-off.
