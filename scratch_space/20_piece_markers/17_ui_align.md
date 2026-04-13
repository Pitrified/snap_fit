# Align existing UI

## Overview

Some elements and objects changed in this feature, as tracked in
`scratch_space/20_piece_markers/*`

please look at the current state of the UI/backend and see if there are any misalignments with the new data structures, and if so, align them.

## Summary of changes from feat/sheet-identity

### New fields on existing models

| Model | New field | Type | Default |
|---|---|---|---|
| `PieceRecord` | `label` | `str \| None` | `None` |
| `PieceRecord` | `sheet_origin` | `tuple[int, int]` | `(0, 0)` |
| `SheetRecord` | `metadata` | `SheetMetadata \| None` | `None` |
| `Piece` | `label` | `str \| None` | `None` |
| `Piece` | `sheet_origin` | `tuple[int, int]` | `(0, 0)` |
| `Piece` | `centroid_in_sheet` (property) | `tuple[int, int]` | - |
| `Sheet` | `metadata` | `SheetMetadata \| None` | `None` |
| `Sheet` | `slot_grid` | `SlotGrid \| None` | `None` |
| `Sheet` | `crop_offset` | `int` | `0` |

### New modules (no UI/API impact, listed for context)

- `src/snap_fit/aruco/sheet_metadata.py` - SheetMetadata, QRChunkHandler, SheetMetadataEncoder/Decoder
- `src/snap_fit/aruco/slot_grid.py` - SlotGrid
- `src/snap_fit/aruco/board_image_composer.py` - BoardImageComposer
- `src/snap_fit/config/aruco/metadata_zone_config.py` - MetadataZoneConfig, SlotGridConfig
- `src/snap_fit/utils/basemodel_kwargs.py` - BaseModelKwargs (moved from data_models)

---

## Misalignment analysis

### M1: Template uses `piece.piece_id.piece_idx` but field is `piece_id.piece_id`

**File**: `webapp_resources/templates/piece_detail.html` line 18
**Problem**: The template accesses `{{ piece.piece_id.piece_idx }}` but the
`PieceId` model defines the field as `piece_id` (not `piece_idx`).
**Fix**: Change template to `{{ piece.piece_id.piece_id }}`.

---

### M2: `matches.html` checks `match.similarity_manual is not none` but the property never returns None

**File**: `webapp_resources/templates/matches.html` lines 43-44
**Problem**: `MatchResult.similarity_manual` is a `@property` that always
returns a float (falls back to `self.similarity` when the override is
`None`). The raw field is `similarity_manual_` (with underscore). The
Jinja2 `is not none` check will always be `True`, so the column always
shows a value even when no manual override exists.
**Fix**: Change to `match.similarity_manual_ is not none` (check the raw
field). This also matches how Pydantic serializes the alias.

---

### M3: New `PieceRecord.label` not shown anywhere in the UI

**Files affected**:
- `webapp_resources/templates/pieces.html` - piece list table
- `webapp_resources/templates/piece_detail.html` - piece detail view
- `webapp_resources/templates/sheet_detail.html` - sheet detail pieces table

**Problem**: `PieceRecord` now has a `label` field (e.g. "A1") assigned
by the slot grid during ingestion. The templates do not display it.
**Fix**: Add a "Label" column/field to each template.

---

### M4: New `SheetRecord.metadata` not shown in sheets UI

**Files affected**:
- `webapp_resources/templates/sheets.html` - sheets list table
- `webapp_resources/templates/sheet_detail.html` - sheet detail view

**Problem**: `SheetRecord` now has a `metadata: SheetMetadata | None` field
with `tag_name`, `sheet_index`, `total_sheets`, `board_config_id`,
`printed_at`. The templates do not display any of this.
**Fix**: Add metadata info to sheet_detail. Optionally show `tag_name` in the
sheets list.

---

### M5: New `PieceRecord.sheet_origin` not shown in the UI

