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

Capture note: the photos were taken at different zoom levels *and* different
distances, so the board roughly fills the frame in all of them. What changes is
which camera app is used and the parallax (far and zoomed -> straighter?).
Pixel 7 Pro; the `x4` images are Open Camera, the others are Google Camera, so
some AI postprocessing was probably going on.

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
- 4 captures per sheet, 12 photos, all 4080x3072.

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

### what actually varies between captures

The capture note said distance was traded against zoom to keep the board filling
the frame. EXIF confirms it and says more:

| capture | app           | focal | 35mm eq | digital zoom | subject dist | HDR+ |
| ------- | ------------- | ----- | ------- | ------------ | ------------ | ---- |
| x1      | Google Camera | 6.81  | 24      | none         | 0.19 m       | yes  |
| x2      | Google Camera | 6.81  | 48      | none         | 0.33-0.36 m  | yes  |
| x5      | Google Camera | 6.81  | 48      | 2.5x         | 0.75-0.79 m  | yes  |
| x4      | Open Camera   | 6.81  | -       | -            | -            | no   |

Every one of the 12 shots is the **same physical lens**: 6.81 mm at f/1.85, the
Pixel 7 Pro main sensor. The 5x telephoto module is never used, not even on
`x5`, presumably because the subject is inside its minimum focus distance. So
"zoom level" is not a lens axis.

Reading the axes off the table, what actually differs is three things at once:

1. **Camera pipeline.** `x1`/`x2`/`x5` carry `Software: HDR+ 1.0.93681`, so
   multi-frame merge, tone mapping and sharpening. `x4` has no HDR+ tag at all,
   so it is a single-shot JPEG with no computational stack.
2. **Subject distance**, 0.19 m to 0.79 m, a 4x spread. This is the parallax
   axis the capture note points at.
3. **Sensor crop and digital upscale.** `x1` uses the full frame. `x2` is a 2x
   in-sensor crop of the 50 MP sensor, which is real detail. `x5` is that same
   2x crop plus a further 2.5x digital upscale, so its true optical detail is
   ~2.5x lower than its pixel count suggests.

`x4` is off all three axes simultaneously: different app, unknown distance, no
crop metadata. It is a fourth capture condition, not a fourth point on any axis
(Q3, D6).

The task framing "which zoom level is cleanest" therefore does not have a clean
answer, because there is no zoom axis. The answerable question is which of four
named capture conditions gives the best contours, and phase 4 reports it that
way.

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

That 1-4 px spread is itself the parallax the capture note predicted, and it
comes out the right size. The homography rectifies the *board plane*; a piece
sits a couple of mm above it, so its top face is displaced radially outward by
roughly `r * t / d`. With `t ~ 2 mm`, an edge piece at `r ~ 5 cm`, and a board
~15 cm wide (Q14), that is ~2 board px at `x1`'s 0.19 m and ~0.5 px at `x5`'s
0.79 m. Matches the observed spread, and confirms "far and zoomed -> straighter"
as a real but small effect. Phase 4 checks the sign as well as the size: the
displacement must point radially outward from the frame centre and shrink with
distance.

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

Two explanations are ruled out by arithmetic:

- **Not parallax.** The thickness effect above is ~2 px at the worst distance,
  an order of magnitude short of 25 px, and it inflates rather than shrinks.
- **Not resolution.** All four captures fill the frame with the board, so they
  all land ~3000 source px across a 520-unit board and downsample by the same
  ~6x. The resampling load is uniform.

What is left is the segmentation. The size of the loss is the tell: 25 px on a
~100 px piece is one knob. The specific hypothesis is that `x4`'s missing HDR+
stack means different white balance and flatter local contrast at the piece
boundary, pushing boundary pixels into the green HSV band, which the
`BackgroundMaskConfig` docstring already names as the failure mode that
"silently erodes every piece". Losing a knob is the worst possible failure for
matching, because `SegmentMatcher.compute_similarity` gates on `SegmentShape`
compatibility before it ever measures shape, so an eroded `OUT` that reads as
`EDGE` returns `1e6` against its true partner.

That gives phase 4 a sharp, checkable prediction rather than a ranking exercise:
on `x4`, the shrunk pieces should have a segment whose `SegmentShape` disagrees
with the same physical segment on `x1`. Cheap to test, and it needs no ground
truth.

