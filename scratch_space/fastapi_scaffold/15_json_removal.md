# Step 5: Remove JSON persistence for metadata and matches

> Part of [10_ui_scaling.md](./10_ui_scaling.md) - SQLite migration plan
> Depends on: All previous steps complete and validated

---

## Starting point

After steps 1-4, the codebase is in a dual-state:

**Domain classes have both JSON and SQLite methods:**
- `SheetManager`: `save_metadata()` (JSON), `load_metadata()` (JSON), `save_metadata_db()` (SQLite), `load_metadata_db()` (SQLite)
- `PieceMatcher`: `save_matches_json()` (JSON), `load_matches_json()` (JSON), `save_matches_db()` (SQLite), `load_matches_db()` (SQLite)

**Services use SQLite exclusively** (step 3):
- `PieceService` reads from `dataset.db` via `DatasetStore`
- `PuzzleService` queries `dataset.db` via `DatasetStore`

**Ingest dual-writes** (step 3):
- `PieceService.ingest_sheets()` writes both `metadata.json` and `dataset.db`

**Cache directory has both formats:**
```
cache/oca/
  metadata.json     <- still present, no longer read by services
  matches.json      <- still present, no longer read by services
  dataset.db        <- primary source for all reads
  contours/         <- unchanged
```

**Notebooks** may still reference JSON methods (need audit).

---

## What changes

### 1. Audit all JSON method callers

Before removing anything, identify every call site for the JSON methods:

**`SheetManager.save_metadata()` callers:**
- `PieceService.ingest_sheets()` - already dual-writes, remove JSON call
- `scratch_space/fastapi_scaffold/01_db_ingestion.ipynb` - update to SQLite
- `scratch_space/contour_/02_match_debug.ipynb` - update to SQLite (if it calls this)
- Any other notebooks in `scratch_space/` - check via grep

**`SheetManager.load_metadata()` callers:**
- Previously used by `PieceService` read methods - already migrated to SQLite in step 3
- Notebook cells that load metadata for analysis
- Test fixtures in `tests/puzzle/test_sheet_manager.py`

**`PieceMatcher.save_matches_json()` callers:**
- Notebooks that run matching and persist results
- No service code calls this (matching is offline)

**`PieceMatcher.load_matches_json()` callers:**
- Previously used by `PuzzleService` - already migrated to SQLite in step 3
- Notebooks that load matches for visualization

Grep commands to run:
```
grep -rn "save_metadata(" src/ tests/ scratch_space/ --include="*.py" --include="*.ipynb"
grep -rn "load_metadata(" src/ tests/ scratch_space/ --include="*.py" --include="*.ipynb"
grep -rn "save_matches_json(" src/ tests/ scratch_space/ --include="*.py" --include="*.ipynb"
grep -rn "load_matches_json(" src/ tests/ scratch_space/ --include="*.py" --include="*.ipynb"
```

### 2. Update PieceService.ingest_sheets() - remove JSON write

Remove the `manager.save_metadata(tag_dir / "metadata.json")` line. Keep only `manager.save_metadata_db(tag_dir / "dataset.db")`.

The contour cache write stays: `manager.save_contour_cache(tag_dir / "contours")`.

### 3. Remove JSON methods from SheetManager

Remove these methods from `src/snap_fit/puzzle/sheet_manager.py`:
- `save_metadata(path, data_root)` - replaced by `save_metadata_db()`
- `load_metadata(path)` [static] - replaced by `load_metadata_db()`
- `to_records(data_root)` - only used by `save_metadata()` and `ingest_sheets()` return value

Wait - `to_records()` is also used by `PieceService.ingest_sheets()` to build the response dict:
```python
records = manager.to_records()
return {"sheets_tag": ..., "sheets_ingested": len(records["sheets"]), ...}
```

This needs a replacement. Options:
- Keep `to_records()` but only for the response-building purpose
- Inline the count logic: `len(manager.sheets)` for sheet count, `sum(len(s.pieces) for s in manager.sheets.values())` for piece count
- Use the `_to_record_objects()` helper introduced in step 2

Decision: inline the counts directly. `to_records()` was a heavy operation (serializes every sheet and piece) just to count them.

### 4. Remove JSON methods from PieceMatcher

Remove these methods from `src/snap_fit/puzzle/piece_matcher.py`:
- `save_matches_json(path)` - replaced by `save_matches_db()`
- `load_matches_json(path)` - replaced by `load_matches_db()`

Keep:
- `save_matches_db()` / `load_matches_db()`
- `match_pair()`, `match_all()`, `match_incremental()`, `get_matched_pair_keys()`, `clear()`
- `get_top_matches()`, `get_matches_for_piece()`, `get_cached_score()`
- `results` property

### 5. Update tests

