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
- `total_sheets = 4`, but only sheets 0, 1, 2 were photographed, which is
  deliberate: 12 pieces at 4 slots per sheet needs exactly 3 sheets (Q2).
  `sheet_03` is not missing data, and the corpus is the whole dataset.
- 4 zoom levels per sheet, 12 photos, all 4080x3072.
- The `x4` shots are the only `IMG_` ones; `x1`/`x2`/`x5` are all `PXL_`.
  Camera mode and zoom level are perfectly confounded at `x4`, and that is
  accepted rather than reshot: `x4` is reported as "a different camera at a
  different zoom", not as a fourth point on a zoom axis (Q3, D6).

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

Ran `SheetAruco.load_sheet` over all 12 photos and tabulated every piece by
`(sheet_index, label)`, with centroids converted to board-image space.

Structural results, identical on all 12:

- 14 of 20 marker ids detected, always the same 14. That is the full ring: the
  six interior ids (5, 6, 9, 10, 13, 14) are never printed, so detection is
  complete. Rectification bounds are not the problem.
- rectified size `620 x 760`, cropped sheet `280 x 300`, `crop_offset = 140`.
- exactly 4 pieces, with the 4 distinct labels A1, A2, B1, B2.

### slot labels are stable, confirmed

Every label lands at the same board-space centroid across all four captures of
its sheet, to within a few pixels (Q8):

| sheet | label | board centroid, x1 / x2 / x4 / x5      | spread |
| ----- | ----- | -------------------------------------- | ------ |
| 0     | A1    | (213,207) (213,208) (213,210) (213,209) | 3 px   |
| 0     | B1    | (358,211) (357,212) (356,214) (357,212) | 3 px   |
| 0     | A2    | (204,362) (205,361) (205,365) (206,361) | 4 px   |
| 0     | B2    | (365,351) (365,351) (364,350) (365,351) | 1 px   |
| 1     | A1    | (202,210) (203,210) (204,211) (203,210) | 2 px   |
| 2     | B2    | (345,352) (346,351) (347,352) (345,350) | 2 px   |

(sheets 1 and 2 behave the same throughout; rows trimmed for length.)

So the physical label is exactly what it looks like: A1 is the top-left slot,
B2 the bottom-right, and it does not depend on the piece. `(sheet_index, label)`
is the identity key across all 12 captures (D2). The only caveat is a negative
one: `PieceId.piece_id` is a per-capture ordinal over descending contour area
and does reorder between captures, so it must never be used to join. The label
is read off `SlotGrid`, not off the ordinal, so it is unaffected.

### which pieces are clipped

`B2` on sheet 0 is flush against the right border of the cropped sheet on all
four captures, and nothing else is clipped anywhere in the dataset:

| sheet | label | clipped on         |
| ----- | ----- | ------------------ |
| 0     | B2    | x1, x2, x4, x5     |
| all others | -| never              |

That is task 1, reproduced across the whole dataset and localised to one piece.
Its contour is truncated into a straight line along the border. Nothing about
p1 is special except where that piece was placed.

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

Recovering those 20 px is sufficient: the piece does not overhang the ring
interior on the physical board (Q1), so no crop into the ring band is needed.

This is not new. `scratch_space/20_piece_markers/16_sheet_cropping.md` derived
the same `-20 px` overshoot and closed it as deliberate: the extra `margin` is a
safety buffer so a sliver of ArUco ring can never bleed into the sheet, and

> With `margin = 20 px` and slot dimensions of ~175 x 327 px this is negligible.
> Document this in `SheetAruco.load_sheet()` with a comment. No code change needed.

That judgement was made against the full-size `greendemo` board. On
`greendemo_small` the slots are ~160 x 170, the pieces nearly fill them, and the
same 20 px is exactly what clips sheet 0's B2. The prior decision is reopened
(D1).

### the x4 captures lose piece extent

Not something the tasks predicted, but it falls straight out of the same table.
Bounding boxes of the same physical piece across captures:

| sheet | label | x1     | x2     | x4 (IMG) | x5     |
| ----- | ----- | ------ | ------ | -------- | ------ |
| 0     | A1    | 105x105| 104x106| **97x83**| 104x105|
| 0     | B1    | 86x117 | 85x117 | **61x111**| 86x117|
| 0     | A2    | 79x111 | 78x109 | **72x88**| 78x110 |
| 1     | B2    | 91x94  | 93x94  | **70x90**| 93x96  |
| 2     | A2    | 101x96 | 98x94  | **76x91**| 98x97  |
| 2     | B2    | 103x85 | 97x67  | **83x66**| 100x84 |

`x4` shrinks the piece on every single row, sometimes by 25 px in one axis
(sheet 0 B1: 86 wide becomes 61). `x2` shrinks on sheet 2 as well; `x1` and `x5`
agree with each other throughout.

