# Scale up storage - SQLite migration for metadata and matches

## 1. Current state (updated Apr 6 2026)

### What we have

The persistence layer is now SQLite-backed for new ingestions. The `oca` dataset cache
still holds legacy JSON files alongside; running the Phase 6 notebook cells creates
`dataset.db` and makes the webapp fully live.

```
cache/
  metadata.json          <- stale root-level leftover (NOT used by webapp)
  matches.json           <- stale root-level leftover (NOT used by webapp)
  contours/              <- stale root-level leftover (NOT used by webapp)
  oca/
    metadata.json        <- kept during transition (removed in step 5)
    matches.json         <- kept during transition (removed in step 5)
    dataset.db           <- created by Phase 6 migration cells
    contours/
      {sheet_id}_contours.npz   <- compressed numpy arrays
      {sheet_id}_corners.json   <- corner indices per piece
```

Contour binary storage (.npz + corners JSON) is efficient and does not need to change.

### What works

- `src/snap_fit/persistence/sqlite_store.py` - `DatasetStore` class with full schema, row conversion, indexed queries. **DONE (Step 1)**
- `SheetManager.save_metadata_db()` / `load_metadata_db()` and `PieceMatcher.save_matches_db()` / `load_matches_db()` - SQLite round-trip methods. **DONE (Step 2)**
- `PieceService` reads from `dataset.db` via `DatasetStore`; `ingest_sheets()` dual-writes JSON + SQLite. **DONE (Step 3)**
- `PuzzleService` reads from `dataset.db` via `DatasetStore`; no longer imports `PieceMatcher`. **DONE (Step 3)**
- All 252 unit tests pass; ruff clean; pyright 0 errors. **DONE (Step 3)**
- Webapp UI renders sheets, pieces, and matches from SQLite where `dataset.db` exists.
- Phase 6 notebook cells in `01_db_ingestion.ipynb` ready to migrate the `oca` dataset. **DONE (Step 4 - notebook prepared)**

### What breaks at scale

- **Every API call re-reads JSON from disk.** `PuzzleService` instantiates a throwaway `PieceMatcher(manager=None)` and calls `load_matches_json()` on every single request. Same for `PieceService` re-reading `metadata.json` every time.
- **No indexing.** Querying matches for one piece requires loading the entire matches file and linear-scanning in Python.
- **Full-puzzle match files will be huge.** 1,500 pieces produce ~4.5M match pairs. A single `matches.json` at that scale would be 500 MB-1 GB of JSON - unacceptable for per-request reads.
- **No cross-dataset querying.** The service loops over tag directories and merges results in Python; there is no unified query surface.
- **Flat file root pollution.** `cache/metadata.json` and `cache/matches.json` still exist alongside `cache/oca/` as leftover artifacts from earlier code; only the tagged subdirectories are used by the webapp.

### Recap of past plans

- `01_ingestion_db.md` evaluated JSON vs SQLite vs PostgreSQL, decided on **SQLite for matches + JSON for metadata** (hybrid approach).
- `02_ingestion_configs.md` migrated ingestion to the ArUco-based loader pattern and propagated `sheets_tag` into cache paths (done).
- `03_snap_fit_analysis.md` documented the full architecture at the current commit - confirmed no SQLite code exists yet, that services reload from disk on every call, and that match queries do linear scans.

The decision to use SQLite for matches was made but never implemented. This plan extends the scope: **move both metadata and matches into a single SQLite database per dataset tag**, replacing the JSON files entirely (contour .npz files stay as-is).

---

## 2. Plan overview

The migration follows five steps. Each step produces a testable checkpoint - validate via both a scratch notebook and the webapp UI before moving to the next.

### Step 1: Add the SQLite persistence module -> [detailed plan](./11_sqlite_persistence_module.md) ✅ DONE

**Starting point:** No database code exists anywhere in the project. `sqlite3` is a Python stdlib module (no new dependencies needed).