### the resolution ceiling

`correct_perspective` sizes the output purely from the board object points:

```
out_width  = board_width  + 2 * rect_margin
out_height = board_height + 2 * rect_margin
```

There is no dependence on the source photo. Confirmed by probe: every capture
rectifies to `620 x 760` from a 4080x3072 sensor frame.

Because the board fills the frame in all 12 shots, this discards roughly the
same ~6x of linear detail every time. So it is **not** a differentiator between
captures, and it does not belong in task 2. It is a standing ceiling on the
whole pipeline: a piece is ~100 x 100 px in the rectified sheet no matter what,
a segment is ~100 points, and about 6x of available detail is thrown away before
matching ever runs.

Whether spending that detail actually improves match scores is an experiment,
not an assumption, and it gets its own phase before any config knob is
committed (Q4, Q10, D8).

### what already exists for task 3

- `MatchResult.similarity_manual_` (alias `similarity_manual`) is a
  hand-annotation slot on each pair. Not used for ground truth (D7).
- `PieceMatcher` already has `save_matches_json` / `load_matches_json` and the
  SQLite equivalents, plus a `frozenset[SegmentId]` cache.
- `SegmentMatcher.compute_similarity` returns `1e6` for a shape-incompatible
  pair and otherwise a mean point distance after an affine fit. Lower is better,
  and it is **not** scale-normalised, so raw scores are only comparable within
  one rectified scale. Phase 5 handles that by rescaling at comparison time
  rather than changing the matcher (Q12, D11).

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
  makes it survive the scale experiment in phase 5, which a pixel-space truth
  would not.
- **D4**: the corpus (all 12 photos ingested and keyed by D2) is built once and
  shared by every later phase. Nothing else starts before it exists.
- **D5**: the phase 1 fix keeps the ring safety buffer as an explicit, named
  quantity rather than smuggling it in as `board.margin`. If a buffer is wanted
  it should be a knob with a stated reason, not a coincidence of units.
- **D6**: task 2 is reported over four named **capture conditions**, not over a
  zoom axis. EXIF shows all 12 shots share one lens, and that app, distance and
  digital upscale all move together, `x4` most of all. The confound is accepted
  rather than reshot (Q3); the honest reporting unit is the condition.
- **D7**: ground truth lives in its own truth file keyed by
  `(sheet_index, label, edge_pos)` and scoped to this picture set, not in
  `MatchResult.similarity_manual_`. That field is a per-pair float on a
  capture-specific result; the truth is a capture-independent set of pairs, and
  overloading the field would conflate "what the matcher scored" with "what is
  actually true".
- **D8**: the rectification scale is investigated as an **experiment first**
  (Q10). Phase 5 measures whether a higher rectified resolution improves match
  separation, and only proposes a config knob if it does. Rejected alternative:
  build the knob up front. It moves every pixel threshold in the codebase, so
  paying that cost before knowing the payoff is backwards.
- **D9**: every phase stays scratch-local to `24_investigate_matching/`. No
  `pipelines/` entry from this effort. Promotion is a separate call, made after
  the investigation says what is worth keeping.
- **D10**: `x4` gets one salvage attempt via mask/threshold tuning in phase 4
  (Q9). If per-condition preprocessing does not recover the lost extent, `x4` is
  ranked worst and the investigation moves on rather than chasing it.
- **D11**: `SegmentMatcher` is left un-normalised. Cross-scale comparisons in
  phase 5 divide the score by the scale factor at analysis time (Q12). Rejected
  alternative: normalise inside the matcher. That silently changes every score
  the rest of the codebase and the stored databases already hold.
- **D12**: the 12 pieces form **disjoint** groups (Q11). Phase 3 asserts that
  the true-pair graph is a disjoint union with no edge crossing between groups,
  which is a real completeness check even before the group sizes are known
  (Q13).

## phases

Phase 1 is an isolated bug fix and runs first. Phase 2 is the shared
prerequisite. Ground truth (phase 3) comes before the capture comparison
because the best-match score is the primary quality metric (Q6), and it is
stated in physical terms (D3) so the later scale experiment does not invalidate
it. Phase 5 also depends only on phase 3, not on phase 4; it is sequenced after
phase 4 to keep one variable moving at a time.

