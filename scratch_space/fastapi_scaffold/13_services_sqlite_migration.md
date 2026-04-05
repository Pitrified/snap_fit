# Step 3: Migrate services layer to use SQLite

> Part of [10_ui_scaling.md](./10_ui_scaling.md) - SQLite migration plan
> Depends on: [Step 2](./12_domain_sqlite_methods.md) (SheetManager/PieceMatcher have SQLite methods)

---

## Starting point

The webapp services read JSON files on every request with no caching:

**PieceService** (`src/snap_fit/webapp/services/piece_service.py`):
- `__init__(cache_dir)` stores the root cache directory
- `_all_tag_dirs()` returns all subdirectories of `cache_dir`
- Every `list_*` / `get_*` method loops over `_all_tag_dirs()`, checks for `metadata.json`, calls `SheetManager.load_metadata(meta)` (reads full JSON file), then validates each record with `model_validate()`
- `ingest_sheets(sheets_tag, data_dir)` writes `metadata.json` + contours via `SheetManager.save_metadata()` + `save_contour_cache()`

**PuzzleService** (`src/snap_fit/webapp/services/puzzle_service.py`):
- `__init__(cache_dir)` stores the root cache directory
- `_all_matches_paths()` returns all `matches.json` files found under tag subdirectories
- Every method instantiates a throwaway `PieceMatcher(manager=None)` and calls `load_matches_json()` to load the full file, then filters in Python
- `match_count()` loads _every_ matches file just to count results

**Performance cost at scale:**
- 6 sheets, 240 matches (OCA) - works fine
- 1,500 pieces, 4.5M matches - every page load reads 500MB+ of JSON, parses it, then discards most of it

**Routers** (`src/snap_fit/webapp/routers/`):
- `piece_ingestion.py` creates `PieceService(settings.cache_path)` per request via `Depends`
- `puzzle_solve.py` creates `PuzzleService(settings.cache_path)` per request via `Depends`
- `ui.py` creates both services per request for rendering templates

---

## What changes

### PieceService: switch reads to DatasetStore, dual-write on ingest

**Helper changes:**

- `_all_tag_dirs()` stays but detection changes: look for `dataset.db` (primary) with `metadata.json` as fallback during transition.
- Add `_db_path(tag_dir)` helper: returns `tag_dir / "dataset.db"`.
- Add `_all_db_paths()` helper: returns all `dataset.db` files across tag directories.

**Read methods - rewrite to use DatasetStore:**

`list_sheets()`:
- Before: loop tag dirs, read `metadata.json`, `model_validate` each raw dict
- After: loop tag dirs, open `DatasetStore(db_path)`, call `store.load_sheets()`, extend results
- The store already returns `list[SheetRecord]` - no `model_validate` needed

`list_pieces()`:
- Same pattern: `store.load_pieces()` returns `list[PieceRecord]`

`get_sheet(sheet_id)`:
- Before: loop all tag dirs, load full `metadata.json`, scan all sheets until match
- After: loop all tag dirs, call `store.load_sheet(sheet_id)`, return first hit
- `DatasetStore.load_sheet()` uses `WHERE sheet_id = ?` - O(1) lookup

`get_piece(piece_id)`:
- Before: loop all tag dirs, load full metadata, scan all pieces until string match
- After: loop all tag dirs, call `store.load_piece(piece_id)`, return first hit

`get_pieces_for_sheet(sheet_id)`:
- Before: calls `list_pieces()` (loads ALL pieces from ALL datasets) then filters by sheet_id
- After: loop all tag dirs, call `store.load_pieces_for_sheet(sheet_id)`, return first non-empty result

**Write method - dual write:**

`ingest_sheets(sheets_tag, data_dir)`:
- Keep existing: `manager.save_metadata(tag_dir / "metadata.json")` for backward compatibility during transition
- Add: `manager.save_metadata_db(tag_dir / "dataset.db")` to also write SQLite
- `manager.save_contour_cache(tag_dir / "contours")` unchanged

### PuzzleService: switch to DatasetStore queries

**Helper changes:**

- Remove `_all_matches_paths()` (was looking for `matches.json`)
- Add `_all_db_paths()` helper: same as PieceService's - find all `dataset.db` under tag directories

**Read methods - rewrite to use DatasetStore:**

`list_matches(limit, min_similarity)`:
- Before: loop matches.json files, create throwaway PieceMatcher for each, load full file, extend results list, filter in Python, sort, slice
- After: loop db files, call `store.load_matches(limit, min_similarity)` which does `WHERE + ORDER BY + LIMIT` in SQL, merge results, re-sort top-level, slice
- Significant performance gain: SQL does the filtering and sorting at the storage level

`get_matches_for_piece(piece_id, limit)`:
- Before: load all matches, filter by string comparison on piece_id
- After: `store.query_matches_for_piece(piece_id, limit)` - indexed lookup