**What was built:**
- `src/snap_fit/persistence/sqlite_store.py` - `DatasetStore` class with `sheets`, `pieces`, `matches` tables, row conversion helpers, context manager support, indexed queries.
- `tests/persistence/test_sqlite_store.py` - full unit test coverage.

**Validation passed:** All round-trip tests pass, including `similarity_manual_` alias handling.

### Step 2: Add save/load SQLite methods to SheetManager and PieceMatcher -> [detailed plan](./12_domain_sqlite_methods.md) ✅ DONE

**Starting point:** `SheetManager` has `save_metadata()` / `load_metadata()` (JSON). `PieceMatcher` has `save_matches_json()` / `load_matches_json()` (JSON).

**What was built:**
- `SheetManager._to_record_objects()`, `save_metadata_db(db_path, data_root)`, `load_metadata_db(db_path)` added.
- `PieceMatcher.save_matches_db(db_path)`, `load_matches_db(db_path)` added.
- JSON methods kept in place during the transition.

**Validation passed:** All tests pass; JSON methods untouched.

### Step 3: Migrate the services layer to use SQLite -> [detailed plan](./13_services_sqlite_migration.md) ✅ DONE

**Starting point:** `PieceService` and `PuzzleService` read JSON files on every call, instantiate throwaway `PieceMatcher` objects, and aggregate by looping over tag directories.

**What changed:**
- `PieceService`: added `_db_path()` helper; rewrote `list_sheets()`, `list_pieces()`, `get_sheet()`, `get_piece()`, `get_pieces_for_sheet()` to use `DatasetStore`; `ingest_sheets()` now dual-writes `metadata.json` + `dataset.db`.
- `PuzzleService`: replaced `_all_matches_paths()` with `_all_db_paths()`; rewrote `list_matches()`, `get_matches_for_piece()`, `get_matches_for_segment()`, `match_count()` to use `DatasetStore`; removed `PieceMatcher` import.
- `tests/webapp/test_routes.py`: `TestWithCachedData.test_pieces_with_mock_data` now creates a `dataset.db` via `DatasetStore` instead of writing `metadata.json`.

**Validation passed:** `uv run pytest` (252/252), `uv run ruff check .` (clean), `uv run pyright` (0 errors).

### Step 4: Write a one-shot migration script for existing cache data -> [detailed plan](./14_cache_data_migration.md) ✅ NOTEBOOK PREPARED

**Starting point:** Existing datasets live in `cache/{tag}/metadata.json` + `cache/{tag}/matches.json`. No `.db` files exist yet.

**What was built:**
- Phase 6 cells added to `scratch_space/fastapi_scaffold/01_db_ingestion.ipynb` (sections 6.1-6.10).
- Cells load JSON records, write to `cache/oca/dataset.db`, then assert record counts, field spot-checks, top-5 similarity checks, and a per-piece query test.
- Final cell lists the stale root-level files with removal instructions.

**To execute:** run Phase 6 cells in `01_db_ingestion.ipynb`.

**After running:** delete stale root-level files (`cache/metadata.json`, `cache/matches.json`, `cache/contours/`) as instructed by cell 6.10.

**Validation (in notebook):** record counts match JSON originals; similarity spot-checks pass; `query_matches_for_piece` returns results; `match_count() == 240`.

### Step 5: Remove JSON persistence for metadata and matches -> [detailed plan](./15_json_removal.md)

**Starting point:** Both JSON and SQLite paths coexist. Services already read from SQLite (step 3). JSON files still exist on disk and the old save/load methods still exist in code.

**What changes:**
- Remove `SheetManager.save_metadata()` / `load_metadata()` JSON methods (or mark deprecated if other offline scripts still use them - check notebook usage, plan migration to new SQLite methods).
- Remove `PieceMatcher.save_matches_json()` / `load_matches_json()` JSON methods (same caveat).
- Update `PieceService.ingest_sheets()` to stop writing `metadata.json` (only writes `.db` now).
- Update any notebook cells (e.g. `01_db_ingestion.ipynb`, `02_match_debug.ipynb`) that still call the JSON methods to use the SQLite equivalents.
- Optionally delete the old `.json` files from `cache/{tag}/` once all consumers are migrated.
- Contour `.npz` and `_corners.json` files remain unchanged - they serve a different purpose (binary geometry data, not queryable metadata).

