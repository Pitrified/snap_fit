---
status: draft
---

# investigate matching

## draft

in
`data/greendemo_small/sheets`

we have 12 pictures of 3 boards, at 4 different zoom levels

`AAA__gds_pM_xZ.jpg`

where M is the board number (1,2,3) and Z is the zoom level (1,2,4,5)
and AAA is a prefix we can ignore (IMG or PXL with timestamp).

```
IMG_20260723_223210__gds_p1_x4.jpg
IMG_20260723_223612__gds_p2_x4.jpg
IMG_20260723_223822__gds_p3_x4.jpg
PXL_20260723_202949294__gds_p1_x2.jpg
PXL_20260723_203005406__gds_p1_x5.jpg
PXL_20260723_203015962__gds_p1_x1.jpg
PXL_20260723_203538742__gds_p2_x2.jpg
PXL_20260723_203549280__gds_p2_x5.jpg
PXL_20260723_203556185__gds_p2_x1.jpg
PXL_20260723_203749409__gds_p3_x2.jpg
PXL_20260723_203755958__gds_p3_x5.jpg
PXL_20260723_203801631__gds_p3_x1.jpg
```

### task 1

all p1 images are cut badly: a piece is cut off slightly.

are there some patches we can do in the reprojection/cut code to fix this?
in the original photo with the aruco rings, the piece is well within the frame.

### task 2

we want to compare and analyze the different zoom levels and camera modes

which one produces the cleanest contours?

### task 3

all these pieces match in a few groups of a few pieces
we can drive the matching code by hand and see if we can get a good match for all pieces
so that we can create a ground truth for the matching code
and then we can test some things in the matching code or preprocessing configs to see how we can maximize the matching scores

## analysis

### what the dataset actually is

Decoded from the QR in the photos themselves, not from the filenames:

- `board_config_id = "greendemo_small"`, resolved from
  `data/aruco_boards/greendemo_small/greendemo_small_SheetArucoConfig.json`.
  The `gds` in the filename is the print-run `tag_name` (`gd_s`), not the board id.
- `total_sheets = 4`. `p1` -> `sheet_index=0`, `p2` -> `sheet_index=1`.
  So the print run has four base sheets and three of them were photographed;
  `sheet_03` has no captures.
- 4 zoom levels per sheet, 12 photos, all 4080x3072.
- The `x4` shots are the only `IMG_` ones; `x1`/`x2`/`x5` are all `PXL_`.
  Camera mode and zoom level are therefore perfectly confounded at `x4` (see Q3).

Board geometry (`greendemo_small`, 4x5 markers, `marker_length=100`,
`marker_separation=40`, `margin=20`, `rect_margin=50`):

```
board image      560 x 700
ring_start       margin + marker_length = 120
ring interior    x 120..440, y 120..580   (320 x 460)
QR strip         y 460..580
piece area       x 120..440, y 120..460   (320 x 340)
slot grid        2x2 -> 4 pieces per sheet, slots ~160 x 170
```

12 physical pieces total (3 sheets x 4 slots), 48 segments.

### probe results

Ran `SheetAruco.load_sheet` on `p1_x1`, `p1_x4`, `p2_x1`:

- 14 of 20 marker ids detected on every one, always the same 14.
  That is the full ring: the six interior ids (5, 6, 9, 10, 13, 14) are never
  printed, so detection is complete. Rectification bounds are not the problem.
- rectified size is `620 x 760` on all three, at every zoom.
- cropped sheet is `280 x 300`, `crop_offset = 140`.
- 4 pieces found on each, all four slot labels assigned and distinct.

Contour bounding boxes in cropped-sheet space, sheet is 280 wide:

| photo   | rightmost piece | x range   | clear of right edge |
| ------- | --------------- | --------- | ------------------- |
| p1_x1   | B2              | 181..280  | no, flush, clipped  |
| p1_x4   | B2              | 182..280  | no, flush, clipped  |
| p2_x1   | B2              | 173..264  | yes, 16 px          |

That is task 1 reproduced and localised: p1's B2 piece runs into the right
border of the cropped sheet, so its contour is truncated into a straight line
along the border. p2's rightmost piece happens to sit 16 px further left and
survives. Nothing about p1 is special except where the pieces were placed.

### root cause of task 1

The cropped sheet is 20 px too small on all four sides.

`SheetAruco.load_sheet` crops `crop_margin` from every side, where