The pieces did not move, so this is the segmentation eroding them. Lost extent
is lost knobs, and knobs are the entire matching signal, so this is likely to
dominate any zoom effect. The plausible mechanism is the HSV background mask:
a different camera app means different white balance and exposure, pushing
piece pixels into the green band, which the `BackgroundMaskConfig` docstring
already warns is the failure mode that "silently erodes every piece".

This also hands task 2 a cheap discriminating metric that needs no ground truth:
disagreement in bounding box between captures of the same physical piece.

### the resolution ceiling

`correct_perspective` sizes the output purely from the board object points:

```
out_width  = board_width  + 2 * rect_margin
out_height = board_height + 2 * rect_margin
```

There is no dependence on the source photo. Confirmed by probe: every zoom
rectifies to `620 x 760` from the same 4080x3072 sensor frame.

So zooming in does **not** buy contour resolution. A piece is ~100 x 100 px in
the rectified sheet no matter what, and a segment is ~100 points. What zoom
changes is how many source pixels are squeezed into that fixed output, i.e. how
much downsampling `warpPerspective` does. It uses `INTER_LINEAR`, which aliases
under heavy downsampling.

An output-scale knob on the warp is worth having and gets its own phase (Q4,
D8), sequenced after the capture comparison so the scale is chosen against
evidence rather than guessed.

### what already exists for task 3

- `MatchResult.similarity_manual_` (alias `similarity_manual`) is a
  hand-annotation slot on each pair. Not used for ground truth (D7).
- `PieceMatcher` already has `save_matches_json` / `load_matches_json` and the
  SQLite equivalents, plus a `frozenset[SegmentId]` cache.
- `SegmentMatcher.compute_similarity` returns `1e6` for a shape-incompatible
  pair and otherwise a mean point distance after an affine fit. Lower is better,
  and it is **not** scale-normalised, so scores are only comparable between
  captures at the same rectified scale. That is fine today, and becomes a
  constraint the moment the scale knob lands.

### incidental finding

`Contour.area` is `compute_rect_area(self.region)`, the **bounding-box** area,
not the contour area. `min_area` filters on that. Not a bug for this work, but
the name misleads and it makes `min_area` sensitive to piece rotation. Noted
here; not in scope unless it bites.

## decisions

- **D1**: task 1 is the `crop_margin` overshoot, and it gets fixed in code.
  Reopens the "negligible, no code change needed" call in
  `20_piece_markers/16_sheet_cropping.md`, on the evidence that it is exactly
  what clips sheet 0's B2 on a smaller board.
  Rejected alternative: undetected markers shrinking the warp bounds. Ruled out,
  all 14 printed ring markers were detected on every photo.
  Rejected alternative: leave it and place pieces more centrally. That hides a
  systematic error behind capture discipline and would silently truncate
  contours on any future tight board.
- **D2**: `(sheet_index, slot_label)` is the physical-piece identity key across
  captures, confirmed by centroid agreement to within 4 px on all 12 photos.
  `PieceId.piece_id` is a per-capture ordinal and must not be used to join.
- **D3**: ground truth is stated once per physical edge pair, in
  `(sheet_index, label, edge_pos)` terms, independent of any capture. This also
  makes it survive the scale change in phase 5, which a pixel-space truth would
  not.
- **D4**: the corpus (all 12 photos ingested and keyed by D2) is built once and
  shared by every later phase. Nothing else starts before it exists.
- **D5**: the phase 1 fix keeps the ring safety buffer as an explicit, named
  quantity rather than smuggling it in as `board.margin`. If a buffer is wanted
  it should be a knob with a stated reason, not a coincidence of units.
- **D6**: the `x4` / `IMG_` confound is accepted, not reshot. `x4` is reported
  as "a different camera at a different zoom" and is never used as evidence
  about zoom alone.
- **D7**: ground truth lives in its own truth file keyed by
  `(sheet_index, label, edge_pos)` and scoped to this picture set, not in
  `MatchResult.similarity_manual_`. That field is a per-pair float on a
  capture-specific result; the truth is a capture-independent set of pairs, and
  overloading the field would conflate "what the matcher scored" with "what is
  actually true".
- **D8**: the rectification output-scale knob is in scope and gets its own
  phase, sequenced after the capture comparison so the chosen scale is
  evidence-backed.
- **D9**: every phase stays scratch-local to `24_investigate_matching/`. No
  `pipelines/` entry from this effort. Promotion is a separate call, made after
  the investigation says what is worth keeping.

## phases

Phase 1 is an isolated bug fix and runs first. Phase 2 is the shared
prerequisite. Ground truth (phase 3) comes before the capture comparison
because the best-match score is the primary quality metric (Q6), and it is
stated in physical terms (D3) so the later scale change does not invalidate it.

