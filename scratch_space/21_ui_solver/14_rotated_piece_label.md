# 14 - Rotated Label on the Piece Image

**Status:** not started
**Parent:** [10_ui_notes.md](10_ui_notes.md)

## Goal

Burn the piece ID label directly into the piece image, rotated to match the piece's placement orientation, so the label stays readable regardless of how the piece is displayed.

## Current State

- Grid cells show a `<span class="grid-cell__label">` positioned via CSS at the bottom-left corner of the cell. This label does **not** rotate with the image.
- When a piece is placed at 90 or 270 degrees, the CSS-overlaid label stays horizontal while the piece image is rotated, which can be disorienting.
- The piece image endpoint (`/api/v1/pieces/{id}/img`) already supports `orientation` and `size` parameters. When `orientation` is set, it uses `cv2.rotate()` server-side.
- There is no option to draw text onto the returned image.

## Analysis

| Aspect | Detail |
|--------|--------|
| Label source | `PieceRecord.label` (e.g. `A3`) if available, else `piece_id` fallback (e.g. `oca_01:3`). |
| When to burn | Only useful when the image will be rotated and displayed on the grid. The un-rotated base image (e.g. on piece detail page) should remain unlabeled. |
| Font rendering | OpenCV `cv2.putText()` with `FONT_HERSHEY_SIMPLEX`. Place at a consistent location (e.g. top-left 10% of the image). |
| Label rotation | If the piece is rotated 90 degrees in the grid, the label is burned onto the **un-rotated** image and then the whole image (including label) is rotated by 90 degrees. The label naturally rotates with the piece. |
| Alternative approach | Burn the label **after** rotation, always at the same screen position (e.g. top-left). This keeps the label always upright. Less intuitive but more readable. |
| Recommended | Burn the label before rotation. When the user sees the grid, each piece has its label oriented the same way the piece photograph was taken, making it easy to identify which piece is which even when rotated. |

## Plan

### Step 1 - Add `label` parameter to piece image endpoint

**File:** `src/snap_fit/webapp/services/piece_service.py`

Extend `get_piece_img()`:
```python
def get_piece_img(
    self,
    piece_id: str,
    size: int | None = None,
    orientation: int = 0,
    label: str | None = None,   # NEW
) -> bytes | None:
```

When `label` is provided:
1. After cropping (before rotation and resize), draw the label onto the image using `cv2.putText()`.
2. Position: top-left corner with a small margin (e.g. `(8, 20)`).
3. Use a dark semi-transparent rectangle behind the text for readability.
4. Font: `cv2.FONT_HERSHEY_SIMPLEX`, scale proportional to image size.
5. Then apply rotation and resize as usual. The label rotates with the piece.

### Step 2 - Add `label` query parameter to API endpoint

**File:** `src/snap_fit/webapp/routers/piece_ingestion.py`

```python
@router.get("/{piece_id}/img")
async def get_piece_img(
    piece_id: str,
    size: int | None = None,
    orientation: int = 0,
    label: str | None = None,   # NEW
):
```

Pass `label` through to `piece_service.get_piece_img()`.

### Step 3 - Use labeled images in grid cells

**File:** `webapp_resources/templates/macros/piece_macros.html`

Update `grid_cell` macro for filled cells:
```html
<img src="/api/v1/pieces/{{ piece_id }}/img?size=80&orientation={{ orientation }}&label={{ piece_label | urlencode }}"
     loading="lazy">
```

This replaces both the CSS-rotated image and the CSS label overlay. The label is now part of the image itself.

Remove or keep the `<span class="grid-cell__label">` as a hover/accessibility fallback.

### Step 4 - Pass label data to the macro

**File:** `webapp_resources/templates/solver.html`

Requires the label for each placed piece. This intersects with [11_placed_piece_labels.md](11_placed_piece_labels.md) - reuse the `piece_labels` dict built there.

Update the macro call:
```html
{{ grid_cell(pos_key, placement=placement, is_target=..., labels=piece_labels) }}
```

## Dependencies

- Depends on [11_placed_piece_labels.md](11_placed_piece_labels.md) for the label data pipeline.
- After this feature, the grid cell rendering switches from CSS rotation to backend-rotated images with burned-in labels.

## Files to touch

| File | Change |
|------|--------|
| `src/snap_fit/webapp/services/piece_service.py` | Add `label` param, burn text onto image before rotation |
| `src/snap_fit/webapp/routers/piece_ingestion.py` | Add `label` query param |
| `webapp_resources/templates/macros/piece_macros.html` | Use backend-rotated labeled image in `grid_cell` |
| `webapp_resources/templates/solver.html` | Pass labels dict; remove CSS transform on grid images |

## Acceptance criteria

- Grid cells show piece images with the label burned in, rotated together with the piece.
- Labels are readable at 80x80px grid cell images.
- Un-labeled images (piece detail, unplaced list) remain unaffected unless `label` param is set.
- The label text is the human-readable label (e.g. `A3`), not the raw piece_id.
