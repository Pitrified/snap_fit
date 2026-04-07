# UI based solver

## Overview

The goal is a human-in-the-loop jigsaw solver: the backend proposes the next placement and the user
accepts or rejects it before moving on. This replaces `NaiveLinearSolver`'s fully greedy pass with a
guided, correctable process. The existing `PlacementState`, `GridModel`, `PieceMatcher`, and
`SheetManager` already have all the primitives; most work is wiring them into a stateful session API
and a new browser UI.

---

## Current codebase gaps (must close before building the solver UI)

| Gap | Where it lives today | What is missing |
|---|---|---|
| `POST /api/v1/puzzle/solve` is a stub | `PuzzleService.solve_puzzle()` | always returns `success=False`; no real solver call |
| `GET /api/v1/interactive/session` | `interactive.py` router | hardcoded `SessionInfo(session_id="placeholder", active=False)` |
| No "run matching" route | `PieceMatcher.match_all()` exists but is never called from HTTP | need a `/api/v1/puzzle/run_matching` endpoint |
| No `PlacementState` persistence | `PlacementState` is in-memory only | need JSON serialize/deserialize |
| No piece image serving | `Piece` has numpy arrays, nothing serves them | need an `img` endpoint so the browser can show pieces |
| No interactive session model | `SessionInfo` has no placement, no pending suggestions | need a richer session schema |
| No solver tab or interactive templates | all pages are read-only data browsers | new templates needed |

---

## Preliminary changes to the UI (before the solver tab)

1. **Fix on one dataset** - pick `oca` (already has matches.json + metadata); all solver UI pages assume
   this dataset tag is loaded. Add a "current dataset" selector to settings or hard-wire it via
   `SnapFitParams`.
2. **Add a "Solver" nav link** in `base.html` pointing to `/solver`.
3. **Serve piece thumbnail images** - add `GET /api/v1/pieces/{piece_id}/img` returning a PNG cropped
   from `piece.img_orig` using `piece.contour_region` (bounding box). The template `<img>` tags
   throughout the UI can then point there. This is needed by every visual in the solver UI.
4. **Visualization primitives** (reusable HTML/JS fragments or Jinja macros):
   - `piece_card.html` macro - thumbnail + type badge + edge shape icons (IN / OUT / EDGE / WEIRD)
   - `match_card.html` macro - two piece thumbnails side-by-side, matched edges highlighted,
     similarity score, accept/reject buttons
   - `grid_canvas` - a CSS grid (or `<canvas>`) showing `GridModel` slots with placed piece
     thumbnails; empty slots shown as dashed outlines

---

## Main solve flow (step by step)

### Session lifecycle

```
POST /api/v1/interactive/sessions          -> create session, returns session_id
GET  /api/v1/interactive/sessions/{id}     -> current state (PlacementState snapshot)
POST /api/v1/interactive/sessions/{id}/next_suggestion   -> propose next placement
POST /api/v1/interactive/sessions/{id}/accept            -> confirm proposed placement
POST /api/v1/interactive/sessions/{id}/reject            -> reject; advance to next candidate
POST /api/v1/interactive/sessions/{id}/undo              -> remove last placed piece
DELETE /api/v1/interactive/sessions/{id}  -> discard session
```

### Step-by-step flow

1. **Start session** - user picks a dataset + grid size (or infer via `infer_grid_size`); backend
   creates a `SolveSession` with a new `PlacementState` and a `GridModel`.
2. **Seed piece** - user picks any corner piece (or backend picks `random.choice(corners)`); it is
   placed at `GridPos(0, 0)` with `Orientation.DEG_0`.
3. **Next suggestion loop:**
   - Backend picks the next "open slot" - a grid position adjacent to the current island with at
     least one already-placed neighbor.
   - For that slot's `OrientedPieceType`, backend calls `PieceMatcher.get_matches_for_piece` on each
     neighbor's free edge and scores all unplaced candidates via `scoring.score_edge`.
   - Top-K candidates (default 3) are returned to the browser ranked by score.
4. **User accepts** first candidate or clicks through alternatives.
5. **Rejected candidates** are flagged; backend never re-proposes them for that slot in this session
   (stored in `SolveSession.rejected: dict[GridPos, set[PieceId]]`).