**Expected outcome:** The JSON persistence code path is fully removed. SQLite is the single source of truth for metadata and matches. Contour cache stays binary.

**Validation:**
- `uv run pytest` - all tests pass.
- `uv run ruff check .` - no lint errors.
- `uv run pyright` - no type errors.
- Webapp: full walkthrough of ingest a dataset (POST /ingest), browse sheets, browse pieces, view matches, view piece detail with top matches.
- Scratch notebook: full round-trip from ingestion through matching through querying.

---

## 3. New cache structure (target state)

```
cache/
  {sheets_tag}/
    dataset.db             <- SQLite: sheets, pieces, matches tables
    contours/
      {sheet_id}_contours.npz
      {sheet_id}_corners.json
```

### SQLite schema (sketch)

**sheets**
| Column     | Type    | Notes                      |
|------------|---------|----------------------------|
| sheet_id   | TEXT PK |                            |
| img_path   | TEXT    | relative to data root      |
| piece_count| INTEGER |                            |
| threshold  | INTEGER | default 130                |
| min_area   | INTEGER | default 80000              |
| created_at | TEXT    | ISO 8601                   |

**pieces**
| Column              | Type    | Notes                                |
|---------------------|---------|--------------------------------------|
| piece_id            | TEXT PK | composite: sheet_id:piece_idx        |
| sheet_id            | TEXT FK | references sheets.sheet_id           |
| corners             | TEXT    | JSON dict                            |
| segment_shapes      | TEXT    | JSON dict                            |
| oriented_piece_type | TEXT    | nullable                             |
| flat_edges          | TEXT    | JSON list                            |
| contour_point_count | INTEGER |                                      |
| contour_region      | TEXT    | JSON tuple                           |

**matches**
| Column              | Type    | Notes                                |
|---------------------|---------|--------------------------------------|
| id                  | INTEGER PK AUTOINCREMENT |                     |
| seg_id1_sheet_id    | TEXT    |                                      |
| seg_id1_piece_idx   | INTEGER |                                      |
| seg_id1_edge_pos    | TEXT    |                                      |
| seg_id2_sheet_id    | TEXT    |                                      |
| seg_id2_piece_idx   | INTEGER |                                      |
| seg_id2_edge_pos    | TEXT    |                                      |
| similarity          | REAL    | indexed                              |
| similarity_manual   | REAL    | nullable                             |

**Indexes on matches:** `(seg_id1_sheet_id, seg_id1_piece_idx)`, `(seg_id2_sheet_id, seg_id2_piece_idx)`, `(similarity)`.

---

## 4. Validation checklist

After full migration, confirm all of these:

| Check | How | Pass criteria |
|-------|-----|---------------|
| Unit tests | `uv run pytest` | All green |
| Lint | `uv run ruff check .` | No errors |
| Types | `uv run pyright` | No errors |
| Ingest via API | POST `/api/v1/pieces/ingest` with `{"sheets_tag": "oca"}` | Returns success, `dataset.db` created |
| Sheets list (UI) | Browse `/sheets` | All sheets shown |
| Piece detail (UI) | Browse `/pieces/{id}` | Piece metadata + top matches shown |
| Matches list (UI) | Browse `/matches` | Paginated match table, correct sort |
| Match count (API) | GET `/api/v1/puzzle/matches/count` | Returns correct total |
| Notebook round-trip | Load DatasetStore, query sheets/pieces/matches | Results match original JSON data |
| Performance | Time a `list_matches(limit=100)` call with large dataset | Sub-second (vs multi-second with JSON at scale) |
| No JSON leftovers | `cache/{tag}/` contains only `dataset.db` + `contours/` | No `metadata.json` or `matches.json` |