| #   | Phase                        | Plan file                        | Covers  |
| --- | ---------------------------- | -------------------------------- | ------- |
| 1   | Fix the interior over-crop   | `01_fix_interior_overcrop.md`    | task 1  |
| 2   | Labelled capture corpus      | `02_capture_corpus.md`           | -       |
| 3   | Ground-truth edge pairs      | `03_match_ground_truth.md`       | task 3  |
| 4   | Capture quality comparison   | `04_capture_quality.md`          | task 2  |
| 5   | Rectification output scale   | `05_rectify_output_scale.md`     | -       |
| 6   | Matching and preprocess tuning | `06_matching_tuning.md`        | task 3  |

**Phase 1 - fix the interior over-crop.**
`crop_margin` becomes `marker_length + rect_margin`, plus an explicit named ring
buffer defaulting to 0 (D5); `crop_offset` becomes `ring_start`. Regression test
asserting the cropped sheet equals the piece area for a known board geometry.
Verify sheet 0's B2 is no longer flush after the change, and that no ArUco
sliver appears as a contour. Update `docs/guides/coordinate_spaces.md` (it
hardcodes 170 / 140 / 660x940) and `docs/library/puzzle/sheet_aruco.md`.

**Phase 2 - labelled capture corpus.**
Ingest all 12 photos, key every piece by `(sheet_index, label)`, persist pieces
and segments. Assert 4 pieces and 4 distinct labels per capture, and centroid
agreement across the 4 captures of each sheet, so a regression in labelling is
caught rather than silently joined on. Scratch-local (D9).

**Phase 3 - ground-truth edge pairs.**
Hand-drive the matcher over the 48 segments on the best capture set and record
the true pairs in D3 form in the truth file (D7). Report the score separation
between true and false pairs as the baseline everything later is measured
against.

**Phase 4 - capture quality comparison.**
Primary metric is the phase-3 best-match score per capture group (Q6).
Secondary, cheap metrics computed alongside: bounding-box agreement of the same
physical piece across captures (already discriminating, see the x4 finding),
contour point count, and corner-detection stability. Test the resampling
hypothesis (`INTER_AREA` vs `INTER_LINEAR`). Report `x4` per D6. Expected to
also settle Q9, whether the x4 erosion is a mask-tuning problem or just a bad
capture.

**Phase 5 - rectification output scale.**
Add the output-scale knob to `correct_perspective` (D8), at the scale phase 4
argues for. Everything downstream in pixel units moves with it: `crop_margin`,
`min_area`, blur and erosion kernels, `pad`, `SlotGrid`, the stored
`sheet_origin` / `contour_region` / `padded_size`, and the non-normalised
`SegmentMatcher` score. Rebuild the corpus at the new scale; the phase 3 truth
file survives unchanged by construction.

**Phase 6 - matching and preprocess tuning.**
Sweep preprocess and matcher parameters against the phase-3 ground truth at the
phase-5 scale, with true-vs-false score separation as the objective.

Phases 4-6 stay `draft` until phase 2 lands; their shape depends on what the
corpus looks like.

## open questions

### answered

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
- Q8 (raised inline): confirm the labels are stable across captures, so top left
  is A1 and so on, regardless of the piece's contour area.
  ANS: confirmed on all 12 photos. Every sheet yields exactly 4 pieces with the
  4 distinct labels, and each label's board-space centroid agrees to within 4 px
  across its four captures. See "slot labels are stable, confirmed" above. The
  label comes from `SlotGrid`, which is purely positional, so contour area never
  enters into it.

### open

- Q9: the `x4` captures shrink every piece's bounding box, by up to 25 px in one
  axis. Is that a mask/threshold tuning problem we should fix (per-capture HSV
  bounds, or auto white balance compensation), or do we just rank `x4` worst and
  move on? It decides whether phase 4 ends in a report or in a code change.
  ANS: we can try and salvage it with a mask/threshold tuning fix, but if that fails we rank `x4` worst and move on.
- Q10: what output scale should phase 5 target? A fixed multiplier (2x, 3x), or
  a stated resolution in px per board unit that the config carries? The second
  is more work but makes every pixel threshold in the codebase interpretable in
  physical units instead of board-pixel units.
  ANS: before we go all in with a config knob, we can do some experiments to see if a different resolution improves the matching scores or not.
- Q11: the 12 pieces "match in a few groups of a few pieces". How many true edge
  pairs should the phase 3 truth file end up with, and are the groups disjoint
  (three separate mini-puzzles) or one set that happens to cluster? Knowing the
  expected count means phase 3 can assert completeness instead of stopping when
  it runs out of obvious pairs.
  ANS: disjoint groups
- Q12: phase 5 moves every pixel threshold, but `SegmentMatcher` scores are not
  scale-normalised, so phase 3's baseline separation numbers stop being
  comparable after the rescale. Do we normalise the score by segment length as
  part of phase 5, or keep the raw score and only ever compare within one scale?
  ANS: rescale while comparing
