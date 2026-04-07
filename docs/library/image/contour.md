# `image/contour`

> Module: `src/snap_fit/image/contour.py`
> Related tests: `tests/`

## Purpose

Wraps an OpenCV contour (numpy array of boundary points) with geometric operations: bounding rectangle computation, translation, corner matching, and splitting into four edge segments.

## Usage

### Minimal example

```python
from snap_fit.image.contour import Contour
from snap_fit.config.types import CornerPos

contour = Contour(cv_contour)  # cv_contour from cv2.findContours
print(f"Area: {contour.area}, Region: {contour.region}")

# Match corners and split into segments
corners = {
    CornerPos.TOP_LEFT: (10, 10),
    CornerPos.TOP_RIGHT: (100, 10),
    CornerPos.BOTTOM_RIGHT: (100, 100),
    CornerPos.BOTTOM_LEFT: (10, 100),
}
contour.build_segments(corners)

for edge_pos, segment in contour.segments.items():
    print(f"{edge_pos.value}: {len(segment)} points, shape={segment.shape}")
```

## API Reference

### `Contour`

Key attributes:

- `cv_contour: np.ndarray` - raw OpenCV contour points
- `region: Rect` - bounding rectangle `(x, y, w, h)`
- `area: int` - area of the bounding rectangle
- `segments: dict[EdgePos, Segment]` - populated after `build_segments()`
- `corner_idxs: dict[CornerPos, int]` - contour point indices closest to each corner
- `corner_coords: dict[CornerPos, np.ndarray]` - actual coordinates at corner indices

Key methods:

- `translate(x_offset, y_offset)` - returns a new translated `Contour`
- `build_segments(corners)` - matches corners to contour and splits into four segments
- `derive(step=5)` - computes contour derivative (orientation/curvature)

## Common Pitfalls

- **Corner matching is nearest-point**: `match_corners()` finds the contour point closest to each given corner using L1 distance. If the contour has sparse points near a corner, the match may be off.
- **Segment wrapping**: When a segment's start index > end index, the segment wraps around the contour array boundary. The `Segment` class handles this automatically.

## Related Modules

- [`image/segment`](segment.md) - the `Segment` objects produced by splitting
- [`puzzle/piece`](../puzzle/piece.md) - provides corner coordinates and triggers `build_segments()`
- [`image/process`](process.md) - `find_contours()` produces the raw cv2 contours
