# 09 - Orientation Debug Page

> **Status:** not started
> **Depends on:** 03 (piece image endpoint)
> **Main plan ref:** Phase 6, Open question #2

---

## Objective

Build a debug page that shows every piece rendered in all 4 orientations
(DEG_0, DEG_90, DEG_180, DEG_270). This page exists to visually verify that:

1. The `Orientation` enum values map correctly to visual rotation
2. CSS `transform: rotate(Ndeg)` matches the backend's rotation convention
3. The `?orientation=` query param on the image endpoint produces correct results
4. Edge labels (TOP/RIGHT/BOTTOM/LEFT) are consistent after rotation

This is the single biggest visual-bug risk in the solver UI. OpenCV rotation
direction, numpy array indexing, and CSS rotation conventions differ subtly.
Getting this wrong means the solver places pieces in wrong orientations.

---

## Background: rotation conventions

| System | Rotation direction | Origin |
|--------|-------------------|--------|
| CSS `transform: rotate()` | Clockwise | top-left of element |
| OpenCV `cv2.rotate()` | ROTATE_90_CLOCKWISE = CW | top-left of image |
| numpy array indexing | row 0 = top, col 0 = left | top-left |
| `Orientation` enum | DEG_0=0, DEG_90=90, DEG_180=180, DEG_270=270 | undefined |

The critical question: when `Orientation.DEG_90` is applied to a piece, does
that mean "the piece's original TOP edge is now pointing RIGHT" (CW rotation)?

`get_original_edge_pos(rotated_edge, orientation)` in `orientation_utils.py`
answers this - it maps a rotated edge position back to the original. The debug
page should make the answer visually obvious.

---

## Plan

### Step 1: Debug page route

In `src/snap_fit/webapp/routers/debug.py` (or `ui.py`), add:

```python
@router.get("/debug/orientations", response_class=HTMLResponse)
async def orientation_debug(
    request: Request,
    dataset_tag: str | None = None,
    piece_id: str | None = None,
    service: ...,
) -> HTMLResponse:
    """Show pieces in all 4 orientations for visual verification."""
    if piece_id:
        pieces = [service.get_piece(piece_id)]
    else:
        pieces = service.list_pieces()[:12]  # limit to first 12 for page size
    return templates.TemplateResponse(
        request,
        "debug_orientations.html",
        {"title": "Orientation Debug", "pieces": pieces},
    )
```

### Step 2: Template

`webapp_resources/templates/debug_orientations.html`:

