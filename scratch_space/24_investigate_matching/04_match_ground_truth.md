---
status: planned
---

# Phase 4 - Ground-truth edge pairs

## Overview

Turn the returned annotation into a truth file: which segments actually pair
with which, stated in physical terms, plus the confirmed shape per segment. It
is the yardstick every later phase measures against, so it must not be derived
from the thing it measures.

Context: [`00_start.md`](00_start.md). Depends on
[`02_capture_corpus.md`](02_capture_corpus.md) for the annotation and
[`03_shape_stability.md`](03_shape_stability.md) for a matcher that can score a
shape-mismatched pair instead of deleting it.

## Goals

1. A truth file keyed in capture-independent terms.
2. Structural assertions that check the hand pass rather than assume it.
3. A baseline separation between true and false pair scores.

## Plan

### Format

Keyed by `(sheet_index, label, edge_pos)` (D3), not by pixels and not by
`PieceId`. That is what makes it survive the phase 6 rescale, and what lets it
be evaluated against every capture condition rather than one. Sketch:

```yaml
shapes:
  s0:A1: { TOP: OUT, RIGHT: OUT, BOTTOM: IN, LEFT: OUT }
  ...
pairs:
  - [s0:A1 RIGHT, s2:B1 LEFT]
  ...
```

It lives in this scratch folder, scoped to this picture set (D7). Not in
`MatchResult.similarity_manual_`: that field is a per-pair float on a
capture-specific result, and overloading it would conflate "what the matcher
scored" with "what is actually true".

### Assertions on the hand pass

These check the annotation, so they run against it and report mismatches rather
than being asserted of it:

- the pair graph is a **disjoint** union, with no edge crossing between groups
  (D12, from Q11),
- each segment has **at most one** partner,
- exactly **2** segments are flat and therefore partnerless. This falls out of
  the census: majority vote leaves 2 flat segments in 48, and a rectangular
  `r x c` assembly would need `2(r+c)`, so even one 3x4 block would need 14.
  These pieces are interior fragments of a bigger puzzle.
- every paired segment is `IN` against `OUT` in the confirmed shapes. A pair
  that is not is either a hand-pass slip or a genuinely surprising piece, and
  either way it needs looking at.

Note what is *not* asserted: the number of groups or their sizes. Nobody knows
them (Q13) and no measurement recovers them, so the phase records what the hand
pass says rather than checking it against an expectation.

### Baseline

With the truth loaded, score every segment pair and report:

- the score distribution for true pairs against false pairs,
- their separation, which is the number phase 7 optimises and phase 3's penalty
  is derived from (Q19),
- how many true pairs are still lost to shape misclassification after phase 3,
  which measures whether phase 3 actually helped.

## Out of scope

- Improving the score. Phase 7.
- Comparing conditions. Phase 5, which uses this baseline as its primary metric.
- Any matcher change. The matcher is being measured here, not modified.

## Done when

- The truth file exists, loads, and covers all 48 segments.
- The structural assertions run, and any mismatch with the hand pass is
  reported and resolved rather than silently accepted.
- The true-vs-false separation is recorded as the baseline.
- `uv run pytest && uv run ruff check . && uv run pyright && uv run pre-commit run --all-files`
  passes.
