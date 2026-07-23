---
status: draft
---

# Phase 7 - Matching and preprocess tuning

## Overview

The original task 3 ask: test things in the matching code and the preprocessing
config to see how far the matching scores can be pushed. It runs last because
every input it needs is produced by an earlier phase, and because tuning against
an unstable classifier or a truncated contour would be tuning against noise.

Draft until phases 3 and 6 land. What is worth sweeping depends on what phase 3
leaves unfixed and what scale phase 6 settles on.

Context: [`00_start.md`](00_start.md). Depends on
[`04_match_ground_truth.md`](04_match_ground_truth.md) for the objective and
[`06_rectify_scale_experiment.md`](06_rectify_scale_experiment.md) for the scale
to run at.

## Goals

1. Improve true-vs-false score separation against the phase 4 ground truth.
2. Fix the shape-incompatibility penalty default from measured data.

## Plan

- Sweep at whatever scale phase 6 settles on, with true-vs-false separation as
  the single objective. Separation, not raw score: a change that lowers every
  score equally has improved nothing.
- Preprocess candidates, from `SheetPreprocessConfig`: the HSV mask bounds
  (whose value floor the docstring already documents as tuned from real
  captures, safe band 60-120), blur kernel, erosion and dilation iterations. The
  erosion pass is a prime suspect for knob loss.
- Matcher candidates, from
  [`SegmentMatcher.match_shape`](../../src/snap_fit/image/segment_matcher.py#L50):
  the two `MAYBE` comments in that method are open design questions left by the
  original author, and this is the phase that answers them with data. Namely
  whether to rescale the distance by the distance between segment ends, and
  whether to use the mean rather than the total. Also the point-correspondence
  scheme itself, which currently walks index `i1` against `floor(i1 * ratio)`,
  a nearest-index correspondence that will misalign wherever the two segments
  are sampled at different densities.
- Fix the shape-incompatibility penalty default (D16, Q19), computed from the
  phase 4 separation: large enough that a true pair always outranks a
  shape-mismatched one, small enough to stay well below the three `1e6`
  sentinels that remain.

## Out of scope

- Changing the ground truth to fit the results. If a "false" pair scores
  suspiciously well, that is a finding to report and check by eye, not a licence
  to edit the yardstick.
- The solver and grid scoring. This phase stops at segment-pair scores.
- Normalising `SegmentMatcher` internally (D11).

## Done when

- The sweep is run and the best configuration recorded, with its separation
  against the phase 4 baseline.
- The penalty default is set from measured data, not guessed.
- Any change that lands in `src` carries a test.
- Findings that did not pan out are written down too, so the next session does
  not repeat them.
- `uv run pytest && uv run ruff check . && uv run pyright && uv run pre-commit run --all-files`
  passes.
