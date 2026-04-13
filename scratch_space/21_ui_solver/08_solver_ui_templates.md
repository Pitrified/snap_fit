# 08 - Solver UI Templates

> **Status:** not started
> **Depends on:** 03 (piece images), 04 (session CRUD), 05 (suggestion engine), 07 (viz primitives)
> **Main plan ref:** Phase 5

---

## Objective

Build the two main solver UI pages: the session list/create page (`solver_home.html`)
and the interactive solver view (`solver.html`). These are the user-facing frontend
for the human-in-the-loop solve flow.

---

## Current state

- Nav has: Home, Sheets, Pieces, Matches. No Solver link.
- No solver-related templates exist.
- Interactive router is a stub (will be rewritten in sub-plan 04).
- Visualization macros will be created in sub-plan 07.

---

## Plan

### Page 1: `GET /solver` - Session Home

Template: `webapp_resources/templates/solver_home.html`

Layout:
```
+-------------------------------------------------------+
|  Solver Sessions                                      |
+-------------------------------------------------------+
|  New Session                                          |
|  Dataset: [dropdown]  Rows: [__]  Cols: [__]          |
|  [Create Session]                                     |
+-------------------------------------------------------+
|  Active Sessions                                      |
|  +---+----------+------+-------+--------+-----------+ |
|  | # | Dataset  | Grid | Pieces| Status | Actions   | |
|  +---+----------+------+-------+--------+-----------+ |
|  | 1 | oca      | 6x8  | 12/48 | active | [Open]    | |
|  | 2 | demo     | 3x4  | 12/12 | done   | [Open]    | |
|  +---+----------+------+-------+--------+-----------+ |
+-------------------------------------------------------+
```

Route in `ui.py`:
```python
@router.get("/solver", response_class=HTMLResponse, summary="Solver home")
async def solver_home(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    interactive_service: Annotated[InteractiveService, Depends(...)],
) -> HTMLResponse:
    datasets = settings.available_datasets()
    tag = settings.active_dataset
    sessions = interactive_service.list_sessions(tag) if tag else []
    return templates.TemplateResponse(
        request,
        "solver_home.html",
        {"title": "Solver", "datasets": datasets, "sessions": sessions, "current_tag": tag},
    )
```

Form submission:
- JavaScript `POST /api/v1/interactive/sessions` with dataset_tag, grid_rows, grid_cols
- On success, redirect to `/solver/{session_id}?dataset_tag={tag}`

### Page 2: `GET /solver/{session_id}` - Interactive Solver

Template: `webapp_resources/templates/solver.html`

Layout (from main plan):
```
+-------------------------+------------------------------+
|  Grid canvas            |  Suggestion panel            |
|  (GridModel slots,      |  - piece thumbnail           |
|   placed thumbnails,    |  - neighbor context          |
|   empty dashed boxes)   |  - score breakdown           |
|                         |  - [Accept] [Skip] [Undo]    |
+-------------------------+------------------------------+
|  Info bar: Progress N/M | Total score | Status         |
+-------------------------------------------------------+
|  Unplaced pieces (scrollable row of piece_cards)       |
+-------------------------------------------------------+
```

Route in `ui.py`:
```python
@router.get("/solver/{session_id}", response_class=HTMLResponse, summary="Solver view")
async def solver_page(
    request: Request,
    session_id: str,
    dataset_tag: str,
    interactive_service: ...,
    piece_service: ...,
) -> HTMLResponse:
    session = interactive_service.get_session(dataset_tag, session_id)
    all_pieces = piece_service.list_pieces_for_tag(dataset_tag)
    placed_ids = set(pid for pid, _ in session.placement.values())
    unplaced = [p for p in all_pieces if str(p.piece_id) not in placed_ids]
    return templates.TemplateResponse(
        request,
        "solver.html",
        {
            "title": f"Solver: {session_id[:8]}",
            "session": session,
            "unplaced": unplaced,
        },
    )
```

### Grid canvas implementation

The grid is rendered as a CSS grid with `grid-template-columns: repeat(cols, 90px)`:

```jinja2
{% from "macros/piece_macros.html" import grid_cell %}

<div class="solver-grid"
     style="grid-template-columns: repeat({{ session.grid_cols }}, 90px);
            grid-template-rows: repeat({{ session.grid_rows }}, 90px);">
  {% for ro in range(session.grid_rows) %}
    {% for co in range(session.grid_cols) %}
      {% set pos_key = ro ~ "," ~ co %}
      {% set placement = session.placement.get(pos_key) %}
      {{ grid_cell(pos_key, placement=placement, is_target=(pos_key == suggestion_slot)) }}
    {% endfor %}
  {% endfor %}
</div>
```

### Suggestion panel

Rendered from the `SuggestionBundle` returned by the `next_suggestion` API:

```jinja2
{% if suggestion %}
<div class="suggestion-panel">
  <h3>Suggested for slot {{ suggestion.slot }}</h3>
  {% set candidate = suggestion.candidates[suggestion.current_index] %}
  <div class="suggestion-candidate">
    {{ piece_card(candidate, size=150) }}
    <div class="suggestion-scores">
      <p>Total: {{ score_badge(candidate.score) }}</p>
      {% for pos, score in candidate.neighbor_scores.items() %}
        <p>vs {{ pos }}: {{ score_badge(score) }}</p>
      {% endfor %}
    </div>
    <div class="suggestion-nav">
      {{ suggestion.current_index + 1 }} / {{ suggestion.candidates | length }}
    </div>
  </div>
  <div class="suggestion-actions">
    <button onclick="acceptSuggestion()" class="btn btn--accept">Accept</button>
    <button onclick="skipSuggestion()" class="btn btn--skip">Skip</button>
    <button onclick="undoLast()" class="btn btn--undo">Undo</button>
  </div>
</div>
{% else %}
<div class="suggestion-panel suggestion-panel--empty">
  <p>Click an empty slot or press "Next Suggestion"</p>
  <button onclick="nextSuggestion()" class="btn">Get Suggestion</button>
</div>
{% endif %}
```

### JavaScript interactions

Minimal JS in `webapp_resources/static/js/solver.js`:

```javascript
const SESSION_ID = '{{ session.session_id }}';
const DATASET_TAG = '{{ session.dataset_tag }}';
const API_BASE = `/api/v1/interactive/sessions/${SESSION_ID}`;

async function nextSuggestion(overridePos = null) {
    const body = overridePos ? {override_pos: overridePos} : {};
    const res = await fetch(`${API_BASE}/next_suggestion?dataset_tag=${DATASET_TAG}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
    });
    const data = await res.json();
    renderSuggestion(data);
}

async function acceptSuggestion() {
    const res = await fetch(`${API_BASE}/accept?dataset_tag=${DATASET_TAG}`, {method: 'POST'});
    const session = await res.json();
    renderGrid(session);
    nextSuggestion();  // auto-advance
}

async function skipSuggestion() {
    const res = await fetch(`${API_BASE}/reject?dataset_tag=${DATASET_TAG}`, {method: 'POST'});
    const data = await res.json();
    renderSuggestion(data);
}

async function undoLast() {
    const res = await fetch(`${API_BASE}/undo?dataset_tag=${DATASET_TAG}`, {method: 'POST'});
    const session = await res.json();
    renderGrid(session);
}

function selectSlot(posKey) {
    nextSuggestion(posKey);
}

function renderGrid(session) {
    // Re-render grid cells with updated placement data
    // Could also just reload the page for simplicity
    location.reload();
}

function renderSuggestion(bundle) {
    // Update suggestion panel DOM
    // For v1, just reload the page
    location.reload();
}
```

**v1 approach:** Use full page reloads after each action. This is simple and
correct. Optimize to partial DOM updates later if needed.

### Unplaced pieces row

A scrollable horizontal row at the bottom showing all unplaced pieces:

```jinja2
<div class="unplaced-pieces">
  <h3>Unplaced Pieces ({{ unplaced | length }})</h3>
  <div class="unplaced-pieces__scroll">
    {% for piece in unplaced %}
      {{ piece_card(piece, size=60, show_shapes=false) }}
    {% endfor %}
  </div>
</div>
```

CSS:
```css
.unplaced-pieces__scroll { display: flex; overflow-x: auto; gap: 4px; padding: 8px 0; }
```

### Info bar

```jinja2
<div class="solver-info">
  <span>Placed: {{ session.placed_count }} / {{ session.total_cells }}</span>
  <progress value="{{ session.placed_count }}" max="{{ session.total_cells }}"></progress>
  {% if session.score is not none %}
    <span>Score: {{ "%.2f" | format(session.score) }}</span>
  {% endif %}
  <span class="badge">{{ "Complete" if session.complete else "In Progress" }}</span>
</div>
```

---

## File touchmap

| File | Change |
|------|--------|
| `webapp_resources/templates/solver_home.html` | **NEW** - session list + create form |
| `webapp_resources/templates/solver.html` | **NEW** - interactive solver view |
| `webapp_resources/static/js/solver.js` | **NEW** - JS interactions |
| `webapp_resources/templates/base.html` | Add "Solver" nav link (if not done in 02) |
| `src/snap_fit/webapp/routers/ui.py` | Add `GET /solver` and `GET /solver/{session_id}` routes |

---

## Test strategy

- Manual: create session from solver home, verify redirect to solver view
- Manual: solver view renders grid with correct dimensions
- Manual: click empty cell, verify suggestion appears
- Manual: accept/skip/undo buttons work (page reloads)
- Manual: unplaced pieces row scrolls horizontally
- Manual: progress bar updates after placement
- E2E test: Playwright or similar - create session, accept 3 suggestions, undo 1
