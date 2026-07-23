---
status: draft
---

# Phase 5 - Capture condition comparison

## Overview

Task 2 asked which zoom level gives the cleanest contours. EXIF says there is no
zoom level to rank: all 12 shots use the same 6.81 mm f/1.85 main sensor, and
app, subject distance and digital upscale move together. So this phase compares
four named **capture conditions** (D6) and says so plainly rather than implying
a zoom axis that does not exist.

Draft until phase 3 lands, because how much of the observed difference between
conditions is a capture property and how much is classifier instability is
exactly what phase 3 determines.

Context: [`00_start.md`](00_start.md), sections "what actually varies between
captures" and "the x4 captures lose piece extent". Depends on
[`04_match_ground_truth.md`](04_match_ground_truth.md) for the primary metric.

## The conditions

| capture | app           | 35mm eq | digital zoom | subject dist  | HDR+ |
| ------- | ------------- | ------- | ------------ | ------------- | ---- |
| x1      | Google Camera | 24      | none         | 0.19 m        | yes  |
| x2      | Google Camera | 48      | none         | 0.33-0.36 m   | yes  |
| x5      | Google Camera | 48      | 2.5x         | 0.75-0.79 m   | yes  |
| x4      | Open Camera   | -       | -            | derived below | no   |

## Goals

1. Rank the four conditions on contour quality, with the confound stated.
2. Establish whether `x4`'s lost piece extent is recoverable.
3. Derive the `x4` subject distance and the piece thickness from the data.

## Plan

### Metrics

Primary: the phase 4 best-match score, computed per condition (Q6). It is the
only metric that measures what the pipeline is actually for.

Secondary, and none of them need the truth file, so they can run while the
annotation is out:

- `SegmentShape` agreement against the confirmed shapes, per condition. The
  phase 3 fixture re-read as a per-condition score.
- bounding-box agreement of the same physical piece across conditions. Already
  discriminating: `x4` shrinks every piece, up to 25 px in one axis, which is
  5.9 mm of real board.
- contour point count.

### Salvage x4

`x4` loses roughly one knob per piece, and the shape table confirms the
consequence rather than just predicting it: `s0:A1 TOP` and `s2:A2 BOTTOM` are
knobs appearing and disappearing on `x4` specifically. The hypothesis is that
the missing HDR+ stack means different white balance and flatter local contrast
at the piece boundary, pushing boundary pixels into the green HSV band, which
the `BackgroundMaskConfig` docstring already names as the failure mode that
"silently erodes every piece".

One attempt at per-condition mask/threshold tuning (D10). If it does not recover
the lost extent, `x4` is ranked worst and the investigation moves on rather than
chasing it.

### Derive the geometry

Two numbers come out of the data rather than out of assumptions.

**`x4` subject distance** (Q15). Open Camera wrote no `SubjectDistance`. The
board's 165 mm long edge spans a known pixel count, the lens is 6.81 mm, and the
sensor is 9.83 x 7.37 mm (from the 24 mm equivalent and a 3.52 crop factor), so

```
d = f * H_real / h_on_sensor
```

Validate the method against `x1`/`x2`/`x5`'s recorded distances **before**
trusting it on `x4`.

**Piece thickness** (Q16, D17). No caliper, so invert the parallax relation
instead. The homography rectifies the board plane; a piece sits above it, so its
top face displaces radially outward by `r * t / d`. Three known distances plus
the measured displacements give `t` by least squares over all 12 pieces.

Expect it to be crude: the displacements are 1-4 px against integer centroids,
so the signal sits near the quantisation floor. Two things make it usable, fit a
piece **corner** rather than the centroid, since corners sit further out and so
move further, and fit all 12 pieces at once rather than reading rows.

Also check the sign, not just the magnitude: displacement must point radially
outward from the frame centre and shrink with distance. Predicted, with
`t ~ 2 mm` as the placeholder being replaced:

| capture | distance | predicted displacement |
| ------- | -------- | ---------------------- |
| x1      | 0.19 m   | 0.74 mm = 3.1 board px |
| x2      | 0.35 m   | 0.40 mm = 1.7 board px |
| x5      | 0.79 m   | 0.18 mm = 0.8 board px |

## Out of scope

- Rectification scale. Phase 6. It is uniform across conditions (the board fills
  the frame in all 12, so the ~5.8x discard is the same everywhere), so it is
  not a differentiator and does not belong here.
- Reshooting to break the confound. Rejected in D6.
- Correcting for thickness parallax in the pipeline. This phase measures it;
  acting on it would be separate work.

## Done when

- The four conditions are ranked on the primary metric, with the confound
  reported rather than glossed.
- The `x4` salvage has been attempted once and its outcome recorded either way.
- `x4`'s distance is derived, with the method validated against the three known
  distances first.
- Piece thickness is fitted, with its uncertainty stated honestly.
- `uv run pytest && uv run ruff check . && uv run pyright && uv run pre-commit run --all-files`
  passes.
