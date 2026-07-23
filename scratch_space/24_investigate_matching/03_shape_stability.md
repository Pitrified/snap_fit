---
status: planned
---

# Phase 3 - Segment shape stability

## Overview

10 of 48 segments (21%) get a different `SegmentShape` depending on which of the
four captures you look at. Same physical segment, same board, four photos, and
the answers include sign inversions (`OUT` becoming `IN`) and one segment with
three different verdicts.

This gates everything in task 3. `SegmentMatcher.compute_similarity` calls
`is_compatible` **before** it measures any shape, and returns `1e6` if the pair
fails. `EDGE` is incompatible with everything; `IN`+`IN` and `OUT`+`OUT` are
rejected. So a segment that flips returns `1e6` against its true partner and is
never scored at all. Tuning scores while a fifth of segments can fail the gate
is wasted effort, which is why this precedes ground truth (D14).

Context: [`00_start.md`](00_start.md), section "segment shape classification is
unstable". Depends on [`02_capture_corpus.md`](02_capture_corpus.md).

## The observed instability

Post-phase-1 baseline, on untruncated contours:

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

Sheet 2 accounts for 8 of 11. `x4` is the odd one out in 6, but `x1` alone is
wrong twice and `x2` twice, so this is not reducible to "`x4` is a bad capture".

### the hypothesis is already partly confirmed

Phase 1 changed only the crop width, by 20 px per side. That moved the count
from 10 to 11, changed which segments are unstable, and **flipped `s0:A1 TOP`
from an `OUT` majority to an `IN` majority**. No piece moved; only the image
border did.

So the correlation study below is no longer testing whether the corner chain
matters. It is measuring how much. Phase 2 also handed over two results that
narrow the work:

- **the sign convention is fine.** Comparing each segment's assigned `IN`/`OUT`
  against the sign of its chord deviation gives 0 disagreements in 48. `IN` is a
  socket, `OUT` is a tab. Do not go looking for a sign bug.
- **deviation magnitude is a usable confidence measure.** Typical segments bulge
  17-25 px; five sit at 1-5 px, and four of those five are in the table above.
  The current `flat_th = 1.5 * std` discards exactly this signal.

## Goals

1. Reproduce the table as a fixture that fails when the count gets worse.
2. Establish whether corner placement is the mechanism.
3. Reduce the disagreement count, measured against hand-confirmed shapes.
4. Make a misclassification visible rather than silent (D16).

## Plan

### Test the corner-placement hypothesis first

Before changing any threshold, establish the mechanism. The chain, all in code
already read:

```
bbox varies (up to 25 px between conditions)
  -> pad_rect region varies
  -> piece image shape varies
  -> build_cross_masked thickness = sum(shape)/2/4*1.05 varies
  -> find_corner lands elsewhere
  -> match_corners picks different split indices
  -> ShapeDetector sees a different point set
```

Test it by correlating, per segment, shape disagreement against bbox
disagreement and against corner displacement between conditions. If the 10
disagreeing segments cluster on the pieces whose bbox moves most, the mechanism
is corner placement and the threshold is a secondary effect. If they do not, the
threshold is the whole story.

An inversion cannot come from the alignment transform:
`estimate_affine_transform` uses `cv2.estimateAffinePartial2D`, a 4-DOF
similarity with no reflection, so handedness is preserved. It has to come from
the segment boundaries moving.

### Attack the self-defeating threshold

[`_detect_shape_adaptive`](../../src/snap_fit/image/shape_detector.py#L129) sets

```python
flat_th = max(10.0, np.std(s1_xs) * 1.5)
```

so the threshold for detecting a knob is derived from the spread that the knob
itself creates. A stronger knob raises its own bar, and any small contour change
moves `std`, moves the threshold, and flips the verdict. Candidates, in
increasing order of departure from the current design:

- an absolute threshold in mm, now that 4.24 board units/mm is known (Q14), so
  the number means something physical instead of being relative to the feature,
- a threshold derived from the segment's **chord length** rather than from its
  deviation, which is independent of the knob,
- signed area between the segment and its chord instead of counting points past
  a threshold. This is what the classification actually means, it needs no count
  threshold at all, and its sign is the `IN`/`OUT` answer directly.

The last is the most likely to fix inversions, since a sign is more robust than
a count. Try it, but do not assume it: the fixture decides.

### Convert the gate to a penalty

Independent of the classifier, and worth doing even if the classifier improves:
convert `is_compatible` from a hard gate into a score penalty (D16), so a
misclassification degrades a pair instead of deleting it silently.

Constraint: `1e6` is overloaded across four unrelated meanings, and only the
first changes.

| site                                   | meaning                          | changes |
| -------------------------------------- | -------------------------------- | ------- |
| `segment_matcher.py:45`                | shape incompatible               | yes     |
| `piece_matcher.py:51`                  | segment missing from the manager | no      |
| `grid/suggestion.py:22` `_NO_SCORE`    | no placed neighbour / uncached   | no      |
| `interactive_service.py:541`           | user-rejected pair               | no      |

So the penalty must stay bounded well below `1e6`, or a penalised pair becomes
indistinguishable from the three sentinels that remain. It ships as a config
value with a provisional default; the real number is computed from phase 4's
measured separation and fixed in phase 7 (Q19).

Second consequence: the gate currently prunes. Removing it means every pair gets
scored, which at 48 segments is ~1100 pairs and irrelevant, but is a real cost
at puzzle scale. Note it in the code rather than letting it be discovered later.

## Acceptance criterion

Measured against the **hand-confirmed** shapes from the phase 2 annotation
(D13), not against agreement between conditions. Self-consistency is not enough:
a classifier that returns `WEIRD` everywhere would be perfectly consistent and
perfectly useless, and `WEIRD` passes `is_compatible` so it would look like an
improvement.

Work can start against the majority vote as a provisional target and be
re-scored when the annotation returns.

## Out of scope

- Score tuning. Phase 7.
- Per-condition preprocessing to salvage `x4`. Phase 5, D10.
- Rectification scale. Phase 6, though a higher scale may reduce the instability
  on its own, which phase 6 will see.

## Done when

- The 10-disagreement table exists as a fixture.
- The corner-placement hypothesis is confirmed or ruled out, with the
  correlation reported either way.
- Disagreement against hand-confirmed shapes is lower than the baseline, or the
  phase reports why it could not be and what the ceiling is.
- `is_compatible` is a bounded, configurable penalty, with the sentinel
  constraint respected and tests covering it.
- `uv run pytest && uv run ruff check . && uv run pyright && uv run pre-commit run --all-files`
  passes.
