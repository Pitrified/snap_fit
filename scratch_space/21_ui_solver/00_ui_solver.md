# UI based solver

## Status tracking

Always track status of the current implementation state in
[01_status_tracker.md](01_status_tracker.md).

Sub-plans: 02 through 09 in this folder.


## Overview

The goal is a human-in-the-loop jigsaw solver: the backend proposes the next placement and the user
accepts or rejects it before moving on. This replaces `NaiveLinearSolver`'s fully greedy pass with a
guided, correctable process. The existing `PlacementState`, `GridModel`, `PieceMatcher`, and
`SheetManager` already have all the primitives; most work is wiring them into a stateful session API
and a new browser UI.

---

## Completed since initial plan (feat/sheet-identity)

The `scratch_space/20_piece_markers/` feature branch implemented significant infrastructure that
this solver UI plan originally assumed was missing. Summary of what landed:

| Component | What was built | Impact on this plan |
|---|---|---|
| `SheetMetadata` + QR codes | Machine-readable sheet identity (tag, index, total, board config, date) encoded as QR codes on printed boards | Datasets are now self-identifying; session creation can auto-detect dataset tag |
| `SlotGrid` + labels | Grid of labeled slots (A1, B2, ...) printed on boards; centroid-to-slot mapping at ingest time | Pieces have human-readable `label` field; solver UI can show slot labels |
| `BoardImageComposer` | Assembles printable board images with ArUco ring + slot labels + QR metadata | Not directly used by solver UI but enables new datasets |
| `Piece.label` + `Piece.sheet_origin` + `Piece.centroid_in_sheet` | Pieces now carry slot label, origin in sheet coords, and can compute sheet-space centroid | Piece image endpoint can crop from sheet image using stored coords |
| `Sheet.crop_offset` + `Sheet.metadata` + `Sheet.slot_grid` | Sheet tracks coordinate transform between board-image and cropped-sheet space | Enables correct overlay of slot grid on piece images |
| `PieceRecord.label` + `PieceRecord.sheet_origin` | Persistence of new fields in Pydantic records | Available via API without loading full Sheet objects |
| `SheetRecord.metadata` | Persistence of SheetMetadata | Available via API for dataset identification |
| SQLite schema migrations | `pieces` table has `label`, `sheet_origin` columns; `sheets` table has `metadata` column | No schema work needed for these fields |
| Template updates | All UI templates show label, sheet_origin, metadata fields | Piece/sheet detail pages already display new data |
| `MetadataZoneConfig` + `SlotGridConfig` | Config models for board generation parameters | Reusable for solver grid visualization |

---

## Current codebase gaps (must close before building the solver UI)

| Gap | Where it lives today | What is missing | Status |
|---|---|---|---|
| `POST /api/v1/puzzle/solve` is a stub | `PuzzleService.solve_puzzle()` | always returns `success=False`; no real solver call | **open** |
| `GET /api/v1/interactive/session` | `interactive.py` router | hardcoded `SessionInfo(session_id="placeholder", active=False)` | **open** |
| No "run matching" route | `PieceMatcher.match_all()` exists but is never called from HTTP | need a `/api/v1/puzzle/run_matching` endpoint | **open** |
| No `PlacementState` persistence | `PlacementState` is in-memory only | need JSON serialize/deserialize | **open** |
| No piece image serving | `Piece` has numpy arrays, nothing serves them | need an `img` endpoint so the browser can show pieces | **open** |
| No interactive session model | `SessionInfo` has no placement, no pending suggestions | need a richer session schema | **open** |
| No solver tab or interactive templates | all pages are read-only data browsers | new templates needed | **open** |
| No piece labels or slot identity | pieces only had numeric index | need slot-grid labels on pieces | **done** (feat/sheet-identity) |
| No sheet metadata or QR identity | no machine-readable sheet identity | need QR codes + SheetMetadata | **done** (feat/sheet-identity) |
| SQLite missing piece/sheet fields | persistence dropped new fields | need schema migration | **done** (feat/sheet-identity) |
| Templates not showing new fields | label, metadata, sheet_origin not displayed | update templates | **done** (feat/sheet-identity) |

---

## Preliminary changes to the UI (before the solver tab)

