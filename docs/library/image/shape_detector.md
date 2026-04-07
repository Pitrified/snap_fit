# `image/shape_detector`

> Module: `src/snap_fit/image/shape_detector.py`
> Related tests: `tests/`

## Purpose

Classifies a segment's shape as IN (inward tab), OUT (outward tab), EDGE (flat boundary), or WEIRD (ambiguous). Supports two strategies: a fixed-threshold naive approach and an adaptive approach that scales thresholds based on segment statistics.

## Usage

### Minimal example

```python
from snap_fit.image.shape_detector import ShapeDetector, ShapeDetectorStrategy

detector = ShapeDetector(ShapeDetectorStrategy.ADAPTIVE)
shape = detector.detect_shape(source_coords, points)
# Returns SegmentShape.IN, .OUT, .EDGE, or .WEIRD
```

## API Reference

### `ShapeDetector`

Constructor: `ShapeDetector(strategy=ShapeDetectorStrategy.NAIVE)`

Method: `detect_shape(source_coords, points) -> SegmentShape`

### Strategies

**NAIVE**: Fixed thresholds (`flat_th=20`, `count_th=5`). Aligns points horizontally, counts how many points deviate left (OUT) or right (IN) of the center line.

**ADAPTIVE** (default in production): Computes `flat_th` from `1.5 * std(x-coords)` and `count_th` as `5%` of segment length. Reduces false WEIRD classifications while preserving safety for truly ambiguous segments.

### Algorithm

1. Align segment points horizontally using an affine transform (start to `[0,0]`, end to `[0,500]`)
2. Extract x-coordinates of all transformed points
3. Count points beyond negative threshold (OUT) and positive threshold (IN)
4. Classify based on which threshold is exceeded

## Common Pitfalls

- **WEIRD is conservative**: The adaptive strategy prefers WEIRD when both IN and OUT thresholds are exceeded. This is intentional - WEIRD segments are still allowed to match (see `Segment.is_compatible()`).

## Related Modules

- [`image/segment`](segment.md) - calls `ShapeDetector` during construction
- [`config`](../config/index.md) - `SegmentShape` enum for classification results
