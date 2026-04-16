# 12 - Orientation of Suggested Pieces

**Status:** done
**Parent:** [10_ui_notes.md](10_ui_notes.md)

## Goal

When the suggestion panel proposes a piece for a grid slot, show both the correctly rotated image and a text description of the orientation (e.g. "Place piece #5 rotated 90 degrees clockwise").

## Current State

- The suggestion panel in `solver.html` already applies CSS rotation: `style="transform: rotate({{ candidate.orientation }}deg)"`.
- The backend image endpoint (`/api/v1/pieces/{id}/img?orientation=DEG`) supports server-side rotation via OpenCV.
- `SuggestionCandidate` schema includes `orientation: int` (0, 90, 180, 270).
- The debug page `debug_orientations.html` validates that CSS rotation matches backend rotation exactly.
- Currently there is **no text label** explaining the rotation.

## Analysis

| Aspect | Detail |
|--------|--------|
| CSS vs backend rotation | CSS rotate applies to the un-rotated base image. Both are equivalent per the debug page verification. CSS is simpler (no extra API call). Backend is pixel-accurate. |
| Image display | CSS rotate can cause the image to overflow its container (a square rotated 90 degrees still fits, but the pixel boundary shifts). The current suggestion image is 150x150px in a centered block. |
| Orientation text | Human-readable labels: 0 = "no rotation", 90 = "90 degrees clockwise", 180 = "180 degrees", 270 = "90 degrees counter-clockwise" (or "270 degrees clockwise"). |
| Piece type context | The slot type (CORNER/EDGE/INNER) and slot position drive the required orientation. Showing "Slot requires CORNER at 90 degrees" helps the user understand why. |

## Plan

### Step 1 - Add orientation text to suggestion panel

**File:** `webapp_resources/templates/solver.html`

- Below the candidate image/label, add an orientation description line.
- Use a Jinja2 lookup dict for human-readable labels:
  ```
  {% set orient_text = {0: "No rotation", 90: "90\u00b0 clockwise", 180: "180\u00b0", 270: "270\u00b0 clockwise (90\u00b0 counter-clockwise)"} %}
  ```
- Render: `<p class="suggestion-orientation">{{ orient_text[candidate.orientation] }}</p>`

### Step 2 - Use backend-rotated image instead of CSS rotation

**File:** `webapp_resources/templates/solver.html`

Switch the suggestion image from CSS transform to the backend endpoint:
```
<img src="/api/v1/pieces/{{ candidate.piece_id }}/img?size=150&orientation={{ candidate.orientation }}">
```
This avoids CSS clipping and overflow issues. The image arrives already rotated - no `transform` style needed.

This same switch should be considered for the `grid_cell` macro (filled cells), but that is a larger change and is tracked in [14_rotated_piece_label.md](14_rotated_piece_label.md).

### Step 3 - Show slot type context

**File:** `webapp_resources/templates/solver.html`

Below the orientation text, add slot type context:
```
<p class="suggestion-slot-info">Slot {{ suggestion.slot }} - {{ slot_type_name }}</p>
```

To get the slot type, the router must pass `slot_types: dict[str, str]` built from `GridModel`.

**File:** `src/snap_fit/webapp/routers/ui.py`

In the solver view, instantiate `GridModel(rows, cols)` and build a slot type lookup, or compute it for just the suggested slot.

## Files to touch

| File | Change |
|------|--------|
| `webapp_resources/templates/solver.html` | Add orientation text, switch img to backend-rotated, add slot type line |
| `src/snap_fit/webapp/routers/ui.py` | Pass slot type info for suggestion slot to template |
| `webapp_resources/static/css/components.css` | Style `.suggestion-orientation` and `.suggestion-slot-info` |

## Acceptance criteria

- Suggestion panel shows human-readable orientation text (e.g. "90 degrees clockwise").
- Suggestion image is properly rotated (no CSS overflow artifacts).
- Slot type context is visible (e.g. "Slot 0,1 - EDGE").
- Grid placement cells are unaffected (separate feature).
