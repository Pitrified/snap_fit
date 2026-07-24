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
- 4 captures per sheet, 12 photos, all 3072x4080 portrait.

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

The board's long edge is 165 mm edge to edge (Q14), so 700 board units span
165 mm and **1 board unit = 0.236 mm** (4.24 units/mm). The board is 132 mm
wide. Every pixel figure below converts through that.

12 physical pieces total (3 sheets x 4 slots), 48 segments.

### what actually varies between captures

The capture note said distance was traded against zoom to keep the board filling
the frame. EXIF confirms it and says more:

| capture | app           | focal | 35mm eq | digital zoom | subject dist | HDR+ |
| ------- | ------------- | ----- | ------- | ------------ | ------------ | ---- |
| x1      | Google Camera | 6.81  | 24      | none         | 0.19 m       | yes  |
| x2      | Google Camera | 6.81  | 48      | none         | 0.33-0.36 m  | yes  |
| x5      | Google Camera | 6.81  | 48      | 2.5x         | 0.75-0.79 m  | yes  |
| x4      | Open Camera   | 6.81  | -       | -            | derived (Q15)| no   |

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

`x4` is off all three axes simultaneously: different app, no distance recorded,
no crop metadata. It is a fourth capture condition, not a fourth point on any
axis (Q3, D6). Its distance is derived from the board's apparent size in phase 5
(Q15): the board's 165 mm long edge spans a known pixel count, the lens is
6.81 mm, and the sensor is 9.83 x 7.37 mm (from the 24 mm equivalent), so
`d = f * H_real / h_on_sensor` recovers it. The same formula run on `x1`/`x2`/`x5`
checks the method against their recorded `SubjectDistance` before it is trusted
on `x4`.

The task framing "which zoom level is cleanest" therefore does not have a clean
answer, because there is no zoom axis. The answerable question is which of four
named capture conditions gives the best contours, and phase 5 reports it that
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

That 1-4 px spread is the parallax the capture note predicted, and with the
board size now known (Q14) it comes out the right size. The homography rectifies
the *board plane*; a piece sits a couple of mm above it, so its top face is
displaced radially outward by roughly `r * t / d`. Taking `t ~ 2 mm` as a
placeholder, an edge piece at `r ~ 70 mm` from the board centre, and
4.24 units/mm:

| capture | distance | predicted displacement |
| ------- | -------- | ---------------------- |
| x1      | 0.19 m   | 0.74 mm = 3.1 board px |
| x2      | 0.35 m   | 0.40 mm = 1.7 board px |
| x5      | 0.79 m   | 0.18 mm = 0.8 board px |

That is the observed 1-4 px spread, so "far and zoomed -> straighter" is real,
quantified, and small. Phase 5 checks the sign too: the displacement must point
radially outward from the frame centre and shrink with distance.

The thickness cannot be measured directly, there is no caliper (Q16), so phase 5
**inverts the relation instead**: three known distances and the measured
displacements give `t` by least squares over all 12 pieces. That turns the one
assumed input into a derived one. Expect it to be crude, because the observed
displacements are 1-4 px against integer centroids, so the signal sits near the
quantisation floor. Two things make it usable: fitting a piece *corner* rather
than the centroid, since corners sit further out and so move further, and using
all 12 pieces at once rather than eyeballing rows (D17).

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
`320 x 340`. 20 px lost left, right, top and bottom, which is 4.7 mm of real
board on each side.

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

### segment shape classification is unstable

This is the biggest finding, and it was not in any of the three tasks.

Classified all 48 segments under all 4 capture conditions and compared. **10 of
48 segments (21%) do not get the same `SegmentShape` across conditions**, and
the disagreements are not confined to one capture:

| segment        | x1   | x2   | x4   | x5   | kind          |
| -------------- | ---- | ---- | ---- | ---- | ------------- |
| s0:A1 TOP      | IN   | IN   | EDGE | IN   | knob lost     |
| s1:B1 RIGHT    | OUT  | EDGE | OUT  | IN   | three answers |
| s2:A1 BOTTOM   | IN   | EDGE | EDGE | IN   | knob lost     |
| s2:A1 RIGHT    | IN   | IN   | OUT  | IN   | inversion     |
| s2:A1 TOP      | OUT  | EDGE | OUT  | OUT  | knob lost     |
| s2:A2 LEFT     | OUT  | OUT  | IN   | OUT  | inversion     |
| s2:A2 BOTTOM   | EDGE | EDGE | OUT  | EDGE | knob invented |
| s2:B1 LEFT     | EDGE | IN   | IN   | IN   | knob lost     |
| s2:B1 BOTTOM   | IN   | IN   | OUT  | IN   | inversion     |
| s2:B1 RIGHT    | OUT  | EDGE | EDGE | EDGE | knob invented |
| s2:B2 TOP      | OUT  | IN   | EDGE | OUT  | three answers |