**`tests/puzzle/test_sheet_manager.py`:**
- Remove tests for `save_metadata()`, `load_metadata()`, `to_records()` JSON methods
- Or better: rename them to test the SQLite equivalents if they are not already covered by step 2's tests
- Keep tests for `save_contour_cache()`, `load_contour_for_piece()` (binary, unchanged)

**`tests/puzzle/test_piece_matcher.py`:**
- Remove tests for `save_matches_json()`, `load_matches_json()`
- Or rename to SQLite equivalents

**`tests/webapp/test_routes.py`:**
- Update test setup to create `.db` files instead of `.json` files (if tests create mock data)
- Alternatively, the tests may use the ingest endpoint which now writes `.db` only

### 6. Update notebooks

Any notebook cell that calls `save_metadata()`, `load_metadata()`, `save_matches_json()`, or `load_matches_json()` must switch to the SQLite equivalents.

Common pattern replacement in notebooks:
```python
# Before:
manager.save_metadata(output_dir / "metadata.json")
matcher.save_matches_json(output_dir / "matches.json")

# After:
manager.save_metadata_db(output_dir / "dataset.db")
matcher.save_matches_db(output_dir / "dataset.db")
```

Note: both SheetManager and PieceMatcher write to the _same_ `dataset.db` file (different tables). This is a change from having separate `metadata.json` and `matches.json`.

### 7. Delete stale JSON files from cache

After all code is migrated and tests pass, delete:
- `cache/oca/metadata.json`
- `cache/oca/matches.json`
- Any other `metadata.json` / `matches.json` in tag subdirectories

This is a manual cleanup step. The notebook should list which files can be removed.

### 8. Remove json import where no longer needed

After removing JSON methods, `SheetManager` may no longer need `import json` at the top (unless `save_contour_cache` still uses it for corners JSON - it does, so keep it). `PieceMatcher` can drop `import json` entirely.

---

## Expected outcome

**Final state of SheetManager persistence methods:**
- `save_metadata_db(db_path, data_root)` - write sheets + pieces to SQLite
- `load_metadata_db(db_path)` [static] - read back from SQLite
- `save_contour_cache(cache_dir)` - write `.npz` + `_corners.json` (unchanged)
- `load_contour_for_piece(piece_id, cache_dir)` [static] - read contour data (unchanged)

**Final state of PieceMatcher persistence methods:**
- `save_matches_db(db_path)` - write matches to SQLite
- `load_matches_db(db_path)` - read matches from SQLite

**Final cache directory structure:**
```
cache/
  {sheets_tag}/
    dataset.db             <- single source of truth for metadata + matches
    contours/
      {sheet_id}_contours.npz
      {sheet_id}_corners.json
```

No `.json` files for metadata or matches. Contour binary files remain as-is.

---

## Validation

### Full verification suite

```bash
uv run pytest && uv run ruff check . && uv run pyright
```

All three must pass cleanly.

### Webapp end-to-end walkthrough

1. Start dev server: `uv run uvicorn snap_fit.webapp.main:app --reload`
2. Ingest a dataset: POST `/api/v1/pieces/ingest` with `{"sheets_tag": "oca"}`
   - Verify: response shows correct sheet/piece counts
   - Verify: `cache/oca/dataset.db` is created (no `metadata.json`)
3. Browse `/sheets` - all sheets present
4. Browse `/pieces/{piece_id}` - piece detail with matches
5. Browse `/matches` - match table populated
6. Browse `/` - dashboard stats correct

### Notebook round-trip

Final notebook cell verifying the full pipeline:
1. Load dataset via SheetManager + ArUco config
2. Run `PieceMatcher.match_all()`
3. Save via `save_metadata_db()` + `save_matches_db()`
4. Load via `load_metadata_db()` + `load_matches_db()`
5. Query via `DatasetStore.query_matches_for_piece()`
6. All results verified

### Grep for stale references

After all changes:
```bash
grep -rn "metadata\.json\|matches\.json" src/ tests/ --include="*.py"
```

Should return zero hits in `src/` and `tests/` (only allowed in `scratch_space/` docs or comments).

```bash
grep -rn "save_metadata\b\|load_metadata\b" src/ tests/ --include="*.py"
```

Should only find `save_metadata_db` / `load_metadata_db` references (the `_db` variants).

```bash
grep -rn "save_matches_json\|load_matches_json" src/ tests/ --include="*.py"
```

Should return zero hits.

---

## Risk assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Removing a method that is still called somewhere | Medium | Grep audit before removing (step 1 of this plan) |
| Notebook cells break silently | Medium | Run each notebook end-to-end after migration |
| `to_records()` removal breaks ingest response | Low | Replace with inline counts |
| Test fixtures assume JSON format | Medium | Update fixtures as part of test changes |
| Someone manually reads `metadata.json` outside the codebase | Low | Document the change in a commit message |