6. **Island grows** - loop from step 3. When all slots are filled, session is marked `complete`.

### Slot selection strategy (brainstorm)

- **Most-constrained first** - pick the open slot with the most already-placed neighbors (maximizes
  cross-edge scoring signal). Simple to implement: iterate `PlacementState.empty_positions()`, count
  neighbors via `GridModel.neighbors()`.
- **Row-by-row** - mimic `NaiveLinearSolver` order; less optimal but predictable for the user.
- **User override** - user can click any empty slot on the grid canvas to force the solver to suggest
  for that slot next. Needs a `POST …/next_suggestion` body with an optional `override_pos`.

---

## Multiple solve islands

Allowing the user to start from any position at any time adds minimal backend complexity - `PlacementState`
already supports non-contiguous placements. The main complications are:

- **Scoring across disconnected islands is meaningless** until they merge; present score as "within-island" only.
- **Grid alignment ambiguity** - two islands could be internally consistent but misaligned relative to
  each other. Deferring cross-island alignment until islands are adjacent is the safest option.
- **Recommendation**: allow free placement from the start but surface a clear warning in the UI when
  the user picks a seed piece for a second island. Keep it in scope for v1 so the architecture does
  not have to be changed later.

---

## Session state model

```python
# new Pydantic schema (src/snap_fit/webapp/schemas/session.py)

class SolveSession(BaseModel):
    session_id: str
    dataset_tag: str
    grid_rows: int
    grid_cols: int
    placement: dict[str, tuple[str, int]]   # GridPos str -> (PieceId str, Orientation int)
    pending_suggestion: SuggestionBundle | None
    rejected: dict[str, list[str]]          # GridPos str -> list[PieceId str]
    score: float | None
    complete: bool
    created_at: datetime
    updated_at: datetime

class SuggestionBundle(BaseModel):
    slot: str                               # GridPos as "ro,co"
    candidates: list[SuggestionCandidate]   # ranked, top first
    current_index: int                      # which candidate is displayed

class SuggestionCandidate(BaseModel):
    piece_id: str
    orientation: int
    score: float
    neighbor_scores: dict[str, float]       # per-neighbor edge score breakdown
```

Sessions can be stored in-memory (Python dict keyed by `session_id`) for the prototype. Persistence to
`cache/{tag}/sessions/{session_id}.json` for durability is a follow-on step.

---

## UI updates

### New pages / routes (under `ui` router)

| Route | Template | Purpose |
|---|---|---|
| `GET /solver` | `solver_home.html` | list active sessions + "new session" form |
| `GET /solver/{session_id}` | `solver.html` | main interactive solver view |

### `solver.html` layout

```
+-------------------------+------------------------------+
|  Grid canvas            |  Suggestion panel            |
|  (GridModel slots,      |  - piece thumbnail           |
|   placed thumbnails,    |  - neighbor context          |
|   empty dashed boxes)   |  - score breakdown           |
|                         |  - [Accept] [Skip] [Undo]    |
+-------------------------+------------------------------+
|  Progress bar  |  Score |  Pieces placed N/M           |
+-----------------------------------------------------------+
```

- Grid canvas is a CSS `grid` where each cell is a `<div>` with a `background-image` pointing to the
  piece thumbnail endpoint. Clicking an empty cell fires `override_pos`.
- Suggestion panel shows the current `SuggestionBundle.candidates[current_index]`. The [Skip] button
  increments `current_index`; [Accept] POSTs to `/accept`; [Undo] POSTs to `/undo`.
- The panel also shows which edges are being matched (highlight on the piece thumbnail via a colored
  border on the appropriate side).

### Visualization primitives

- **Piece thumbnail** - `<img src="/api/v1/pieces/{piece_id}/img?size=100">` hit the new image endpoint.
- **Edge highlight** - CSS classes `.edge-top`, `.edge-right`, `.edge-bottom`, `.edge-left` overlay a
  colored border on the matching side of the thumbnail.
- **Shape badge** - small colored dot (IN=blue, OUT=red, EDGE=grey, WEIRD=yellow) at each edge midpoint.
- **Slot type badge** - corner / edge / inner label on empty slots so users know what piece type to expect.
- **Score color** - similarity score rendered with a color gradient (green < 0.3, yellow < 0.7, red >= 0.7).

