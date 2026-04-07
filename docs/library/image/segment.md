# `image/segment`

> Module: `src/snap_fit/image/segment.py`
> Related tests: `tests/`

## Purpose

A `Segment` represents one edge of a puzzle piece - the contour points between two adjacent corners. It extracts its points from the parent `Contour`, classifies its shape (IN/OUT/EDGE/WEIRD) using `ShapeDetector`, and provides compatibility checking for matching.

## Usage

### Minimal example

```python
# Segments are created by Contour.split_contour(), not directly
contour.build_segments(corners)
segment = contour.segments[EdgePos.TOP]

print(f"Points: {len(segment)}")
print(f"Shape: {segment.shape}")  # SegmentShape.IN, .OUT, .EDGE, or .WEIRD
print(f"Start: {segment.start_coord}, End: {segment.end_coord}")

# Check compatibility for matching
if segment.is_compatible(other_segment):
    print("These segments could interlock")
```

## API Reference

### `Segment`

Key attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `points` | `np.ndarray` | Contour points for this edge |
| `shape` | `SegmentShape` | Classified shape (IN/OUT/EDGE/WEIRD) |
| `start_coord` | `np.ndarray` | First point coordinates |
| `end_coord` | `np.ndarray` | Last point coordinates |
| `coords` | `np.ndarray` | Stacked [start, end] coordinates |
| `swap_coords` | `np.ndarray` | Reversed [end, start] for matching |
| `is_wrapped` | `bool` | Whether segment wraps around the contour |

Key method: `is_compatible(other: Segment) -> bool`

Compatibility rules:

- IN + OUT = compatible (standard tab/slot fit)
- WEIRD + IN/OUT = compatible (allows matching despite classification issues)
- WEIRD + WEIRD = compatible
- EDGE + anything = incompatible (flat edges do not interlock)
- IN + IN or OUT + OUT = incompatible (same polarity)

## Common Pitfalls

- **Shape detection happens at construction**: The `ShapeDetector` is called during `__init__`, so shape is immutable after creation.
- **Point order matters**: `swap_coords` reverses start/end for affine alignment in `SegmentMatcher`. The matching algorithm aligns one segment's start to the other's end.

## Related Modules

- [`image/contour`](contour.md) - parent contour that creates segments
- [`image/shape_detector`](shape_detector.md) - the shape classification algorithm
- [`image/segment_matcher`](segment_matcher.md) - compares two segments for similarity
- [`config`](../config/index.md) - `SegmentShape` enum