Sheet 2 accounts for 8 of the 11. `x4` is the odd one out in 6, but `x1` alone
is wrong twice and `x2` alone twice, so this is not simply "`x4` is bad".

Re-measured after phase 1, on untruncated contours. The count was 10 before that
fix, which matters more than the number does; see the next section.

### the crop fix moved the baseline, which is the phase 3 hypothesis in action

Phase 1 widened the crop by 20 px per side. The disagreement count went 10 -> 11
and the membership changed:

- `s0:B1 BOTTOM` became stable and left the list,
- `s1:B1 RIGHT` and `s2:A1 BOTTOM` became unstable and joined it,
- `s0:A1 TOP` **flipped sign**, from an `OUT` majority to an `IN` majority.

Nothing physical changed. Same pieces, same photo files; only the image border
moved. The pre-fix numbers were taken on truncated contours so they were never
the right baseline, but the mechanism this exposes is the point: a pure border
change propagates through `pad_rect` to the piece image size, to the
`build_cross_masked` thickness (literally `sum(shape)/2/4*1.05`), to
`find_corner`, to where segments get split.

That is the corner-placement chain phase 3 set out to test, demonstrated before
phase 3 starts. It also means shape counts are only comparable within one
pipeline configuration, which constrains phases 6 and 7 as well.

### the IN/OUT convention is sound; corner placement is the weak link

Checked independently of `ShapeDetector`: for each segment take the chord
between its endpoints and measure the largest perpendicular deviation, signed
outward from the piece centroid. A tab bulges outward, a socket inward.

Result across all 48 `x1` segments: **0 disagreements** with the assigned
`IN`/`OUT`. So `IN` = socket, `OUT` = tab, and the sign convention is not the
problem.

What this does *not* validate is where the corners are, since it uses the same
detected corners the classifier does, so a displaced corner misleads both
identically. `s0:A1` is the illustration: its tab sits near the top-left corner,
and depending on where that corner lands the tab belongs to either `TOP` or
`LEFT`. Post-fix it reads `LEFT: OUT` (deviation +28.5 px, the largest in the
set) with `TOP: IN`; pre-fix it read the other way. Neither is obviously wrong.
The corner decides, and the corner moves.

Deviation magnitude looked like a confidence measure at first: typical segments
bulge 17-25 px, five sit at 1-5 px, and four of those five are in the
disagreement list. **That claim did not survive the ground truth** (see below):
it predicts instability between conditions, but not correctness.

### measured against the hand-confirmed truth

All 48 shapes came back confirmed (Q17). Accuracy of the current classifier:

| condition | correct | |
| --------- | ------- | ---- |
| x1        | 41/48   | 85% |
| x2        | 42/48   | 88% |
| x4        | 40/48   | 83% |
| x5        | 42/48   | 88% |
| **majority vote** | **43/48** | **90%** |

So roughly one segment in eight is misclassified, and voting across four
captures recovers only a little of it.

The five the vote gets wrong:

| segment        | truth | vote | votes           | deviation | flagged? |
| -------------- | ----- | ---- | --------------- | --------- | -------- |
| s0:A1 TOP      | OUT   | IN   | IN/IN/EDGE/IN   | -11.2     | split    |
| s2:A1 BOTTOM   | OUT   | IN   | IN/EDGE/EDGE/IN | -11.9     | split    |
| s2:A1 LEFT     | IN    | OUT  | OUT/OUT/OUT/OUT | +13.4     | **none** |
| s2:A1 TOP      | EDGE  | OUT  | OUT/EDGE/OUT/OUT| +2.2      | split    |
| s2:B1 BOTTOM   | OUT   | IN   | IN/IN/OUT/IN    | -17.4     | split    |

`s2:A1 LEFT` is the important row. All four conditions agree, so nothing marks
it for review, and it is wrong. That is exactly the case D13 rejected the cheap
option for: had the 37 unanimous segments been taken on trust and only the 11
splits hand-checked, this error would have entered the truth file silently.

