# 13 - Side-by-Side Matching Preview

**Status:** done
**Parent:** [10_ui_notes.md](10_ui_notes.md)

## Goal

When the suggestion engine proposes a match, display a visual preview showing the existing placed piece and the proposed piece overlapping along the matched edge, with transparency, to let the user verify fit quality.

## Current State

- The suggestion panel shows the candidate piece image and a list of neighbor scores (`vs 0,1: 0.034`), but **no visual comparison** of how the two edges actually fit.
- `SegmentMatcher` in `src/snap_fit/image/segment_matcher.py` computes an affine transform aligning one segment onto another. The transform and similarity are computed but the aligned visualization is not exposed.
- `process.py` has `estimate_affine_transform()` and `transform_contour()` which can align segment points.
- `draw_contour()`, `draw_corners()` and other drawing functions exist in `image/utils.py`.
- Per the UI notes: "the ends of the two matching segments in the contour can be matched (some code in some random notebook does this)". Likely in `scratch_space/contour_/` or `scratch_space/piece_matcher/`.
- The match card macro (`match_card`) already shows two piece images side-by-side with a "vs" label, but with no alignment or overlay.

## Analysis

| Aspect | Detail |
|--------|--------|
| Segment alignment | `SegmentMatcher._transform_s1()` aligns segment1 onto segment2 using affine partial estimation. Returns transformed points array. |
| Coordinate space | Segment points are in piece-local coordinates. Both pieces have their own local coordinate systems. Need to work in a shared canvas. |
| Piece images | Available via the `/img` endpoint. Crop from processed sheet, optionally rotated. |
| Overlay approach | Option A: Generate a composite server-side (OpenCV alpha blending). Option B: Client-side CSS overlapping with `opacity`. Server-side is cleaner and more accurate. |
| What to show | The matched edge region - not necessarily the full piece. Crop to the area around the matching segments. |
| Neighbor context | Each suggestion has `neighbor_scores` with `{pos_key: score}`. Each pos_key maps to a placed piece. The scored segment pairs are recoverable via `get_scored_segment_pairs()`. |

## Plan

### Step 1 - Create match preview image endpoint

**File:** `src/snap_fit/webapp/services/piece_service.py` (or a new `match_preview_service.py`)

New method `get_match_preview_img(piece_id_1, edge_1, piece_id_2, edge_2, orientation_1, orientation_2, size)`:

1. Load both piece crop images from cache.
2. Apply the respective rotations (so edges are in their placed orientation).
3. Create a composite canvas:
   - Draw piece_1 (the placed piece) at full opacity on the left half.
   - Compute segment alignment transform from `SegmentMatcher`.
   - Draw piece_2 (the candidate) at ~50% opacity, positioned so the matching edges overlap.
4. Encode as PNG and return bytes.

Alternatively, a simpler version:
1. Draw piece_1 image on the left.
2. Draw piece_2 image on the right (rotated to its proposed orientation).
3. Draw the two segment contours overlaid in the center, color-coded (green for piece_1 edge, red for piece_2 edge).
4. Add a similarity score label.

### Step 2 - Add API endpoint

**File:** `src/snap_fit/webapp/routers/puzzle_solve.py` (or `piece_ingestion.py`)

```
GET /api/v1/puzzle/matches/preview?piece1=X&edge1=top&piece2=Y&edge2=bottom&orient1=0&orient2=90&size=300
```

Returns PNG of the match preview image.

### Step 3 - Integrate into suggestion panel

**File:** `webapp_resources/templates/solver.html`

For each neighbor score in the suggestion, add a match preview thumbnail:
```html
{% for pos, score in candidate.neighbor_scores.items() %}
  {% set neighbor = session.placement[pos] %}
  <div class="match-preview">
    <img src="/api/v1/puzzle/matches/preview?piece1={{ neighbor[0] }}&edge1={{ facing_edge_1 }}&piece2={{ candidate.piece_id }}&edge2={{ facing_edge_2 }}&orient1={{ neighbor[1] }}&orient2={{ candidate.orientation }}&size=200">
    <p>vs {{ pos }}: {{ score_badge(score) }}</p>
  </div>
{% endfor %}
```

The challenge is computing `facing_edge_1` and `facing_edge_2` in the template. These depend on the relative grid positions and orientations. Options:
- **Option A:** Pre-compute in the backend and include in `SuggestionCandidate.neighbor_scores` (extend the schema to include edge info).
- **Option B:** Compute in JavaScript client-side from grid position arithmetic.
- **Recommended:** Option A - extend `neighbor_scores` from `dict[str, float]` to `dict[str, NeighborScoreDetail]` with fields: `score`, `my_edge`, `their_edge`, `their_piece_id`.

### Step 4 - Extend SuggestionCandidate schema

**File:** `src/snap_fit/webapp/schemas/interactive.py`

```python
class NeighborScoreDetail(BaseModel):
    score: float
    my_edge: str       # Edge of the candidate facing this neighbor
    their_edge: str    # Edge of the placed neighbor facing the candidate
    their_piece_id: str  # Piece ID of the placed neighbor

class SuggestionCandidate(BaseModel):
    ...
    neighbor_details: dict[str, NeighborScoreDetail]  # pos_key -> detail
```

**File:** `src/snap_fit/grid/suggestion.py`

Extend `RawCandidate` and `score_candidates()` to capture edge pair info alongside scores.

## Complexity assessment

This is the **most complex** feature in the UI notes. It touches:
- A new image generation pipeline (server-side compositing).
- A new API endpoint.
- Schema extensions to carry edge pair metadata.
- Template changes for inline previews.

**Recommended approach:** Start with the simpler "side-by-side with segment overlay" (Step 1, simpler version) before attempting full alpha-blended overlap.

## Files to touch

| File | Change |
|------|--------|
| `src/snap_fit/webapp/services/piece_service.py` | New `get_match_preview_img()` method |
| `src/snap_fit/webapp/routers/puzzle_solve.py` | New preview endpoint |
| `src/snap_fit/webapp/schemas/interactive.py` | `NeighborScoreDetail` model, extend `SuggestionCandidate` |
| `src/snap_fit/grid/suggestion.py` | Extend `RawCandidate` and `score_candidates()` to capture edge pairs |
| `webapp_resources/templates/solver.html` | Add match preview images to suggestion panel |
| `webapp_resources/static/css/components.css` | `.match-preview` styles |

## Acceptance criteria

- Each neighbor score in the suggestion panel includes a visual preview.
- The preview shows both the placed piece's edge and the candidate's edge, aligned or side-by-side.
- The similarity score is visible on the preview.
- Labels identify both pieces (not just the candidate).
