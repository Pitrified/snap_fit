# 11 - Placed Piece Labels

**Status:** not started
**Parent:** [10_ui_notes.md](10_ui_notes.md)

## Goal

When a piece is placed on the solver grid, show a readable label on top of the cell to help the user track placements.

## Current State

- The `grid_cell` macro in `webapp_resources/templates/macros/piece_macros.html` already renders a `<span class="grid-cell__label">` for filled cells.
- The label text is currently the raw `piece_id` string (e.g. `oca_01:3`), which is functional but can be hard to read at a glance on small 90x90px cells.
- The CSS class `grid-cell__label` in `webapp_resources/static/css/components.css` positions it at the bottom-left with absolute positioning, black background.
- `PieceRecord.label` is available in the data model; it may be `None` for some datasets.

## Analysis

| Aspect | Detail |
|--------|--------|
| Data source | `session.placement[pos_key]` returns `(piece_id_str, orientation)`. The `piece_id_str` is what appears as the label. |
| Slot label | There is a `slot_type` badge on empty cells, but not on filled cells. |
| Label readability | At 90x90px, a full piece_id like `oca_01:3` is tight. Shorter labels (`#3`, `1:3`) would be cleaner. |
| Backend data | `PieceRecord.label` is populated from `SlotGrid` assignment during ingestion (e.g. `A1`, `B3`). If SlotGrid is not used, label is `None`. |

## Plan

### Step 1 - Improve label formatting in grid_cell macro

**File:** `webapp_resources/templates/macros/piece_macros.html`

- Accept an optional `labels` dict parameter in the `grid_cell` macro: `grid_cell(pos, placement, slot_type, is_target, labels)`.
- When `labels` is provided and `labels[piece_id]` exists, show that value instead of the raw `piece_id`.
- Fallback: show a shortened form of piece_id (just the piece index after the colon, like `#3`).

### Step 2 - Pass piece labels from solver template

**File:** `webapp_resources/templates/solver.html`

- The solver template already has `unplaced` (a list of PieceRecord objects).
- Build a label map in the template context: router passes `piece_labels: dict[str, str]` mapping `piece_id_str` to `piece.label or short_id`.
- This requires a small addition to the solver endpoint in `src/snap_fit/webapp/routers/ui.py`.

### Step 3 - Style the label for readability

**File:** `webapp_resources/static/css/components.css`

- Ensure `grid-cell__label` has:
  - `font-size: 0.65rem` (compact)
  - `max-width: 100%` with `overflow: hidden; text-overflow: ellipsis`
  - Semi-transparent dark background for contrast
  - White text
  - Padding `1px 3px`

## Files to touch

| File | Change |
|------|--------|
| `webapp_resources/templates/macros/piece_macros.html` | Add `labels` param to `grid_cell`, use label lookup with fallback |
| `webapp_resources/templates/solver.html` | Pass `labels` dict to `grid_cell` calls |
| `src/snap_fit/webapp/routers/ui.py` | Build `piece_labels` dict in solver view context |
| `webapp_resources/static/css/components.css` | Tweak `grid-cell__label` for readability at small sizes |

## Acceptance criteria

- Placed cells show a human-readable label (e.g. `A3` if SlotGrid label exists, or `#3` as fallback).
- Label is legible at 90x90px cell size.
- No change to the data model or API.