Three of the five are on `s2:A1`, one piece.

**Correction to the deviation-as-confidence idea.** Median |deviation| is 19.7 px
where the vote is right and 11.9 px where it is wrong, so there is a signal, but
it is far too weak to filter on: the five lowest-deviation segments contain only
one of the five errors, while `s2:B1 BOTTOM` (-17.4) and `s2:A1 LEFT` (+13.4)
are wrong at perfectly confident magnitudes. Useful as a tie-breaker at best,
not as a gate.

### the bottleneck is corner placement, not contour quality

The hand annotation named the mechanism directly, twice: `s0:A1` "the problem is
the corner detection: left/top segments are not split correctly (left segment
reaches into the top one)" and `s2:B1` "contour split into segment is wrong,
left segment reaches into the bottom one".

That is confirmed by a blur sweep against the truth. Blur controls how faithful
the contour is, and it does **not** move shape accuracy at all:

| blur ksize | sigma  | x1 | x2 | x4 | x5 | vote  |
| ---------- | ------ | -- | -- | -- | -- | ----- |
| 21         | 3.5 px | 41 | 42 | 40 | 42 | 43/48 |
| 15         | 2.6 px | 42 | 42 | 38 | 42 | 43/48 |
| 11         | 2.0 px | 42 | 43 | 41 | 41 | 43/48 |
| 7          | 1.4 px | 42 | 42 | 43 | 41 | 42/48 |
| 5          | 1.1 px | 41 | 42 | 41 | 42 | 42/48 |
| 3          | 0.8 px | 42 | 41 | 41 | 41 | 42/48 |

Flat across the range, and piece counts stay at 4 throughout. So a better
contour does not buy a better shape verdict. The corners land wrong regardless,
and once a segment boundary is in the wrong place no amount of contour precision
recovers the right answer.

### what the blur actually costs, and where it will matter

`blur_kernel_size` is the kernel *support*, not the radius: `apply_gaussian_blur`
passes `sigma=0`, so OpenCV derives `sigma = 0.3*((k-1)*0.5-1)+0.8`, which is
**3.5 px** for `k=21`. On a ~100 px piece that is a 3.5% radius, on a ~25 px knob
about 14%.

It is not free, though. On `s2:A1`, contour area is 4138 px^2 at blur 21 against
6043 px^2 with blur off, so the blur is eating roughly 30% of the piece, about
2-3 px of boundary all the way round.

That matters for **matching** even though it does not matter for shape. A
systematic inward shift does not cancel between a true pair, because a tab
shrinks while its matching socket grows, so the two boundaries move in opposite
senses and the error adds rather than subtracts. On a score that is a mean point
distance, 2-3 px per side is large. Phase 7 should treat blur as a candidate
lever for the *score*, having established here that it is not one for the shape.

### the erosion pass grows pieces, it does not shrink them

The hand annotation attributes two pieces' problems to "high erosion, contour is
quite inside the piece". The symptom is real, the mechanism is not: on the
HSV-mask path the binary is background=255 and pieces=0, so `cv2.erode` shrinks
the *background* and therefore grows the piece.

Measured on `s2:A1`:

| variant                | bbox   | contour area |
| ---------------------- | ------ | ------------ |
| erosion only (2, 0)    | 71x105 | 4568         |
| default (ero 2, dil 1) | 69x103 | 4138         |
| no morphology (0, 0)   | 67x101 | 3710         |
| dilation only (0, 1)   | 64x86  | 3294         |

Erosion pushes the contour out, dilation pulls it in, and the default nets
slightly outward of no-morphology at all. The blur is what sits the contour
inside the piece. Worth recording so phase 7 does not spend its sweep on the
wrong parameter.

This sits upstream of everything else in task 3. `SegmentMatcher.compute_similarity`
calls `is_compatible` **before** it measures any shape, and `EDGE` is
incompatible with everything, `IN` with `IN`, `OUT` with `OUT`. So a segment
that flips returns `1e6` against its true partner and never gets scored. Tuning
the score is pointless while a fifth of the segments can fail the gate.

Two mechanisms are visible in the code, both worth naming:

**The adaptive threshold is self-defeating.** `_detect_shape_adaptive` sets
`flat_th = max(10.0, np.std(s1_xs) * 1.5)`, so the threshold for detecting a
knob is derived from the spread that the knob itself creates. A stronger knob
raises its own bar. Any small change in the contour moves `std`, which moves the
threshold, which flips the verdict. That is exactly the observed behaviour.

