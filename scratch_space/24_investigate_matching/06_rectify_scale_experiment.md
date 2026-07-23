---
status: draft
---

# Phase 6 - Rectification scale experiment

## Overview

`correct_perspective` sizes its output purely from the board object points, with
no dependence on the source photo, so every capture rectifies to 620x760 no
matter what. In physical terms, now that the board is known to be 165 mm on its
long edge:

```
rectified   700 units / 165 mm  =  4.24 px/mm   (~108 dpi)
source     4080 px    / 165 mm  = 24.7 px/mm    (~628 dpi)
discarded  5.8x linear
```

Because the board fills the frame in all 12 shots, that ~5.8x is discarded
equally every time. It is not a differentiator between conditions, which is why
it is not part of task 2. It is a standing ceiling on the whole pipeline: a
piece is ~100x100 px rectified and a segment ~100 points, and most of the
captured detail is thrown away before matching runs.

Whether spending that detail improves match scores is an experiment, not an
assumption (D8). This phase measures it and produces a go/no-go on a config
knob, rather than building the knob first.

Context: [`00_start.md`](00_start.md), section "the resolution ceiling". Depends
on [`04_match_ground_truth.md`](04_match_ground_truth.md) for the truth to
measure against. Independent of phase 5, and sequenced after it only to keep one
variable moving at a time.

## Goals

1. Measure whether higher rectified resolution improves true-vs-false
   separation.
2. Produce a go/no-go on a real config knob, with the measured gain attached.

## Plan

- Re-rectify the corpus at 2x / 3x / 4x, which in physical terms is 8.5 / 12.7 /
  17 px/mm, against an optical ceiling of ~24.7 px/mm at `x1` and rather less at
  `x5` given its 2.5x digital upscale.
- Move everything in pixel units with the scale, or the run measures the wrong
  thing: `crop_margin`, `min_area`, the blur and erosion kernels, `pad` in
  `Piece.from_contour`, and `SlotGrid`. A scale change that leaves `min_area`
  fixed silently changes which contours survive filtering.
- Re-run matching and measure separation against the phase 4 truth file. The
  truth is in `(sheet_index, label, edge_pos)` terms (D3), so it survives the
  rescale unchanged. That was the point of stating it physically.
- Compare across scales by **rescaling scores at analysis time** (D11):
  `SegmentMatcher` returns a mean point distance and is not scale-normalised, so
  raw scores are only comparable within one scale. Divide by the scale factor
  when comparing. `SegmentMatcher` itself is left alone, because normalising
  inside it would silently change every score the rest of the codebase and the
  stored databases already hold.
- Watch whether shape-classification stability improves with scale as a side
  effect. If phase 3 could not fully fix the classifier, more resolution may do
  some of the work, and that is worth knowing even if the scale knob is
  otherwise rejected.

## Out of scope

- Building the config knob if the experiment says the gain is not there. That is
  the whole point of running the experiment first.
- Restating every pixel threshold in the codebase in physical units. That was
  the more ambitious reading of Q10 and is deferred until there is a reason.
- Correcting thickness parallax, which is a geometry fix, not a resolution one.

## Done when

- Separation is measured at 1x / 2x / 3x / 4x against the phase 4 truth.
- A go/no-go on the config knob is recorded, with the measured gain, or the
  measured absence of one.
- If go: what the knob should be stated in (a multiplier, or px/mm) is decided
  with the numbers in hand.
- `uv run pytest && uv run ruff check . && uv run pyright && uv run pre-commit run --all-files`
  passes.