1. **Fix on one dataset** - all solver UI pages assume this dataset tag is loaded.
   Add a "current dataset" selector to settings (dropdown looking at the valid folders).
   Add a `settings` page if needed.
   Select it so that all routes respect it.
2. **Add a "Solver" nav link** in `base.html` pointing to `/solver`.
3. **Serve piece thumbnail images** - add `GET /api/v1/pieces/{piece_id}/img` returning a PNG cropped
   from `piece.img_orig` using `piece.contour_region` (bounding box). The template `<img>` tags
   throughout the UI can then point there. This is needed by every visual in the solver UI.
   NOTE: `Piece` now has `sheet_origin` and `centroid_in_sheet` properties (from feat/sheet-identity),
   so the crop region is fully recoverable from the cached `PieceRecord`. The endpoint needs to load
   the sheet image from disk (path in `SheetRecord.img_path`), then crop using `contour_region`.
4. **Visualization primitives** (reusable HTML/JS fragments or Jinja macros):
   - `piece_card.html` macro - thumbnail + label badge (e.g. "A1") + type badge + edge shape icons (IN / OUT / EDGE / WEIRD)
   - `match_card.html` macro - two piece thumbnails side-by-side, matched edges highlighted,
     similarity score, accept/reject buttons
   - `grid_canvas` - a CSS grid (or `<canvas>`) showing `GridModel` slots with placed piece
     thumbnails; empty slots shown as dashed outlines; slot labels from `SlotGrid` shown in empty cells
5. **Piece detail enhancement** - templates already show `label`, `sheet_origin`, and `metadata` fields
   (done in feat/sheet-identity). Remaining: make edge shapes editable, add piece image display,
   and add a link to the sheet image with the piece's position highlighted.

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
   UPDATE: We also want a more flexible flow where the user can pick any piece for any slot, place it in a random spot in the grid.  The solver will then build around it, and the user can start multiple islands if they want. This is more complex but more user-friendly and allows for more flexible strategies.
3. **Next suggestion loop:**
   - Backend picks the next "open slot" - a grid position adjacent to the current island with at
     least one already-placed neighbor.
   - For that slot's `OrientedPieceType`, backend calls `PieceMatcher.get_matches_for_piece` on each
     neighbor's free edge and scores all unplaced candidates via `scoring.score_edge`.
   - Top-K candidates (default 3) are returned to the browser ranked by score.
4. **User accepts** first candidate or clicks through alternatives.
   Also updates the matching score to 0 (best) so it is ranked at the top of the list if they skip and come back later.
5. **Rejected candidates** are flagged; backend never re-proposes them for that slot in this session
   (stored in `SolveSession.rejected: dict[GridPos, set[PieceId]]`).
   Also update the matching score to reflect the manual rejection (e.g. set to 1e6) so they are ranked at the bottom of the list.
6. **Island grows** - loop from step 3. When all slots are filled, or all pieces
   are placed or all matches are rejected, session is marked `complete`.

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
    piece_label: str | None                 # slot-grid label (e.g. "A1") for identification
    orientation: int
    score: float
    neighbor_scores: dict[str, float]       # per-neighbor edge score breakdown