```
crop_margin = marker_length + margin + rect_margin = 170
```

But the rectified image's coordinate origin is the **object-coordinate** origin,
the outer corner of the first marker, offset by `rect_margin`. Object
coordinates do not include the board `margin`: OpenCV's grid board starts at 0
at the first marker corner. The ring's inner edge in rectified space is at
`rect_margin + marker_length = 150`. Cropping at 170 overshoots it by exactly
`margin = 20` px, on every side.

Measured: the cropped sheet is `280 x 300` where the true piece area is
`320 x 340`. 20 px lost left, right, top and bottom.

This is not new. `scratch_space/20_piece_markers/16_sheet_cropping.md` derived
the same `-20 px` overshoot and closed it as deliberate: the extra `margin` is a
safety buffer so a sliver of ArUco ring can never bleed into the sheet, and

> With `margin = 20 px` and slot dimensions of ~175 x 327 px this is negligible.
> Document this in `SheetAruco.load_sheet()` with a comment. No code change needed.

That judgement was made against the full-size `greendemo` board. On
`greendemo_small` the slots are ~160 x 170, the pieces nearly fill them, and the
same 20 px is exactly what clips p1's B2. The prior decision is reopened (D1).

### the resolution ceiling, and why it matters for task 2

`correct_perspective` sizes the output purely from the board object points:

```
out_width  = board_width  + 2 * rect_margin
out_height = board_height + 2 * rect_margin
```

There is no dependence on the source photo. Confirmed by probe: `x1` and `x4`
both rectify to `620 x 760` from the same 4080x3072 sensor frame.

So zooming in does **not** buy contour resolution. A piece is ~100 x 100 px in
the rectified sheet no matter what, and a segment is ~100 points. What zoom
changes is how many source pixels are squeezed into that fixed output, i.e. how
much downsampling `warpPerspective` does. It uses `INTER_LINEAR`, which aliases
under heavy downsampling. That gives task 2 a concrete hypothesis to test rather
than a vibe check: the differences between zoom levels are resampling artifacts,
and the real lever may be an output-scale knob on the warp (Q4).

### cross-capture piece identity

`PieceId.piece_id` is an ordinal assigned by descending contour area, so it is
not stable across captures: p1_x1 ordered its pieces A1, B1, A2, B2 while p1_x4
ordered them A1, B2, B1, A2.

ANS: this is insane. there are literal physical labels on the board, and when we take pictures of the pieces we take note of the labels. confirm that the labels are stable across captures, so top left is A1 and so on, regardless of the piece's contour area.

The slot label is stable. `(sheet_index, slot_label)` names a physical piece
across all 12 captures, and it comes for free from the QR plus `SlotGrid`. That
is the join key for everything downstream (D2).

Consequence: ground truth can be stated once, in physical terms, as pairs of
`(sheet_index, label, edge_pos)`, and then scored against every capture variant.
Task 2 and task 3 become the same experiment run with different groupings, which
is why the corpus is built once, first (D4).

### what already exists for task 3

- `MatchResult.similarity_manual_` (alias `similarity_manual`) is already a
  hand-annotation slot on each pair.
- `PieceMatcher` already has `save_matches_json` / `load_matches_json` and the
  SQLite equivalents, plus a `frozenset[SegmentId]` cache.
- `SegmentMatcher.compute_similarity` returns `1e6` for a shape-incompatible
  pair and otherwise a mean point distance after an affine fit. Lower is better,
  and it is **not** scale-normalised, so scores are only comparable between
  captures at the same rectified scale. Fine here, since the scale is fixed.

So there is a place to put ground truth. Whether it belongs there is Q5.

### incidental finding

`Contour.area` is `compute_rect_area(self.region)`, the **bounding-box** area,
not the contour area. `min_area` filters on that. Not a bug for this work, but
the name misleads and it makes `min_area` sensitive to piece rotation. Noted
here; not in scope unless it bites.

## decisions

- **D1**: task 1 is the `crop_margin` overshoot, and it gets fixed in code.
  Reopens the "negligible, no code change needed" call in
  `20_piece_markers/16_sheet_cropping.md`, on the evidence that it is exactly
  what clips p1's B2 on a smaller board.
  Rejected alternative: undetected markers shrinking the warp bounds. Ruled out,
  all 14 printed ring markers were detected on every probed photo.
  Rejected alternative: leave it and place pieces more centrally. That hides a
  systematic error behind capture discipline and would silently truncate
  contours on any future tight board.