`get_matches_for_segment(piece_id, edge_pos, limit)`:
- Before: load all matches, double-check both seg_id1 and seg_id2 with string/enum comparisons
- After: `store.query_matches_for_segment(piece_id, edge_pos, limit)` - indexed lookup

`match_count()`:
- Before: load every matches.json, count len(results)
- After: `store.match_count()` - `SELECT COUNT(*)`, near-instant

`solve_puzzle(...)`:
- No change (still a stub)

### PuzzleService no longer imports PieceMatcher

After this change, `PuzzleService` does not need to instantiate throwaway `PieceMatcher(manager=None)` objects. It only imports `DatasetStore` and `MatchResult`. This is a cleaner dependency graph.

### Routers and schemas: no changes

The routers create services via `Depends` and pass through to the same service method signatures. No router or schema changes needed. The FastAPI response serialization stays the same because the services return the same Pydantic model types.

### UI router: no changes

The UI router (`ui.py`) calls the services to get data for Jinja2 templates. Since the service methods return the same types, templates render identically.

---

## Expected outcome

- All webapp queries go through SQLite with indexed lookups.
- Ingest writes to both JSON and SQLite (dual-write for transition safety).
- Existing test suite passes - responses are identical.
- The per-request performance for match queries is dramatically better (SQL filtering vs full JSON parse).
- `PuzzleService` drops its dependency on `PieceMatcher` for read operations.

---

## Validation

### Existing test suite

**`tests/webapp/test_routes.py`** must continue passing. These smoke tests hit the API endpoints via `TestClient` and verify response shapes. If they were hardcoded to expect specific data, the migration script (step 4) must run first to populate `.db` files. Otherwise, ensure the test setup creates test data in the expected format.

Run: `uv run pytest tests/webapp/`

### Manual webapp walkthrough

Start the dev server and verify each page works:

1. `uv run uvicorn snap_fit.webapp.main:app --reload`
2. Browse `/` - dashboard loads, stats cards show correct counts
3. Browse `/sheets` - all sheets listed (same as before migration)
4. Browse `/sheets/{sheet_id}` - sheet detail with pieces table
5. Browse `/pieces` - all pieces listed
6. Browse `/pieces/{piece_id}` - piece detail with top 20 matches
7. Browse `/matches` - paginated match table, sorted by similarity ascending

### API endpoint spot-checks

Use curl or the Swagger UI at `/docs`:

```
GET /api/v1/pieces/sheets       -> verify sheet count matches JSON-era count
GET /api/v1/puzzle/matches/count -> verify total match count
GET /api/v1/puzzle/matches?limit=5 -> verify top 5 matches are same values
GET /api/v1/puzzle/matches/piece/{id}?limit=3 -> verify piece-specific matches
```

### Scratch notebook cell

A notebook cell that:

1. Instantiates `PieceService(cache_dir)` and `PuzzleService(cache_dir)` directly (no FastAPI)
2. Calls `list_sheets()`, `list_pieces()`, `list_matches(limit=10)`, `match_count()`
3. Compares results to baseline values captured before the migration (or to direct JSON loads)
4. Times the calls and confirms they complete in reasonable time

### Performance comparison (informational)

Optional but useful: time the `match_count()` call before and after migration.

- Before: `PuzzleService.match_count()` reads every `matches.json` file
- After: `SELECT COUNT(*) FROM matches` per db file

The difference should be dramatic even at 240 matches, and will be essential at 4.5M.

---

## Migration safety

This step introduces **dual-write** on ingest and **SQLite-first reads**. During the transition:

- Old datasets that only have `metadata.json` / `matches.json` (no `dataset.db`) will not appear in the new service queries.
- Step 4 (migration script) addresses this by converting existing JSON cache to SQLite.
- As a fallback, the `_all_tag_dirs()` helper could fall back to JSON if no `.db` is found. Decision: do NOT add a JSON fallback in the services - it defeats the purpose and complicates the code. Instead, run step 4 before deploying step 3 in production, or accept that un-migrated datasets are temporarily invisible.

Recommended execution order: run the migration script (step 4) first on existing data, then deploy the service changes (step 3). The plan numbering is logical (design before migration), but execution can be reordered.

---

## Files touched

| File | Change type |
|------|------------|
| `src/snap_fit/webapp/services/piece_service.py` | Rewrite read methods, add dual-write |
| `src/snap_fit/webapp/services/puzzle_service.py` | Rewrite read methods, drop PieceMatcher dependency |
| `src/snap_fit/webapp/routers/piece_ingestion.py` | No change |
| `src/snap_fit/webapp/routers/puzzle_solve.py` | No change |
| `src/snap_fit/webapp/routers/ui.py` | No change |
| `src/snap_fit/webapp/schemas/` | No change |
| `tests/webapp/test_routes.py` | May need test data setup update |