---

## Backend implementation plan (phased)

### Phase 1 - piece image endpoint (unblocks all UI work)

- Add `GET /api/v1/pieces/{piece_id}/img` in `piece_ingestion.py` router.
- Service method `PieceService.get_piece_img(piece_id) -> bytes` - load sheet via `SheetManager`,
  crop `piece.img_orig` by `contour_region`, encode as PNG, return.
- `PieceService` currently reads from SQLite records only and does not hold a live `SheetManager`.
  Options:
  - **Option A (lazy load)**: load the sheet image file on demand from the path stored in `SheetRecord.img_path`.
  - **Option B (full load)**: add a `SheetManager` instance to `PieceService` that loads on first request.
  - Option A is simpler and avoids memory issues for large datasets.

### Phase 2 - session CRUD + PlacementState serialization

- Serialize `PlacementState` to/from `dict[str, tuple[str, int]]` (GridPos -> (PieceId, orientation)).
- Add `InteractiveService` class in `src/snap_fit/webapp/services/interactive_service.py`:
  - Holds `_sessions: dict[str, SolveSession]` (in-memory for now).
  - `create_session(tag, rows, cols) -> SolveSession`
  - `get_session(session_id) -> SolveSession`
  - `place(session_id, piece_id, pos, orientation) -> SolveSession`
  - `undo(session_id) -> SolveSession`
- Wire into the `interactive` router (replace the placeholder endpoints).

### Phase 3 - suggestion engine

- `suggest_next(session_id) -> SuggestionBundle`:
  - Find most-constrained open slot.
  - Gather unplaced pieces of the correct `PieceType`.
  - Score each candidate against placed neighbors using `scoring.score_edge`.
  - Filter out `rejected[slot]`.
  - Return top-K ranked by score.
- Add `accept(session_id) -> SolveSession` and `reject(session_id) -> SolveSession` endpoints.

### Phase 4 - run matching endpoint (prerequisite if matches not yet computed)

- Add `POST /api/v1/puzzle/run_matching` that calls `PieceMatcher.match_all()` + `save_matches_db()`.
- Show progress via a simple polling pattern: return a job id, poll `GET /api/v1/puzzle/matching_status/{job_id}`.
- For the initial prototype, matching can just be a blocking call with a loading spinner.

### Phase 5 - solver UI templates

- Build `solver_home.html` and `solver.html` using existing `base.html` shell.
- JavaScript is minimal: fetch API calls for accept/reject/undo, DOM updates for the suggestion panel,
  CSS grid rerender on each state change. No heavy framework needed.

---

## Open questions / design decisions

1. **Session storage** - in-memory dict is fine for a single-process dev server. If the FastAPI app is
   restarted, all sessions are lost. Is that acceptable for the prototype? If not, persist to
   `cache/{tag}/sessions/{id}.json` on every state change.
2. **Orientation display** - pieces are stored in their original photo orientation. When rendering in
   the grid, the CSS `transform: rotate(Ndeg)` on the thumbnail handles display-side rotation.
   Confirm that `Orientation` enum values map directly to CSS degrees (DEG_0=0, DEG_90=90, etc.).
3. **Multiple datasets** - the session model includes `dataset_tag`. The `InteractiveService` will
   need to load a separate `SheetManager` + `PieceMatcher` per tag. Lazy-load on session create.
4. **Reject propagation** - if a user rejects piece X for slot (1,1), should X also be penalized for
   adjacent slots? Probably not - keep rejection scoped to the specific slot.
5. **Score normalization** - `SegmentMatcher` returns raw similarity (lower=better, 1e6=incompatible).
   Display a normalized 0-1 confidence (1 = best) to users: `confidence = 1 / (1 + raw_score)`.
6. **Undo depth** - simple stack of `(GridPos, PieceId, Orientation)` tuples. How many levels? Start
   with unlimited undo (just a list), trim to last 20 for memory safety.
7. **Manual similarity override** - `MatchResult.similarity_manual_` already exists. Expose an input
   in the match_card so users can fine-tune scores independently of the solver flow.
8. **Grid size inference vs manual** - `infer_grid_size` from `solver/utils.py` may return `None` for
   unusual piece counts. The "new session" form should let the user confirm or override rows/cols.
