# `image/segment_matcher`

> Module: `src/snap_fit/image/segment_matcher.py`
> Related tests: `tests/`

## Purpose

Computes the geometric similarity between two edge segments by estimating an affine transformation that maps one segment onto the other, then measuring point-by-point distance. This is the core comparison engine for the puzzle matching pipeline.

## Usage

### Minimal example

```python
from snap_fit.image.segment_matcher import SegmentMatcher

matcher = SegmentMatcher(segment1, segment2)
similarity = matcher.compute_similarity()

if similarity < 50:
    print("Good match!")
elif similarity >= 1e6:
    print("Incompatible shapes")
```

## API Reference

### `SegmentMatcher`

Constructor: `SegmentMatcher(segment1, segment2)` - immediately computes the affine transform from `segment1.coords` to `segment2.swap_coords`.

- `compute_similarity() -> float` - returns similarity score (lower is better). Returns `1e6` if shapes are incompatible.
- `match_shape() -> float` - raw distance computation (called by `compute_similarity()` after compatibility check)

### Algorithm

1. Estimate an affine transform aligning `s1.coords` (start/end) to `s2.swap_coords` (end/start reversed)
2. Transform all points of `s1` using this matrix
3. For each transformed point in `s1`, find the corresponding point in `s2` (using length ratio)
4. Sum distances between paired points, normalize by the longer segment length

## Common Pitfalls

- **Asymmetric comparison**: `SegmentMatcher(a, b)` transforms `a` onto `b`. The result is not necessarily identical to `SegmentMatcher(b, a)` due to the resampling direction, though it should be close.
- **Score interpretation**: There is no fixed threshold for "good match". Typical good matches score below 20-50; poor matches score in the hundreds. The `1e6` sentinel means the shapes are fundamentally incompatible.

## Related Modules

- [`image/segment`](segment.md) - the `Segment` objects being compared
- [`image/process`](process.md) - provides `estimate_affine_transform()` and `transform_contour()`
- [`puzzle/piece_matcher`](../puzzle/piece_matcher.md) - orchestrates matching across all piece pairs