**Corner placement depends on the bounding box, which we already know moves.**
The chain is all in code that has been read:

```
bbox varies (up to 25 px, see below)
  -> pad_rect region varies
  -> piece image shape varies
  -> build_cross_masked thickness = sum(shape)/2/4*1.05 varies
  -> find_corner lands elsewhere
  -> match_corners picks different split indices
  -> ShapeDetector sees a different point set
  -> shape flips
```

An inversion (`OUT` -> `IN`) cannot come from the transform: the alignment uses
`cv2.estimateAffinePartial2D`, a 4-DOF similarity with no reflection, so
handedness is preserved. It has to come from the segment boundaries moving far
enough that the chord falls on the other side of the mass, which is what a
displaced corner does. This is the leading hypothesis, not a confirmed cause,
and phase 3 tests it by correlating shape disagreements against bbox
disagreements per segment.

**Majority vote across the four conditions is a usable denoiser.** Every
`EDGE` that appears in only one condition is contradicted by the other three,
and the two that appear in three of four (`s2:A2 BOTTOM`, `s2:B1 RIGHT`) look
genuine. That gives a defensible shape label per segment without hand-labelling
all 48, and it is how phase 4 seeds the truth file (D13).

### what the flat-edge census does and does not tell us

Majority vote leaves exactly **2 genuinely flat segments** out of 48, both on
sheet 2. That rules out a whole class of structure: a rectangular assembly of
`r x c` pieces has `2(r+c)` flat border edges, so even a single 3x4 block would
need 14. Two flat edges across 12 pieces means these are interior fragments cut
out of a larger puzzle, not self-contained rectangles.

So the census does **not** pin down the grouping, and Q13 cannot be recovered by
measurement any more than from memory. It is deferred: the pieces will be
matched by hand later, and that hand-matching becomes the truth (D12). What the
census still gives is a real invariant to check the hand-matching against:
exactly 2 segments should end up with no partner, and the other 46 should pair
up or be explained.

### the x4 captures lose piece extent

Bounding boxes of the same physical piece across conditions:

| sheet | label | x1     | x2     | x4 (IMG) | x5     |
| ----- | ----- | ------ | ------ | -------- | ------ |
| 0     | A1    | 105x105| 104x106| **97x83**| 104x105|
| 0     | B1    | 86x117 | 85x117 | **61x111**| 86x117|
| 0     | A2    | 79x111 | 78x109 | **72x88**| 78x110 |
| 1     | B2    | 91x94  | 93x94  | **70x90**| 93x96  |
| 2     | A2    | 101x96 | 98x94  | **76x91**| 98x97  |
| 2     | B2    | 103x85 | 97x67  | **83x66**| 100x84 |

`x4` shrinks the piece on every single row, sometimes by 25 px in one axis
(sheet 0 B1: 86 wide becomes 61, which is 5.9 mm of real board). `x2` shrinks on
sheet 2 as well; `x1` and `x5` agree with each other throughout.

Two explanations are ruled out by arithmetic:

- **Not parallax.** The thickness effect is ~3 px at the worst distance, an
  order of magnitude short of 25 px, and it inflates rather than shrinks.
- **Not resolution.** All four conditions fill the frame with the board, so they
  all land ~4080 source px across a 165 mm edge and downsample by the same
  ~5.8x. The resampling load is uniform.

What is left is the segmentation. The size of the loss is the tell: 25 px on a
~100 px piece is one knob. The hypothesis is that `x4`'s missing HDR+ stack
means different white balance and flatter local contrast at the piece boundary,
pushing boundary pixels into the green HSV band, which the
`BackgroundMaskConfig` docstring already names as the failure mode that
"silently erodes every piece".

And the shape table above confirms the consequence rather than just predicting
it: `s0:A1 TOP` and `s2:A2 BOTTOM` are exactly knobs appearing and disappearing
on `x4`. The bbox loss and the shape instability are the same defect measured
two ways.

### the resolution ceiling

`correct_perspective` sizes the output purely from the board object points:

```
out_width  = board_width  + 2 * rect_margin
out_height = board_height + 2 * rect_margin
```

There is no dependence on the source photo. Confirmed by probe: every capture
rectifies to `620 x 760` from a 3072x4080 sensor frame.

