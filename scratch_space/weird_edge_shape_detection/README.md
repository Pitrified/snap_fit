# Weird Edge Shape Detection Issue

## Overview

During development of the Naive Linear Solver, we discovered that **110 out of 192 segments (57%)** in the sample puzzle were classified as `WEIRD` shape, causing the `SegmentMatcher` to return `1e6` (incompatible) scores for most edge comparisons.

### Goal

Fix the shape classification algorithm so that most segments are correctly classified as `IN`, `OUT`, or `EDGE` instead of `WEIRD`.

### ⚠️ Critical Constraint: WEIRD is Safer Than Misclassification

**Misclassifying a segment is WORSE than classifying it as WEIRD.**

- **Wrong IN/OUT**: The matcher computes similarity assuming wrong polarity → bad matches propagate errors
- **WEIRD fallback**: Triggers more flexible matching methods that don't rely on shape assumption

Therefore, the classification algorithm should:
1. **Prefer WEIRD over uncertain IN/OUT** - when evidence is ambiguous, default to WEIRD
2. **Minimize false IN/OUT** - only classify as IN/OUT when confident
3. **Accept some WEIRD** - a small WEIRD rate is acceptable if it prevents misclassification

### Proposed Approaches

**Option A: Adaptive Thresholds**
- Calculate `flat_th` and `count_th` based on segment statistics (std dev, percentile)
- Pros: Self-adjusting to different puzzle scales and image resolutions
- Cons: May still fail on genuinely ambiguous shapes

**Option B: Net Displacement / Area-Based Classification**
- Use signed area or mean displacement from center line instead of counting points
- Pros: More robust to noise; single metric instead of two thresholds
- Cons: Needs tuning of area threshold

**Option C: Improved Corner Detection (Upstream Fix)**
- Fix corner detection so segments don't bisect tabs/slots
- Pros: Addresses root cause; cleaner segments
- Cons: More invasive change; may require reprocessing all data

## Plan

1. [x] Create feature branch and planning doc
2. [ ] Data exploration notebook: load v1 and v2 puzzle data, visualize segment point distributions
3. [ ] Quantify WEIRD vs IN/OUT/EDGE counts across both datasets
4. [ ] Visualize problematic segments to understand failure modes
5. [ ] **USER DECISION**: Select approach (A, B, or C)
6. [ ] Implement chosen solution in prototype notebook
7. [ ] Validate fix reduces WEIRD count significantly
8. [ ] Port fix to `src/snap_fit/image/segment.py`

---

## Problem Details

## Root Cause

The shape classification algorithm in `src/snap_fit/image/segment.py` uses simple threshold-based detection:

```python
def _compute_shape(self) -> None:
    # Transform segment to align with x-axis
    # ...
    
    # Count points far from center line
    flat_th = 20
    out_count = (s1_xs < -flat_th).sum()  # points to the left
    in_count = (s1_xs > flat_th).sum()    # points to the right
    
    count_th = 5
    is_out = bool(out_count > count_th)
    is_in = bool(in_count > count_th)
    
    # Classification
    match (is_out, is_in):
        case True, False:  -> OUT (tab protruding outward)
        case False, True:  -> IN  (slot going inward)
        case False, False: -> EDGE (flat boundary)
        case True, True:   -> WEIRD (ambiguous)
```

### Why WEIRD Happens

A segment is classified as `WEIRD` when it has **significant points on BOTH sides** of the center line (`count_th=5` points beyond `flat_th=20` pixels on each side).

This can occur due to:

1. **Noisy contour extraction** - Jagged edges from image processing
2. **Poor corner detection** - Segment boundaries cut through tabs/slots
3. **Threshold sensitivity** - Fixed thresholds don't adapt to puzzle scale
4. **Complex tab shapes** - Tabs with curves that cross the center line

## Impact

When `is_compatible()` returned `False` for WEIRD shapes:

| Metric          | Before Fix | After Fix |
|-----------------|------------|-----------|
| Total Score     | 64,000,397 | ~2,610    |
| Max Edge Score  | 1,000,000  | ~140      |
| Mean Edge Score | 780,493    | ~32       |
| Edges with 1e6  | 64         | 0         |

## Temporary Fix Applied

Modified `Segment.is_compatible()` to treat `WEIRD` shapes as potentially compatible:

```python
def is_compatible(self, other: Segment) -> bool:
    # EDGE segments are never compatible
    if self.shape == s.EDGE or other.shape == s.EDGE:
        return False
    
    # Standard IN/OUT compatibility
    if (self.shape == s.IN and other.shape == s.OUT) or \
       (self.shape == s.OUT and other.shape == s.IN):
        return True
    
    # WEIRD segments treated as potentially compatible
    if self.shape == s.WEIRD or other.shape == s.WEIRD:
        return True
    
    return False
```

This allows the contour similarity to be computed even when shape classification fails.

## Recommended Permanent Solutions

### Option 1: Adaptive Thresholds

Calculate thresholds based on segment/contour statistics:

```python
flat_th = np.std(s1_xs) * 1.5  # Adapt to segment's own variance
count_th = max(5, len(s1_xs) * 0.05)  # Percentage-based count
```

### Option 2: Net Displacement Metric

Instead of counting points, measure the net displacement from center:

```python
mean_x = np.mean(s1_xs)
if mean_x < -threshold:
    shape = OUT
elif mean_x > threshold:
    shape = IN
else:
    shape = EDGE
```

### Option 3: Area-Based Classification

Calculate the signed area under the curve:

```python
signed_area = np.trapz(s1_xs)
if signed_area < -area_threshold:
    shape = OUT
elif signed_area > area_threshold:
    shape = IN
else:
    shape = EDGE
```

### Option 4: Improved Corner Detection

Fix upstream corner detection to ensure segments are split at actual corner points, preventing tabs from being bisected.

## Shape as Soft Constraint

Consider using shape compatibility as a **score modifier** rather than a hard filter:

```python
def compute_similarity(self) -> float:
    base_score = self.match_shape()  # Contour similarity
    
    if not self.s1.is_compatible(self.s2):
        # Penalize incompatible shapes but don't reject
        return base_score * 1.5 + SHAPE_PENALTY
    
    return base_score
```

## Files Involved

- `src/snap_fit/image/segment.py` - Shape classification and compatibility
- `src/snap_fit/image/segment_matcher.py` - Uses `is_compatible()` as gate
- `src/snap_fit/image/contour.py` - Builds segments from contour corners

## Testing

To verify the fix:

```python
# Count shapes after loading pieces
from collections import Counter
shapes = [seg.shape for piece in pieces for seg in piece.segments.values()]
print(Counter(shapes))

# Expected: fewer WEIRD, more IN/OUT
# Actual before: weird=110, out=32, edge=25, in=25
```

## Related Issues

- Corner detection quality affects segment boundaries
- Image preprocessing (blur, threshold) affects contour smoothness
- Puzzle piece photography angle affects tab/slot visibility