- **D2**: `(sheet_index, slot_label)` is the physical-piece identity key across
  captures. `PieceId.piece_id` is a per-capture ordinal and must not be used to
  join.
- **D3**: ground truth is stated once per physical edge pair, in
  `(sheet_index, label, edge_pos)` terms, independent of any capture.
- **D4**: the corpus (all 12 photos ingested and keyed by D2) is built once and
  shared by tasks 2 and 3. Neither task starts before it exists.
- **D5**: the fix in phase 1 must keep the ring safety buffer as an explicit,
  named quantity rather than smuggling it in as `board.margin`. If a buffer is
  wanted it should be a knob with a stated reason, not a coincidence of units.

## proposed phases

Cheapest and most independent first. Phase 1 is a real bug with a known root
cause; everything after it depends on the corpus.

| #   | Phase                         | Covers | Notes                                                                                                                          |
| --- | ----------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Fix the interior over-crop    | task 1 | `crop_margin` -> `marker_length + rect_margin`, `crop_offset` -> `ring_start`. Regression test on board geometry. Update `docs/guides/coordinate_spaces.md` (hardcodes 170 / 140 / 660x940) and `docs/library/puzzle/sheet_aruco.md`. Verify B2 is no longer flush after the change. |
| 2   | Labelled capture corpus       | -      | Ingest all 12 photos, key every piece by `(sheet_index, label)`, persist pieces and segments. Assert 4 pieces and 4 distinct labels per capture. Probably a `pipelines/` entry, since bulk ingest is already a backlog candidate. |
| 3   | Capture quality comparison    | task 2 | Score contour quality per capture with stated metrics, grouped by zoom. Test the resampling hypothesis (`INTER_AREA` vs `INTER_LINEAR`, output scale). Report the confound at `x4`. |
| 4   | Ground-truth edge pairs       | task 3 | Hand-drive the matcher over 48 segments, record the true pairs in D3 form, store them. Report the score separation between true and false pairs. |
| 5   | Matching and preprocess tuning| task 3 | Sweep preprocess and matcher parameters against the phase-4 ground truth, using true-vs-false score separation as the objective. |

Phases 3-5 stay `draft` until phase 2 lands; their shape depends on what the
corpus looks like.

## open questions

- Q1: the fix recovers 20 px per side. Is that enough to fully contain p1's B2,
  or does the piece genuinely overhang the ring interior on the board? If it
  overhangs, the fix is correct but insufficient and we also need to decide
  whether to crop into the ring band at all.
  ANS: the piece does not overlap the ring interior, so the fix is sufficient.
- Q2: `sheet_03` of the four-sheet run was never photographed. Intentional, or
  is it coming? It changes whether the corpus is "the dataset" or a subset.
  ANS: intentional, we had a total of 12 pieces, so we only needed 3 sheets.
- Q3: every `x4` photo is an `IMG_` capture and every other zoom is `PXL_`, so
  camera mode and zoom cannot be separated. Do we reshoot to break the
  confound, or do we accept it and report `x4` as "a different camera at a
  different zoom"?
  ANS: accept it and report `x4` as "a different camera at a different zoom".
- Q4: the rectified output is fixed at `620 x 760` regardless of source zoom, so
  contour resolution is capped by board units, not by the photo. Do we add an
  output-scale knob to `correct_perspective`? It would change every stored
  coordinate and every tuned pixel threshold downstream, so it is a separate
  effort if we want it. Spin-off, or fold into phase 3?
  ANS: do it, it gets its own phase.
- Q5: where does ground truth live? `MatchResult.similarity_manual_` already
  exists but holds a float score per pair, whereas D3 wants a set of true pairs
  in physical terms. Reuse and reinterpret the field, or add a separate truth
  file keyed by `(sheet_index, label, edge_pos)`?
  ANS: a custom truth file keyed for this specific set of pictures.
- Q6: what is "cleanest contour" for task 2, concretely? Candidates: contour
  point count, perimeter smoothness, corner-detection stability, agreement of
  the same physical piece's contour across captures, or simply the phase-4
  match score. The last one is the only metric that measures what we care
  about, but it makes phase 3 depend on phase 4.
  ANS: best match score as first metric, but we can compute a few.
- Q7: should phase 2 land in `pipelines/` (bulk ingest is already a backlog
  candidate there) or stay scratch-local for this investigation?
  ANS: stay scratch-local for this investigation.