In physical units, now that the board is known to be 165 mm on its long edge:

```
rectified   700 units / 165 mm  =  4.24 px/mm   (~108 dpi)
source     4080 px    / 165 mm  = 24.7 px/mm    (~628 dpi)
discarded  5.8x linear
```

Because the board fills the frame in all 12 shots, that ~5.8x is discarded
equally every time. So it is **not** a differentiator between captures, and it
does not belong in task 2. It is a standing ceiling on the whole pipeline: a
piece is ~100 x 100 px rectified, a segment is ~100 points, and most of the
available detail is thrown away before matching ever runs.

Whether spending that detail improves match scores is an experiment, not an
assumption, and it gets its own phase before any config knob is committed (Q4,
Q10, D8). Candidate scales in physical terms: 2x = 8.5 px/mm, 3x = 12.7 px/mm,
4x = 17 px/mm, against an optical ceiling of ~24.7 px/mm at `x1` and rather less
at `x5` given its 2.5x digital upscale.

### what already exists for task 3

- `MatchResult.similarity_manual_` (alias `similarity_manual`) is a
  hand-annotation slot on each pair. Not used for ground truth (D7).
- `PieceMatcher` already has `save_matches_json` / `load_matches_json` and the
  SQLite equivalents, plus a `frozenset[SegmentId]` cache.
- `SegmentMatcher.compute_similarity` returns `1e6` for a shape-incompatible
  pair and otherwise a mean point distance after an affine fit. Lower is better,
  and it is **not** scale-normalised, so raw scores are only comparable within
  one rectified scale. Phase 6 handles that by rescaling at comparison time
  rather than changing the matcher (Q12, D11).

### the metadata text line sits inside the piece area

Surfaced by the phase 1 fix: with the crop no longer overshooting, the
human-readable identity line ("gd_s 01/04 2026-07-23") is now visible at the
bottom of the cropped sheet.

It is not a regression, it is a board-generation flaw the over-crop was hiding.
`SheetMetadataEncoder._place_text` draws at `(x0, y0 - 4)` where `y0` is the
**top** of the QR strip, and `putText`'s y is the baseline, so the text extends
upward from there:

```
text occupies board y   446 .. 456
piece area ends at      460
```

Entirely inside the region reserved for pieces. The method's own docstring says
"just above the QR strip", so the placement is deliberate; what is wrong is that
"just above the strip" *is* the piece area.

Measured impact on this dataset: **none**.

- raw contour count is identical with the old and new crop on all 12 photos
  (7/7, 6/6, 5/5, 4/4), so the wider crop introduces no contour at all, not even
  a sub-threshold one,
- no contour falls in the text band on any photo,
- the lowest piece clears the band by 38-54 px (9-13 mm of real board),
- mean grey in the text band is within a few levels of the rest of the sheet.

The reason is `blur_kernel_size = 21`: a 21x21 Gaussian runs before the HSV mask,
and the text is ~10 px tall with ~1 px strokes in the rectified image, so it
dissolves into the background completely.

That last point is the catch, and it is a constraint on phase 7 rather than a
problem now. The text is invisible *because of a parameter phase 7 sweeps*. Drop
the blur far enough and it becomes contours. A piece placed in the bottom ~14 px
of the piece area would also overlap it, which nothing prevents; this dataset
just happens not to do that.

The real fix is in board generation, moving the text inside the QR strip instead
of above it. It does not help already-photographed boards, so it is out of scope
here and recorded as a spin-off candidate (Q20).

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
  makes it survive the scale experiment in phase 6, which a pixel-space truth
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
  (Q10). Phase 6 measures whether a higher rectified resolution improves match
  separation, and only proposes a config knob if it does. Rejected alternative:
  build the knob up front. It moves every pixel threshold in the codebase, so
  paying that cost before knowing the payoff is backwards.
- **D9**: every phase stays scratch-local to `24_investigate_matching/`. No
  `pipelines/` entry from this effort. Promotion is a separate call, made after
  the investigation says what is worth keeping.
- **D10**: `x4` gets one salvage attempt via mask/threshold tuning in phase 5
  (Q9). If per-condition preprocessing does not recover the lost extent, `x4` is
  ranked worst and the investigation moves on rather than chasing it.
- **D11**: `SegmentMatcher` is left un-normalised. Cross-scale comparisons in
  phase 6 divide the score by the scale factor at analysis time (Q12). Rejected
  alternative: normalise inside the matcher. That silently changes every score
  the rest of the codebase and the stored databases already hold.
