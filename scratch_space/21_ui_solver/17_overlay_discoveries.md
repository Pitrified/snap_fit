# 17 - Overlay Discoveries and Patterns

**Purpose:** Record what was learned while implementing feature 15 (piece inspection overlay) to
inform the design of feature 13 (side-by-side matching preview).

---

## Coordinate spaces recap

The contour cache (`.npz`) stores contour points **already translated to piece-local space**.
`Piece.from_contour()` calls `contour.translate(-region_pad[0], -region_pad[1])` when it creates
the piece, so the stored contour coordinates align directly with:
- the crop image returned by `/api/v1/pieces/{id}/img`
- `PieceRecord.sheet_origin` + `padded_size` (the crop rect on the processed sheet image)

`SheetManager.load_contour_for_piece(piece_id, contour_dir)` conveniently provides both
`contour_pts` (shape `(N, 1, 2)`, dtype int32) and `corner_indices` (`{CornerPos.value: int}`).

---

## Segment extraction from the cached contour

Given `corner_indices`, extract a segment's points using:

```python
start_idx = corner_indices[start_corner.value]   # e.g. "top_right"
end_idx   = corner_indices[end_corner.value]       # e.g. "top_left"

# Wrap-around segments (start_idx > end_idx) span end-of-array -> start-of-array:
if start_idx <= end_idx:
    seg_pts = contour_pts[start_idx : end_idx + 1]
else:
    seg_pts = np.vstack((contour_pts[start_idx:], contour_pts[: end_idx + 1]))
```

`EDGE_ENDS_TO_CORNER` in `snap_fit.config.types` maps each `EdgePos` to its
`(start_CornerPos, end_CornerPos)` pair:

| Edge   | Start corner | End corner   |
|--------|-------------|--------------|
| LEFT   | TOP_LEFT    | BOTTOM_LEFT  |
| BOTTOM | BOTTOM_LEFT | BOTTOM_RIGHT |
| RIGHT  | BOTTOM_RIGHT| TOP_RIGHT    |
| TOP    | TOP_RIGHT   | TOP_LEFT     |

---

## Drawing approach (server-side PNG)

Feature 15 used **server-side rendering** via OpenCV: the overlay is baked into the image
bytes returned from a dedicated endpoint (`/img/inspect`).

Pros:
- No client JS required.
- Reuses existing `draw_*` helpers in `image/utils.py`.
- A toggle button simply swaps the `<img src>`.

Cons:
- Round-trip to the server on every toggle.
- Cannot animate or interact with overlay elements (e.g. hover a segment to highlight it).

For feature 13 the same server-side approach is likely sufficient for a first version;
client-side Canvas would only be needed for interactive/animated matching exploration.

---

## Affine alignment for matching preview (feature 13)

`SegmentMatcher(seg1, seg2)` in `src/snap_fit/image/segment_matcher.py` already computes an
affine transform that maps `seg2` onto `seg1`.  The transform is `(scale, angle, tx, ty)`.

To produce the side-by-side overlay for feature 13:

1. Load the crop image of the **placed** piece (piece A) and the **candidate** piece (piece B).
2. Load both contours from cache and extract the matching segment points for each.
3. Compute or retrieve the affine transform (already cached in `PieceMatcher._lookup` as
   `MatchResult` - but the raw transform matrix is **not** stored).
   - Option A: Re-run `SegmentMatcher(seg_a, seg_b).estimate_transform()` on demand.
   - Option B: Store the transform matrix in `MatchResult` (schema change needed).
   - Option A is simpler for an initial version.
4. Apply the transform to piece B's crop image using `cv2.warpAffine`.
5. Composite both images with transparency using `cv2.addWeighted`.

### Segment reconstruction for SegmentMatcher

`SegmentMatcher` takes `Segment` objects, which require a live `Contour` object.
To reconstruct a `Segment` from cache data without loading the full `Sheet`:

```python
from snap_fit.image.contour import Contour
from snap_fit.image.segment import Segment
from snap_fit.config.types import EDGE_ENDS_TO_CORNER, EdgePos

contour = Contour(contour_pts)          # Build lightweight Contour from cached pts
# Inject corner_idxs directly (match_corners is not needed when we already have indices):
contour.corner_idxs = {CornerPos(k): v for k, v in corner_indices.items()}
contour.corner_coords = {
    CornerPos(k): contour_pts[v][0] for k, v in corner_indices.items()
}
edge_pos = EdgePos.TOP
start_corner, end_corner = EDGE_ENDS_TO_CORNER[edge_pos]
segment = Segment(contour, contour.corner_idxs[start_corner], contour.corner_idxs[end_corner])
```

This avoids re-running the full `Piece` creation pipeline (ArUco, contour detection, etc.).

---

## Color conventions established in feature 15

| Edge   | BGR color         | CSS color  |
|--------|-------------------|------------|
| TOP    | (0, 0, 255) red   | #ef4444    |
| RIGHT  | (0, 255, 0) green | #22c55e    |
| BOTTOM | (255, 0, 0) blue  | #3b82f6    |
| LEFT   | (255, 255, 0) cyan| #06b6d4    |
| Corner | (255, 255, 255)   | white      |

These are in `_SEGMENT_COLORS` in `src/snap_fit/webapp/services/piece_service.py`.
Reuse or import them for feature 13.

---

## Files relevant to feature 13

| File | Purpose |
|------|---------|
| `src/snap_fit/image/segment_matcher.py` | `SegmentMatcher` - affine transform estimation |
| `src/snap_fit/puzzle/piece_matcher.py` | `PieceMatcher` - match cache and `_lookup` |
| `src/snap_fit/webapp/services/piece_service.py` | `get_piece_inspection_img`, `_draw_inspection_overlay`, `_find_tag_dir_for_piece` |
| `src/snap_fit/puzzle/sheet_manager.py` | `load_contour_for_piece` |
| `src/snap_fit/image/contour.py` | `Contour` class, `corner_idxs`, `split_contour` |
| `src/snap_fit/image/segment.py` | `Segment` class, `points` (N,1,2 array) |
| `src/snap_fit/config/types.py` | `EDGE_ENDS_TO_CORNER`, `CornerPos`, `EdgePos` |
| `webapp_resources/templates/piece_detail.html` | Existing toggle button pattern to extend |

---

## Open questions for feature 13

- Should the matching preview be a new page/endpoint or a modal overlay on the piece detail page?
- The affine transform in `SegmentMatcher` is a 2D rigid body (scale + rotation + translation).
  Does the current implementation also handle reflection (mirroring) for pieces on the reverse side?
- Should the composite image show piece B warped onto piece A's coordinate frame, or place both
  images side-by-side with the matching segments aligned at a shared edge?