```jinja2
{% extends "base.html" %}
{% block content %}
<h1>Orientation Debug</h1>
<p>Each piece shown in 4 orientations. Red dot = original TOP edge. Blue dot = original RIGHT edge.</p>

<table class="debug-table">
  <thead>
    <tr>
      <th>Piece</th>
      <th>DEG_0 (original)</th>
      <th>DEG_90</th>
      <th>DEG_180</th>
      <th>DEG_270</th>
    </tr>
  </thead>
  <tbody>
    {% for piece in pieces %}
    <tr>
      <td>
        {{ piece.piece_id }}<br>
        {{ piece.label or '-' }}<br>
        {{ piece.oriented_piece_type.piece_type.name if piece.oriented_piece_type else '?' }}
      </td>
      {% for deg in [0, 90, 180, 270] %}
      <td class="debug-cell">
        <div class="orientation-box">
          {# Method A: backend rotation via ?orientation= param #}
          <div class="orientation-method">
            <span class="method-label">Backend rotate</span>
            <img src="/api/v1/pieces/{{ piece.piece_id }}/img?size=120&orientation={{ deg }}"
                 width="120" height="120">
          </div>
          {# Method B: CSS rotation on original image #}
          <div class="orientation-method">
            <span class="method-label">CSS rotate</span>
            <div style="width:120px; height:120px; overflow:hidden;">
              <img src="/api/v1/pieces/{{ piece.piece_id }}/img?size=120"
                   style="transform: rotate({{ deg }}deg); transform-origin: center;"
                   width="120" height="120">
            </div>
          </div>
          {# Edge labels after rotation #}
          <div class="edge-labels">
            <span class="edge-label edge-label--top">T</span>
            <span class="edge-label edge-label--right">R</span>
            <span class="edge-label edge-label--bottom">B</span>
            <span class="edge-label edge-label--left">L</span>
          </div>
        </div>
        <div class="orientation-info">
          <code>{{ deg }}deg</code>
        </div>
      </td>
      {% endfor %}
    </tr>
    {% endfor %}
  </tbody>
</table>

<h2>Convention Reference</h2>
<ul>
  <li><strong>DEG_0:</strong> Original photo orientation. TOP edge is physically at top.</li>
  <li><strong>DEG_90:</strong> Piece rotated 90 degrees CW. Original TOP now faces RIGHT.</li>
  <li><strong>DEG_180:</strong> Piece rotated 180 degrees. Original TOP now faces BOTTOM.</li>
  <li><strong>DEG_270:</strong> Piece rotated 270 degrees CW (= 90 CCW). Original TOP now faces LEFT.</li>
</ul>

<h2>How to verify</h2>
<ol>
  <li>Pick a corner piece or edge piece with a clear flat edge</li>
  <li>In DEG_0, identify which side is flat (that's the EDGE side)</li>
  <li>In DEG_90, the flat side should be rotated 90 degrees clockwise</li>
  <li>Backend rotate and CSS rotate should produce identical visual results</li>
  <li>If they differ, the rotation convention is wrong</li>
</ol>
{% endblock %}
```

### Step 3: CSS for debug page

```css
.debug-table { border-collapse: collapse; }
.debug-table th, .debug-table td { border: 1px solid #d1d5db; padding: 8px; text-align: center; }
.debug-cell { vertical-align: top; }
.orientation-box { display: flex; flex-direction: column; gap: 8px; align-items: center; }
.orientation-method { display: flex; flex-direction: column; align-items: center; }
.method-label { font-size: 10px; color: #6b7280; margin-bottom: 2px; }
.edge-labels { position: relative; width: 120px; height: 120px; }
.edge-label { position: absolute; font-size: 10px; font-weight: bold; }
.edge-label--top { top: 0; left: 50%; transform: translateX(-50%); color: red; }
.edge-label--right { right: 0; top: 50%; transform: translateY(-50%); color: blue; }
.edge-label--bottom { bottom: 0; left: 50%; transform: translateX(-50%); color: green; }
.edge-label--left { left: 0; top: 50%; transform: translateY(-50%); color: orange; }
```

### Step 4: Add segment shape display per orientation

For each orientation, show what the edge positions map to after rotation.
This uses `get_original_edge_pos()` logic:

```jinja2
<div class="edge-mapping">
  {# For DEG_90: grid-TOP was originally piece-LEFT #}
  {# Show: "TOP -> LEFT_shape", "RIGHT -> TOP_shape", etc. #}
  {% for edge in ['TOP', 'RIGHT', 'BOTTOM', 'LEFT'] %}
    {% set original = get_original_edge(edge, deg) %}
    <span>{{ edge }}: {{ piece.segment_shapes.get(original, '?') }}</span>
  {% endfor %}
</div>
```

This requires passing a helper function to the template context or computing
the mapping server-side.

---

## File touchmap

| File | Change |
|------|--------|
| `webapp_resources/templates/debug_orientations.html` | **NEW** - debug page |
| `src/snap_fit/webapp/routers/debug.py` or `ui.py` | Add `GET /debug/orientations` route |
| `webapp_resources/static/css/components.css` | Add debug page styles |

---

## Test strategy

- Manual: open `/debug/orientations`, pick a corner piece, verify flat edge rotates correctly
- Manual: compare backend-rotated and CSS-rotated images - they must match
- Manual: verify edge labels are consistent with segment shapes table
- Document findings: write a comment in `orientation_utils.py` confirming the convention