- **D12**: the 12 pieces form **disjoint** groups (Q11), the group sizes are not
  known to anyone (Q13), and the flat-edge census cannot recover them. So the
  grouping is **supplied by hand, later**, and that hand-matching is the truth.
  Phase 4 splits around that hand-off: everything that prepares for it runs now,
  the transcription runs when the answer arrives. Phase 4 asserts structure, not
  a count: disjointness, at most one partner per segment, and exactly 2
  partnerless flat segments.
  Rejected alternative: have the matcher discover the grouping and confirm it by
  eye. It sounds cheaper but it is the same circularity D15 rejects, and with an
  unknown group count there is no signal for when to stop looking.
  The pairs and the per-segment shapes (D13) are both hand judgements over the
  same 12 pieces, so they are collected as **one hand-off**, not two: a single
  annotation sheet produced at the end of phase 2, returned once, consumed by
  phases 3 and 4.
- **D13**: segment shapes are **confirmed by hand for all 48** (Q17), with the
  majority vote across the four conditions used only to pre-fill the annotation
  sheet and to flag the 10 split ones for attention. That makes phase 3's
  acceptance criterion "agrees with truth" rather than "agrees with itself".
  Rejected alternative: accept the vote as truth and hand-check only the 10
  splits. A unanimous wrong answer is exactly what a systematic classifier bug
  produces, so the vote cannot certify the 38.
- **D14**: shape-classification stability is its own phase, placed **before**
  ground truth. Rejected alternative: treat it as one metric inside the capture
  comparison, which is where it started. It gates `compute_similarity` before
  any score is computed, so a fifth of the segments cannot be scored at all
  until it is addressed. It is a correctness problem, not a quality metric.
- **D15**: ground truth is **human-authored**, not matcher-derived. The pieces
  are matched by hand against the physical pieces (Q13); the matcher never gets
  a vote on what is true.
  Rejected alternative: accept the matcher's top-N as truth. That bakes the
  matcher's current bias into the yardstick used to measure the matcher, and
  every later phase would be measuring agreement with itself.
- **D16**: shape incompatibility becomes a **score penalty, not a hard gate**
  (Q18). One misclassified segment currently deletes a true pair silently, with
  no trace in the results, which is the worst possible failure mode for a
  yardstick. As a penalty the pair still ranks, just badly, and the mistake is
  visible and recoverable.
  Constraint: `1e6` is currently overloaded across four unrelated meanings, and
  only the first of them changes. `SegmentMatcher` returns it for shape
  incompatibility; `PieceMatcher` for a missing segment; `grid/suggestion._NO_SCORE`
  for no placed neighbour or an uncached pair; `interactive_service` writes it as
  the user-rejected marker. The penalty must therefore stay bounded well below
  `1e6` so a penalised pair can never be confused with any of the three
  sentinels that remain.
  Consequence: the gate currently prunes, so removing it means every pair gets
  scored. At 48 segments that is ~1100 pairs and irrelevant, but it is a real
  cost at puzzle scale and should be noted rather than discovered later.
  The penalty lands as a **config value in phase 3** with a provisional default,
  is computed from phase 4's measured true-vs-false separation, and has its
  default fixed in phase 7 (Q19). So the mechanism ships before the number is
  known, and the number is derived rather than guessed.
- **D17**: piece thickness is **derived, not measured** (Q16). Phase 5 fits it
  from the parallax displacement across the three known subject distances.
  Rejected alternative: leave `t = 2 mm` as an assumption. It is the only
  unmeasured input to the one physical-geometry claim in this document, and the
  data to pin it down has already been captured.

## phases

Phase 1 is an isolated bug fix and runs first. Phase 2 is the shared
prerequisite. Phase 3 comes next because shape classification gates the matcher
outright (D14), so neither the truth file nor any score comparison is meaningful
until it is understood. Ground truth (phase 4) precedes the capture comparison
because the best-match score is the primary quality metric (Q6). Phase 6 depends
only on phase 4, and is sequenced after phase 5 to keep one variable moving at
a time.

The one external dependency is the hand annotation: the pairs (Q13) and the
per-segment shapes (Q17). Both are judgements over the same 12 pieces, so phase
2 ends by producing one annotation sheet and handing it over (D12). Phase 3 can
start against the majority vote while it is out; only its acceptance number and
phase 4's truth file actually wait.