**File**: `webapp_resources/templates/piece_detail.html`
**Problem**: `PieceRecord` now has `sheet_origin: tuple[int, int]` (origin of
the piece's padded region in cropped-sheet coordinates). Not shown.
**Fix**: Add to piece detail view alongside `contour_region`.

---

### M6: SQLite store does not persist `PieceRecord.label` or `PieceRecord.sheet_origin`

**File**: `src/snap_fit/persistence/sqlite_store.py`
**Problem**: The `pieces` table DDL has no `label` or `sheet_origin` columns.
`_piece_to_row()` and `_row_to_piece()` ignore these fields. After ingestion
the `PieceRecord` objects have label/sheet_origin populated, and
`save_metadata_db()` calls `store.save_pieces()`, but the data is silently
dropped during row conversion.
**Fix**: Add `label TEXT` and `sheet_origin TEXT` columns to the `pieces` DDL.
Update `_piece_to_row()` to include them. Update `_row_to_piece()` to read
them back.

---

### M7: SQLite store does not persist `SheetRecord.metadata`

**File**: `src/snap_fit/persistence/sqlite_store.py`
**Problem**: The `sheets` table has no `metadata` column. `_sheet_to_row()` and
`_row_to_sheet()` ignore the `metadata` field. After ingestion the
`SheetRecord` may carry a `SheetMetadata`, but it is silently dropped.
**Fix**: Add `metadata TEXT` column to the `sheets` DDL. Store it as JSON
(via `SheetMetadata.model_dump_json()`). Read it back via
`SheetMetadata.model_validate_json()`.

---

### M8: (Pre-existing) `edge_pos` renders as enum repr instead of readable value

**Files**: `matches.html`, `piece_detail.html`
**Problem**: `{{ match.seg_id1.edge_pos }}` renders the Python enum repr
(e.g. `<EdgePos.TOP: 'top'>`) instead of just `"TOP"`. Same for
`segment_shapes` and `flat_edges` in piece templates - those already use
`.value` strings because `PieceRecord.from_piece()` serializes them. But
`SegmentId.edge_pos` is the raw `EdgePos` enum.
**Impact**: Only visible when matches are rendered from deserialized
`MatchResult` objects in templates. If Pydantic serializes `edge_pos` as a
string the display may be fine, but if the raw enum object reaches Jinja2
the repr is ugly. Verify at runtime - may already be OK if Pydantic model
serialization in FastAPI response converts it.
**Fix (if needed)**: Use `{{ match.seg_id1.edge_pos.value }}` in templates.

---

## Plan

### Phase 1: Fix data loss in persistence layer (critical)

1. **M6** - Add `label` and `sheet_origin` columns to SQLite `pieces` table.
   Update `_piece_to_row()` and `_row_to_piece()` in `sqlite_store.py`.
2. **M7** - Add `metadata` column to SQLite `sheets` table. Update
   `_sheet_to_row()` and `_row_to_sheet()` in `sqlite_store.py`.
3. Re-ingest a dataset (`uv run uvicorn ... --reload` then POST
   `/api/v1/pieces/ingest`) to populate new columns.
4. Verify with `sqlite3 cache/oca/dataset.db "SELECT label, sheet_origin
   FROM pieces LIMIT 5"` and `... "SELECT metadata FROM sheets LIMIT 1"`.

### Phase 2: Fix template bugs

5. **M1** - Fix `piece_detail.html`: `piece_id.piece_idx` -> `piece_id.piece_id`.
6. **M2** - Fix `matches.html`: `match.similarity_manual` -> `match.similarity_manual_`
   in the `is not none` guard.
7. **M8** - Verify edge_pos rendering at runtime. If ugly, add `.value` in
   `matches.html` and `piece_detail.html`.

### Phase 3: Show new fields in templates

8. **M3** - Add "Label" column to `pieces.html`, `piece_detail.html`, and
   `sheet_detail.html`.
9. **M4** - Add metadata section to `sheet_detail.html`. Optionally add
   `tag_name` column to `sheets.html`.
10. **M5** - Add `sheet_origin` to `piece_detail.html` detail grid.

### Phase 4: Verify end-to-end

11. Run full verification:
    ```bash
    uv run pytest && uv run ruff check . && uv run pyright && uv run pre-commit run --all-files
    ```
12. Start dev server, ingest a dataset, browse all pages. Confirm:
    - Pieces show labels (e.g. "A1")
    - Sheet detail shows metadata (tag_name, sheet_index, printed_at)
    - Piece detail shows sheet_origin, no `piece_idx` error
    - Matches page shows manual override column correctly (dash when absent)
    - No enum repr leaking into templates
