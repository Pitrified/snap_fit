# 03 - Piece Image Endpoint

> **Status:** not started
> **Depends on:** -
> **Main plan ref:** Phase 1, Preliminary changes #3

---

## Objective

Add `GET /api/v1/pieces/{piece_id}/img` that returns a PNG image of a single
puzzle piece cropped from its sheet photo. This unblocks all visual UI work -
piece cards, match cards, grid canvas, debug pages all need piece thumbnails.

---

## Current state

- `PieceRecord` has `contour_region: tuple[int, int, int, int]` (x, y, w, h) and
  `sheet_origin: tuple[int, int]` - both persisted in SQLite.
- `SheetRecord` has `img_path: str` (relative to `data_root`).
- `PieceService.get_piece(piece_id)` returns `PieceRecord` from SQLite.
- No image serving endpoint exists.
- `Piece.from_contour()` crops `img_orig` from the full sheet image with 30px padding
  using `pad_rect()` and `cut_rect_from_image()`.

---

## Plan

### Step 1: Service method

In `src/snap_fit/webapp/services/piece_service.py`, add:

```python
def get_piece_img(
    self,
    piece_id: str,
    size: int | None = None,
    orientation: int = 0,
) -> bytes | None:
    """Load sheet image, crop piece region, encode as PNG.

    Args:
        piece_id: Piece identifier (e.g. "sheet_01-0").
        size: Optional max dimension for resizing (preserves aspect ratio).
        orientation: Rotation in degrees (0, 90, 180, 270).

    Returns:
        PNG bytes or None if piece not found.
    """
```

Implementation:
1. `record = self.get_piece(piece_id)` - get PieceRecord from SQLite
2. Find the `SheetRecord` for `record.piece_id.sheet_id` to get `img_path`
3. Resolve full path: `data_root / img_path` (where `data_root` comes from
   settings or is stored alongside the sheet record)
4. `img = cv2.imread(str(full_path))` - load the full sheet image
5. Crop using `contour_region`: `x, y, w, h = record.contour_region`
   - The `contour_region` is already in **sheet-local** coordinates, matching
     the padded crop done by `Piece.from_contour()`. The region is the same as
     `sheet_origin + (w, h)` effectively.
6. `crop = img[y:y+h, x:x+w]`
7. Optional rotation: `cv2.rotate(crop, cv2.ROTATE_90_CLOCKWISE)` etc.
8. Optional resize: `cv2.resize(crop, ...)` if `size` is specified
9. `_, buf = cv2.imencode('.png', crop)` - encode as PNG
10. Return `buf.tobytes()`

### Step 2: Router endpoint

In `src/snap_fit/webapp/routers/piece_ingestion.py`, add:

```python
from fastapi.responses import Response

@router.get("/{piece_id}/img", summary="Get piece image")
async def get_piece_img(
    piece_id: str,
    size: int | None = None,
    orientation: int = 0,
    service: Annotated[PieceService, Depends(get_piece_service)],
) -> Response:
    img_bytes = service.get_piece_img(piece_id, size=size, orientation=orientation)
    if img_bytes is None:
        raise HTTPException(status_code=404, detail=f"Piece {piece_id} not found")
    return Response(content=img_bytes, media_type="image/png")
```

**Route ordering note:** This route MUST be registered before `GET /{piece_id}`
in the router, otherwise FastAPI matches `"img"` as a `piece_id`. Alternatively,
use a different path like `/img/{piece_id}` or `/pieces/{piece_id}/image`.

### Step 3: Resolve sheet image path

The tricky part is finding the full path to the sheet image. `SheetRecord.img_path`
is stored relative to `data_root`. The service needs to know `data_root`:

Option A: pass `settings.data_path` to `PieceService`
Option B: store absolute path in `SheetRecord` at ingest time
Option C: store `data_root` used at ingest time in `dataset.db`

**Recommendation:** Option A - pass `data_path` alongside `cache_path` to
`PieceService.__init__()`. The Settings object already has both paths.

### Step 4: Caching

Sheet images are large (4-8 MB JPEG). Loading and decoding on every request is
slow. Options:
- **LRU cache** on the service method for the loaded sheet image (keyed by sheet_id)
- **Pre-crop** all pieces at ingest time and save as individual PNGs in cache
- **Lazy pre-crop**: first request generates the crop PNG and saves to
  `cache/{tag}/thumbnails/{piece_id}.png`; subsequent requests serve the file

**Recommendation:** Start with no caching (simplest). If latency is a problem,
add LRU on the sheet image load (since one sheet contains many pieces, sequential
piece requests for the same sheet hit the cache).

```python
from functools import lru_cache

@lru_cache(maxsize=8)
def _load_sheet_image(self, img_path: str) -> np.ndarray:
    return cv2.imread(img_path)
```

### Step 5: Validation of orientation param

Only accept 0, 90, 180, 270:

```python
if orientation not in (0, 90, 180, 270):
    raise HTTPException(status_code=400, detail="orientation must be 0, 90, 180, or 270")
```

Map to OpenCV rotation constants:
```python
_ROTATE_MAP = {
    90: cv2.ROTATE_90_CLOCKWISE,
    180: cv2.ROTATE_180,
    270: cv2.ROTATE_90_COUNTERCLOCKWISE,
}
```

---

## File touchmap

| File | Change |
|------|--------|
| `src/snap_fit/webapp/services/piece_service.py` | Add `get_piece_img()` method, add `data_path` param |
| `src/snap_fit/webapp/routers/piece_ingestion.py` | Add `GET /{piece_id}/img` endpoint |
| `src/snap_fit/webapp/routers/ui.py` | Update `get_piece_service()` to pass `data_path` |
| `src/snap_fit/webapp/core/settings.py` | Possibly add `data_path` property if missing |

---

## Test strategy

- Unit test: `get_piece_img()` with a known ingest - verify returns non-empty bytes
- Unit test: verify PNG header bytes (`\x89PNG`)
- Unit test: orientation parameter applies correct rotation (check dimensions swap for 90/270)
- Integration test: `GET /api/v1/pieces/{piece_id}/img` returns 200 with `image/png` content type
- Integration test: `GET /api/v1/pieces/nonexistent/img` returns 404
- Manual: open URL in browser, see cropped piece image