| #   | Phase                          | Plan file                        | Covers  |
| --- | ------------------------------ | -------------------------------- | ------- |
| 1   | Fix the interior over-crop     | `01_fix_interior_overcrop.md`    | task 1  |
| 2   | Corpus and annotation hand-off | `02_capture_corpus.md`           | -       |
| 3   | Segment shape stability        | `03_shape_stability.md`          | task 3  |
| 4   | Ground-truth edge pairs        | `04_match_ground_truth.md`       | task 3  |
| 5   | Capture condition comparison   | `05_capture_quality.md`          | task 2  |
| 6   | Rectification scale experiment | `06_rectify_scale_experiment.md` | -       |
| 7   | Matching and preprocess tuning | `07_matching_tuning.md`          | task 3  |

**Phase 1 - fix the interior over-crop.**
`crop_margin` becomes `marker_length + rect_margin`, plus an explicit named ring
buffer defaulting to 0 (D5); `crop_offset` becomes `ring_start`. Regression test
asserting the cropped sheet equals the piece area for a known board geometry.
Verify sheet 0's B2 is no longer flush after the change, and that no ArUco
sliver appears as a contour. Update `docs/guides/coordinate_spaces.md` (it
hardcodes 170 / 140 / 660x940) and `docs/library/puzzle/sheet_aruco.md`.

**Phase 2 - corpus and annotation hand-off.**
Ingest all 12 photos, key every piece by `(sheet_index, label)`, persist pieces
and segments. Assert 4 pieces and 4 distinct labels per capture, and centroid
agreement across the 4 captures of each sheet, so a regression in labelling is
caught rather than silently joined on. Record the EXIF condition per capture
alongside, so later phases group by condition rather than by filename.
Scratch-local (D9).

Then produce the **annotation sheet**, the single hand-off (D12): the 12 piece
crops at a consistent scale, each tagged with its `(sheet, label)`, each of its
four edges marked and pre-filled with the majority-vote shape, and the 10 split
segments flagged. It comes back carrying two things, the confirmed shape per
segment (D13) and the pairs written as `s0:A1 RIGHT <-> s2:B1 LEFT` (D15).
Getting this right is most of the phase: if the sheet is awkward to annotate,
the hand pass is where the whole plan stalls.

**Phase 3 - segment shape stability.**
Reproduce the 10/48 disagreement table as a fixture. Test the corner-placement
hypothesis by correlating shape disagreements against bbox disagreements per
segment. Attack the self-defeating `flat_th = 1.5 * std` threshold: candidates
are an absolute threshold in mm (now that 4.24 units/mm is known), a threshold
from the segment chord length rather than its deviation, or measuring signed
area between the segment and its chord instead of counting points. Success is measured against the hand-confirmed
shapes (D13), not against self-consistency, so a classifier that hedges to
`WEIRD` everywhere scores badly rather than perfectly. Work can start against
the majority vote and be re-scored when the annotation returns.

Separately and independently of the classifier: convert `is_compatible` from a
hard gate into a score penalty (D16), keeping the penalty bounded well below the
three `1e6` sentinels that stay. This is worth doing even if the classifier
improves, because it makes a misclassification visible instead of silent. The
penalty ships as a config value with a provisional default; the real number
comes from phase 4 and is fixed in phase 7 (Q19).

**Phase 4 - ground-truth edge pairs.**
Transcribe the returned annotation into the truth file, in D3 terms (D7), and
write its loader and the structural assertions: disjointness, at most one
partner per segment, and exactly 2 partnerless flat segments. Those assertions
are the check on the hand pass, so they run against it rather than being
asserted of it. Report the score separation between true and false pairs as the
baseline everything later is measured against.

Phases 5 and 6 need only that baseline for their primary metric, and both carry
secondary metrics that need no truth at all, so they can start against those if
the annotation is still out.

**Phase 5 - capture condition comparison.**
Primary metric is the phase-4 best-match score per condition (Q6). Alongside it,
three metrics that need no ground truth: `SegmentShape` agreement (the phase-3
fixture, re-read as a per-condition score), bounding-box agreement, and contour
point count. Derive the `x4` subject distance from apparent board size and
validate the method against the recorded distances first (Q15). Check the
parallax sign and magnitude against the `r * t / d` table, then invert it to fit
the piece thickness over all 12 pieces, using corner displacement rather than
centroid for signal (D17). Attempt the `x4` salvage per D10. Report over
conditions, not zoom (D6).