| #   | Phase                          | Plan file                      | Covers  |
| --- | ------------------------------ | ------------------------------ | ------- |
| 1   | Fix the interior over-crop     | `01_fix_interior_overcrop.md`  | task 1  |
| 2   | Labelled capture corpus        | `02_capture_corpus.md`         | -       |
| 3   | Ground-truth edge pairs        | `03_match_ground_truth.md`     | task 3  |
| 4   | Capture condition comparison   | `04_capture_quality.md`        | task 2  |
| 5   | Rectification scale experiment | `05_rectify_scale_experiment.md` | -     |
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
caught rather than silently joined on. Record the EXIF condition per capture
alongside, so phase 4 groups by condition rather than by filename. Scratch-local
(D9).

**Phase 3 - ground-truth edge pairs.**
Hand-drive the matcher over the 48 segments on the best capture condition and
record the true pairs in D3 form in the truth file (D7). Assert the disjoint-
group invariant (D12). Report the score separation between true and false pairs
as the baseline everything later is measured against.

**Phase 4 - capture condition comparison.**
Primary metric is the phase-3 best-match score per condition (Q6). Alongside it,
three cheap metrics that need no ground truth: `SegmentShape` agreement of the
same physical segment across conditions (the sharp `x4` prediction above),
bounding-box agreement, and contour point count. Also check the parallax sign
and magnitude against the `r * t / d` estimate. Attempt the `x4` salvage per
D10. Report over conditions, not zoom (D6).

**Phase 5 - rectification scale experiment.**
Re-rectify the corpus at 2x / 3x / 4x, rerun matching, and measure separation
against the phase-3 truth file, rescaling scores at comparison time (D11).
Everything in pixel units has to move with the scale for the run to be
meaningful: `crop_margin`, `min_area`, blur and erosion kernels, `pad`, and
`SlotGrid`. Outcome is a go/no-go on a real config knob, with the measured gain
attached (D8). The phase 3 truth file survives unchanged by construction (D3).

**Phase 6 - matching and preprocess tuning.**
Sweep preprocess and matcher parameters against the phase-3 ground truth at
whatever scale phase 5 settles on, with true-vs-false score separation as the
objective.

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
  Follow-up from the capture note and EXIF: it is more confounded than that.
  All 12 shots use one lens, and app, distance and digital upscale vary
  together, so there is no zoom axis at all. Reported as four named capture
  conditions instead (D6).
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
- Q9: the `x4` captures shrink every piece's bounding box, by up to 25 px in one
  axis. Is that a mask/threshold tuning problem we should fix (per-capture HSV
  bounds, or auto white balance compensation), or do we just rank `x4` worst and
  move on? It decides whether phase 4 ends in a report or in a code change.
  ANS: we can try and salvage it with a mask/threshold tuning fix, but if that
  fails we rank `x4` worst and move on.
- Q10: what output scale should phase 5 target? A fixed multiplier (2x, 3x), or
  a stated resolution in px per board unit that the config carries? The second
  is more work but makes every pixel threshold in the codebase interpretable in
  physical units instead of board-pixel units.
  ANS: before we go all in with a config knob, we can do some experiments to see
  if a different resolution improves the matching scores or not.
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

### open

- Q13: the groups are disjoint (Q11), but how many groups are there and how big
  is each? With the sizes, phase 3 can assert the exact true-pair count and know
  when the truth file is complete. Without them it can only assert disjointness
  and stop when hand-driving runs dry.
  ANS: dude i have no idea
- Q14: how large is the board physically, as displayed and photographed? Needed
  to turn board units into mm, which is what makes the parallax check
  quantitative rather than order-of-magnitude, and what a "px per mm" scale knob
  would be stated in if phase 5 says yes.
  ANS: longer edge of the board, all picture from the very edges, 16.5cm
- Q15: the `x4` shots have no HDR+ and no `SubjectDistance` in EXIF, so their
  capture distance is unknown. Do you remember roughly how far they were taken
  from, or should phase 4 estimate it from the board's apparent size and treat
  it as derived?
  ANS: derive it
