# 15 - Piece Inspection Overlay

**Status:** done
**Parent:** [10_ui_notes.md](10_ui_notes.md)

## Goal

On the piece detail page, overlay the detected contour segments and corner points on top of the piece image so users can visually verify detection quality.

## Current State

- The piece detail page (`webapp_resources/templates/piece_detail.html`) shows:
  - A plain 250px piece image (no overlays).
  - A metadata grid (type, contour points, region, origin, flat edges).
  - A corners table listing 4 corner coordinates.
  - A segments table listing 4 edges with shape badges.
- All the raw data needed for the overlay is already in `PieceRecord`:
  - `corners: dict[str, tuple[int, int]]` - 4 corner positions in piece-local coordinates.
  - `segment_shapes: dict[str, str]` - shapes per edge.
  - `contour_point_count: int` - number of contour points.
  - `contour_region: tuple[int, int, int, int]` - bounding rect.
- The piece image endpoint (`/api/v1/pieces/{id}/img`) returns a cropped image. Contour and corner coordinates are in the **same piece-local coordinate space** as this crop.
- Drawing functions exist in `src/snap_fit/image/utils.py`: `draw_contour()`, `draw_corners()`, etc.
- Contour data (actual point arrays) is persisted in `.npz` files in `cache/{tag}/contours/`.

## Analysis

| Aspect | Detail |
|--------|--------|
| Contour point data | Not in `PieceRecord` (which stores only metadata). Must be loaded from `.npz` cache or reconstructed by loading the Sheet and extracting the piece's `Contour` object. |
| Corner coordinates | Available in `PieceRecord.corners` as `{corner_name: (x, y)}`. These are in piece-local space (relative to `sheet_origin`). |
| Segment boundaries | To draw segments in different colors, need the corner indices that split the contour. These are in the `.json` files alongside the `.npz` contour cache: `{corner_pos: contour_index}`. |
| Overlay approach | **Option A:** Server-side - new API endpoint that returns the image with contour/corners drawn on it. **Option B:** Client-side - return contour point data as JSON and use HTML Canvas or SVG to overlay. |
| Recommended | **Option A** (server-side) is simpler and leverages existing `draw_*` functions. Add a `?overlay=contour` or similar param to the image endpoint. |

## Plan

### Step 1 - Add overlay image generation to PieceService

**File:** `src/snap_fit/webapp/services/piece_service.py`

New method `get_piece_inspection_img(piece_id, size)`:

1. Load the piece crop image (reuse `get_piece_img()` logic, but keep the raw numpy array before encoding).
2. Load contour data from `.npz` cache for this piece.
3. Load corner indices from `.json` cache.
4. Draw each segment in a different color on the image:
   - TOP = red `(0, 0, 255)`
   - RIGHT = green `(0, 255, 0)`
   - BOTTOM = blue `(255, 0, 0)`
   - LEFT = cyan `(255, 255, 0)`
5. Draw corner points as filled circles with labels (TL, TR, BL, BR).
6. Optionally draw shape labels (`IN`, `OUT`, `EDGE`) at the midpoint of each segment.
7. Resize if `size` is specified.
8. Encode as PNG and return bytes.

Loading contour data requires:
- Finding the `.npz` file: `cache/{tag}/contours/{sheet_filename}_contours.npz`.
- Extracting the piece's contour array by piece index.
- Finding the `.json` file for corner indices.
- Translating contour points from sheet-space to piece-local space using `sheet_origin`.

This is essentially what `SheetManager.load_contour_for_piece()` does, but we need to access it from the service level.

### Step 2 - Add API endpoint

**File:** `src/snap_fit/webapp/routers/piece_ingestion.py`

```python
@router.get("/{piece_id}/img/inspect")
async def get_piece_inspection_img(
    piece_id: str,
    size: int | None = Query(None),
):
    ...
```

Returns PNG with contour/corner overlay.

### Step 3 - Add overlay toggle to piece detail template

**File:** `webapp_resources/templates/piece_detail.html`

Add a toggle button above the piece image:

```html
<div class="piece-image-container">
  <img id="piece-img"
       src="/api/v1/pieces/{{ piece.piece_id }}/img?size=400"
       alt="Piece {{ piece.piece_id }}">
  <button id="toggle-overlay" class="btn btn--outline" onclick="toggleOverlay()">
    Show Contour Overlay
  </button>
</div>

<script>
function toggleOverlay() {
  const img = document.getElementById('piece-img');
  const btn = document.getElementById('toggle-overlay');
  const baseUrl = '/api/v1/pieces/{{ piece.piece_id }}/img?size=400';
  const inspectUrl = '/api/v1/pieces/{{ piece.piece_id }}/img/inspect?size=400';
  if (img.src.includes('/inspect')) {
    img.src = baseUrl;
    btn.textContent = 'Show Contour Overlay';
  } else {
    img.src = inspectUrl;
    btn.textContent = 'Hide Contour Overlay';
  }
}
</script>
```

### Step 4 - Add legend for segment colors

**File:** `webapp_resources/templates/piece_detail.html`

Add a small color legend below the image showing which color maps to which edge:
```html
<div class="segment-legend">
  <span style="color:red;">-- TOP</span>
  <span style="color:green;">-- RIGHT</span>
  <span style="color:blue;">-- BOTTOM</span>
  <span style="color:cyan;">-- LEFT</span>
  <span>O Corner points</span>
</div>
```

## Data loading path

```
PieceRecord (from DB)
  -> piece_id.sheet_id -> find tag from DB path
  -> cache/{tag}/contours/{sheet_filename}_contours.npz -> load numpy array
  -> cache/{tag}/contours/{sheet_filename}_corners.json -> load corner indices
  -> Select contour by piece index
  -> Translate from sheet-space to piece-local using sheet_origin
  -> Split contour into 4 segments using corner indices
  -> Draw segments + corners onto piece crop image
```

## Files to touch

| File | Change |
|------|--------|
| `src/snap_fit/webapp/services/piece_service.py` | New `get_piece_inspection_img()` method |
| `src/snap_fit/webapp/routers/piece_ingestion.py` | New `/img/inspect` endpoint |
| `webapp_resources/templates/piece_detail.html` | Add overlay toggle button, larger image, legend |
| `webapp_resources/static/css/components.css` | `.piece-image-container`, `.segment-legend` styles |

## Acceptance criteria

- Piece detail page has a "Show Contour Overlay" toggle button.
- Clicking it swaps the image to one with colored segment overlays and corner circles.
- Each edge is drawn in a distinct color matching the legend.
- Corner positions are labeled (TL, TR, BL, BR).
- Shape labels (IN/OUT/EDGE/WEIRD) are visible on each segment.
- Image size is increased from 250px to 400px for better visibility of the overlay.