**Phase 6 - rectification scale experiment.**
Re-rectify the corpus at 2x / 3x / 4x (8.5 / 12.7 / 17 px/mm), rerun matching,
and measure separation against the phase-4 truth file, rescaling scores at
comparison time (D11). Everything in pixel units has to move with the scale for
the run to be meaningful: `crop_margin`, `min_area`, blur and erosion kernels,
`pad`, and `SlotGrid`. Outcome is a go/no-go on a real config knob, with the
measured gain attached (D8). The phase 4 truth file survives unchanged by
construction (D3).

**Phase 7 - matching and preprocess tuning.**
Sweep preprocess and matcher parameters against the phase-4 ground truth at
whatever scale phase 6 settles on, with true-vs-false score separation as the
objective. Fix the default shape-incompatibility penalty here, computed from
that separation (D16, Q19).

Phases 5-7 stay `draft` until phase 3 lands; their shape depends on how much of
the instability turns out to be fixable.

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
- Q13: the groups are disjoint (Q11), but how many groups are there and how big
  is each? With the sizes, phase 3 can assert the exact true-pair count and know
  when the truth file is complete. Without them it can only assert disjointness
  and stop when hand-driving runs dry.
  ANS: dude i have no idea
  Follow-up: the flat-edge census cannot recover it either. Majority vote leaves
  only 2 flat segments in 48, far too few for any rectangular assembly, so these
  are interior fragments of a bigger puzzle.
  **Deferred**: the pieces will be matched by hand later, and that becomes the
  truth (D12, D15). Collected together with the shape confirmations (Q17) on the
  annotation sheet that phase 2 hands off.
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

- Q16: what is the piece thickness? 2 mm is assumed above, and it is the only
  unmeasured input to the parallax prediction. A caliper reading turns that
  table from an order-of-magnitude check into a real one, and it is the number
  that would let the pipeline correct thickness parallax rather than just
  tolerate it.
  ANS: no caliper available
  Follow-up: derived instead. Three known subject distances and the measured
  displacements determine `t` by least squares, so the assumption is removed
  without a caliper (D17).
- Q17: phase 3 needs an acceptance criterion for shape classification, and
  "all four conditions agree" is not sufficient on its own, because a classifier
  that returns `WEIRD` everywhere would score perfectly. Should the phase 4
  truth file also carry a human-confirmed `IN`/`OUT`/`EDGE` per segment, so
  stability is measured against truth rather than against self-consistency? It
  is 48 judgements, most already settled by the majority vote.
  ANS: by hand, i will check them
  Follow-up: collected in the same hand-off as the pairs, since both are
  judgements over the same 12 pieces (D12, D13).
- Q18: should a spurious `EDGE` be able to delete a true pair? `is_compatible`
  currently hard-gates on it, so one bad classification silently removes a
  correct match with no trace. Options are to keep the gate, downgrade `EDGE` to
  a score penalty, or treat a low-confidence shape as `WEIRD` (which already
  passes the gate). This is phase 3 work but it changes what phase 4 can even
  observe, so it is worth settling early.
  ANS: is compatible should be a score penalty, not a hard gate.
  Follow-up: constrained by the `1e6` sentinel being overloaded four ways, only
  one of which changes (D16).

- Q19: how big should the shape-incompatibility penalty be (D16)? It has to be
  large enough that a true pair always outranks a shape-mismatched one, and
  small enough to stay well under `1e6`. Phase 4's measured separation between
  true and false pairs gives the scale to set it from, which argues for landing
  D16 as a config value in phase 3 and only fixing its default in phase 7.
  ANS: we'll compute it from the phase 4 separation, and land it as a config
  value in phase 3. The default is fixed in phase 7.

### open

- Q20: the metadata text line is drawn inside the piece area, not inside the QR
  strip (see the finding above). Harmless on this dataset, but only because the
  21 px blur erases it, and phase 7 sweeps that blur. Fixing
  `SheetMetadataEncoder._place_text` changes board generation and cannot help
  boards already photographed, so it does not belong in this effort. Spin it out
  as its own feature folder, or leave it as a note here?
  ANS: mark as note.
  So: no spin-off folder. It stays recorded in the finding above, with the
  blur-sweep constraint carried in `07_matching_tuning.md`. Whoever next touches
  board generation should move the text inside the QR strip.