```

Sessions are persisted to SQLite (`cache/{tag}/dataset.db`) in a `sessions` table alongside the
existing `sheets` and `pieces` tables. The `DatasetStore` already supports schema migrations, so
adding a `sessions` table follows the established pattern. On app restart, active sessions are
reloaded from the database.

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
  piece thumbnail endpoint. Clicking an empty cell fires `override_pos`. Empty cells show the slot
  type badge (corner/edge/inner). Placed pieces show their `label` (e.g. \"A1\") as an overlay.
- Suggestion panel shows the current `SuggestionBundle.candidates[current_index]`. The [Skip] button
  increments `current_index`; [Accept] POSTs to `/accept`; [Undo] POSTs to `/undo`.
- The panel also shows which edges are being matched (highlight on the piece thumbnail via a colored
  border on the appropriate side).

### Visualization primitives

- **Piece thumbnail** - `<img src="/api/v1/pieces/{piece_id}/img?size=100">` hit the new image endpoint.
- **Piece label overlay** - show the slot-grid label (e.g. "A1") from `PieceRecord.label` on or beside
  the thumbnail so the user can identify which physical piece it is. This label is from the printed board.
- **Edge highlight** - CSS classes `.edge-top`, `.edge-right`, `.edge-bottom`, `.edge-left` overlay a
  colored border on the matching side of the thumbnail.
- **Shape badge** - small colored dot (IN=blue, OUT=red, EDGE=grey, WEIRD=yellow) at each edge midpoint.
- **Slot type badge** - corner / edge / inner label on empty slots so users know what piece type to expect.
- **Score color** - similarity score rendered with a color gradient (green < 0.3, yellow < 0.7, red >= 0.7).

---

## Backend implementation plan (phased)

### Phase 1 - piece image endpoint (unblocks all UI work)

- Add `GET /api/v1/pieces/{piece_id}/img` in `piece_ingestion.py` router.
- Service method `PieceService.get_piece_img(piece_id) -> bytes` - load sheet image from disk
  (path from `SheetRecord.img_path` in SQLite), crop using `PieceRecord.contour_region` +
  `PieceRecord.sheet_origin`, encode as PNG, return.
- `PieceRecord` now has `sheet_origin: tuple[int, int]` and `contour_region` which together
  define the exact crop rectangle. No live `SheetManager` needed - just read the image file
  and crop the region. This is Option A (lazy load from disk) and avoids memory issues.
- For rotated views (needed by solver), accept an optional `?orientation=90` query param
  and apply `cv2.rotate()` before encoding.

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

### Phase 6 - orientation debug page

- Build a debug page showing each piece rotated in all 4 orientations (DEG_0, DEG_90, DEG_180, DEG_270).
- Verify that `Orientation` enum values map correctly to CSS `transform: rotate(Ndeg)` and that
  the visual rotation matches the internal state. Document the OpenCV vs numpy array orientation
  and indexing differences (OpenCV uses BGR, row-major; rotation direction conventions differ).
- This is a tricky source of bugs - the debug page should make mismatches immediately visible.

---

## Open questions / design decisions

1. **Session storage** - DECIDED: use SQLite-based persistence (not in-memory dict). Store sessions
   in `cache/{tag}/dataset.db` alongside existing pieces/sheets tables. The `DatasetStore` already
   handles migrations, so add a `sessions` table.
2. **Orientation display** - DECIDED: build a debug page (Phase 6) showing all 4 rotations per piece.
   Verify OpenCV rotation direction vs CSS `transform: rotate()`. Document the numpy row-major
   vs OpenCV BGR conventions. This is the single biggest visual-bug risk.
3. **Multiple datasets** - the session model includes `dataset_tag`. The `InteractiveService` will
   need to load a separate `SheetManager` + `PieceMatcher` per tag. Lazy-load on session create.
   NOTE: `SheetRecord` now carries `metadata: SheetMetadata` with `tag_name`, so dataset identity
   is machine-readable from QR codes (feat/sheet-identity).
4. **Reject propagation** - if a user rejects piece X for slot (1,1), should X also be penalized for
   adjacent slots? Probably not - keep rejection scoped to the specific slot.
5. **Score normalization** - `SegmentMatcher` returns raw similarity (lower=better, 1e6=incompatible).
   Display a normalized 0-1 confidence (1 = best) to users: `confidence = 1 / (1 + raw_score)`.
6. **Undo depth** - simple stack of `(GridPos, PieceId, Orientation)` tuples. How many levels? Start
   with unlimited undo (just a list), trim to last 20 for memory safety.
7. **Manual similarity override** - `MatchResult.similarity_manual_` already exists. Expose an input
   in the match_card so users can fine-tune scores independently of the solver flow.
8. **Grid size inference vs manual** - DECIDED: not mandatory. Use the "free island" mode - the user
   can start from any piece and position, placing them freely on a canvas. The solver builds around
   placed pieces. `SlotGrid` labels (from feat/sheet-identity) can inform the user which physical
   slot a piece came from, but the solver grid is independent of the printed board grid.
9. **Piece labels in solver context** - pieces now have `label` (e.g. "A1") from slot-grid assignment
   during ingestion (feat/sheet-identity). The solver UI should display these labels alongside
   piece thumbnails to help the user identify physical pieces. The label is the printed slot
   position on the board, not the solver grid position.
