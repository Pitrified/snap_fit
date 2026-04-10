# Step 08 - Add `centroid` Property to `Contour`

> **Status:** done
> **Target file:** `src/snap_fit/image/contour.py`
> **Depends on:** nothing

---

## Objective

Add a `centroid` property to the `Contour` class so that `Sheet.build_pieces()`
can map each detected piece to a slot grid position via `SlotGrid.slot_for_centroid()`.

## Current state

`Contour` currently has:
- `self.region` - bounding rectangle (x, y, w, h) from `cv2.boundingRect()`
- `self.area` - computed as `w * h` from region

No centroid is exposed. The centroid can be computed either from:
1. **Bounding rect center:** `(x + w/2, y + h/2)` - fast, approximate
2. **Image moments:** `cv2.moments(contour)` - uses actual contour shape, more accurate

Option 2 is preferred since pieces may be irregular and the bounding box center
can deviate significantly from the actual contour centroid.

## Code stub

```python
# In src/snap_fit/image/contour.py, add to Contour class:

@property
def centroid(self) -> tuple[int, int]:
    """Contour centroid (x, y) computed from image moments."""
    m = cv2.moments(self.cv_contour)
    if m["m00"] == 0:
        # Degenerate contour - fall back to bounding rect center
        x, y, w, h = self.region
        return (x + w // 2, y + h // 2)
    cx = int(m["m10"] / m["m00"])
    cy = int(m["m01"] / m["m00"])
    return (cx, cy)
```

### Performance note

`cv2.moments()` is O(n) where n is the number of contour points. For typical
puzzle pieces (hundreds to low thousands of points) this is negligible. The
property is not cached since contours are immutable after creation and the
computation is fast.

## File touchmap

| File | Change |
|------|--------|
| `src/snap_fit/image/contour.py` | Add `centroid` property to `Contour` class |

## Test strategy

- **Known contour:** Create a square contour, assert centroid is at center
- **Circle contour:** Create a circular contour, assert centroid is near center
- **Degenerate contour:** Zero-area contour falls back to bounding rect center
- **Test file:** `tests/image/test_contour.py` (add to existing or create)

## Acceptance criteria

- [ ] `Contour.centroid` returns `(int, int)` tuple
- [ ] Centroid is computed from image moments (not bounding rect center)
- [ ] Degenerate contour (zero area) does not raise, falls back gracefully
- [ ] Existing tests still pass (no behavioral changes to other methods)
