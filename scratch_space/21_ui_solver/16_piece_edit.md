# 16 - Piece Segment Edit

**Status:** not started
**Parent:** [10_ui_notes.md](10_ui_notes.md)

## Goal

On the piece detail page, allow the user to manually change the detected segment shape labels (IN/OUT/EDGE/WEIRD) when the automatic detection is wrong.

## Current State

- The piece detail page shows a read-only segments table with 4 rows (TOP/RIGHT/BOTTOM/LEFT) and shape badges.
- `PieceRecord` stores `segment_shapes: dict[str, str]` (e.g. `{"top": "IN", "right": "OUT", "bottom": "EDGE", "left": "OUT"}`).
- `PieceRecord` is persisted in `dataset.db` via `DatasetStore` (SQLite).
- `SegmentShape` enum: `IN`, `OUT`, `EDGE`, `WEIRD`.
- Segment shapes affect:
  - **Solver type classification**: `OrientedPieceType` (CORNER/EDGE/INNER) is derived from which edges are EDGE-shaped. Changing a shape may reclassify the piece type.
  - **Match compatibility**: `Segment.is_compatible()` rejects EDGE+anything and same-polarity (IN+IN, OUT+OUT) pairs. Changing a shape changes which matches are valid.
  - **Match scores**: Existing cached matches may become invalid if shape compatibility flips.
- There is no API endpoint for updating piece metadata.
- The `DatasetStore` has write methods (`save_piece`, `save_pieces`) but no `update_piece_segment_shape` method.

## Analysis

| Aspect | Detail |
|--------|--------|
| Scope of change | Changing a single piece's segment shape propagates to: PieceRecord in DB, OrientedPieceType, flat_edges list, all match results involving that segment, solver type partitioning. |
| Cascade options | **Minimal:** Update the DB record only. Matches stay as-is but may be inconsistent. **Full:** Re-run matching for the affected segment. |
| Recommended | Minimal update + invalidation flag. Add a "re-run matching" button (already exists in settings page) and mark matches as potentially stale. |
| UI pattern | Inline edit: replace shape badge with a `<select>` dropdown. Save button triggers `PATCH` request. |
| Validation | Changing an EDGE to IN/OUT means the piece loses a flat edge. Changing IN/OUT to EDGE adds one. The piece type (CORNER/EDGE/INNER) must be recomputed: 0 EDGE = INNER, 1 EDGE = EDGE, 2 EDGE = CORNER. |

## Plan

### Step 1 - Add PATCH endpoint for piece segment shapes

**File:** `src/snap_fit/webapp/routers/piece_ingestion.py`

```python
@router.patch("/{piece_id}/segments")
async def update_segment_shapes(
    piece_id: str,
    updates: dict[str, str],  # e.g. {"top": "OUT", "left": "EDGE"}
):
```

### Step 2 - Add update method to PieceService

**File:** `src/snap_fit/webapp/services/piece_service.py`

New method `update_segment_shapes(piece_id, updates)`:

1. Load the `PieceRecord` from DB.
2. Validate: each key must be a valid `EdgePos`, each value a valid `SegmentShape`.
3. Update `segment_shapes` dict.
4. Recompute `flat_edges`: edges where shape is `EDGE`.
5. Recompute `oriented_piece_type`: based on count of flat edges and their positions.
6. Save updated record back to DB.
7. Return updated `PieceRecord`.

### Step 3 - Add update method to DatasetStore

**File:** `src/snap_fit/persistence/dataset_store.py` (or wherever DatasetStore lives)

New method `update_piece(piece_id, updates)` that updates specific fields of a piece record in SQLite.

### Step 4 - Add edit UI to piece detail template

**File:** `webapp_resources/templates/piece_detail.html`

Replace the static segments table with an editable form:

```html
<table>
  <thead>
    <tr><th>Edge</th><th>Shape</th><th></th></tr>
  </thead>
  <tbody>
    {% for edge, shape in piece.segment_shapes.items() %}
    <tr>
      <td>{{ edge }}</td>
      <td>
        <select id="seg-{{ edge }}" class="seg-select">
          {% for s in ["IN", "OUT", "EDGE", "WEIRD"] %}
            <option value="{{ s }}" {% if s == shape %}selected{% endif %}>{{ s }}</option>
          {% endfor %}
        </select>
      </td>
      <td>
        <span class="badge {% if shape == 'IN' %}badge-success{% elif shape == 'OUT' %}badge-info{% elif shape == 'EDGE' %}badge-warning{% else %}badge{% endif %}">
          {{ shape }}
        </span>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
<button id="save-segments" class="btn btn--accept" onclick="saveSegments()">
  Save Changes
</button>
<span id="save-status"></span>
```

### Step 5 - Add JavaScript for the save action

**File:** `webapp_resources/templates/piece_detail.html` (inline script, or new JS file)

```javascript
async function saveSegments() {
  const updates = {};
  document.querySelectorAll('.seg-select').forEach(sel => {
    const edge = sel.id.replace('seg-', '');
    updates[edge] = sel.value;
  });
  const resp = await fetch('/api/v1/pieces/{{ piece.piece_id }}/segments', {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(updates),
  });
  if (resp.ok) {
    document.getElementById('save-status').textContent = 'Saved!';
    location.reload();
  } else {
    document.getElementById('save-status').textContent = 'Error saving.';
  }
}
```

## Side effects and warnings

- After editing segment shapes, existing match results for that piece may be stale.
- Display a warning: "Segment shapes changed. Consider re-running matching for this dataset."
- The piece type badge on the detail page should update after save (CORNER/EDGE/INNER).
- The solver's type partitioning will pick up the DB change on next session creation or suggestion.

## Files to touch

| File | Change |
|------|--------|
| `src/snap_fit/webapp/routers/piece_ingestion.py` | New `PATCH /{piece_id}/segments` endpoint |
| `src/snap_fit/webapp/services/piece_service.py` | New `update_segment_shapes()` method |
| `src/snap_fit/persistence/dataset_store.py` | New `update_piece()` method (or extend existing) |
| `webapp_resources/templates/piece_detail.html` | Editable segments table with save button |
| `webapp_resources/static/css/components.css` | Style for inline selects and save button |

## Acceptance criteria

- Piece detail page shows a dropdown for each edge's shape.
- User can change shape (e.g. WEIRD to OUT) and click Save.
- After save, the page reloads with updated shapes, flat_edges, and piece type.
- A warning is shown reminding the user to re-run matching if shapes changed.
- Invalid edge/shape values are rejected by the API with a clear error.
