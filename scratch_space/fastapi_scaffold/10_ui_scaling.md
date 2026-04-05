# Scale up storage - SQLite migration for metadata and matches

## 1. Current state

### What we have

The persistence layer is fully JSON-based with per-dataset tag directories:

```
cache/
  {sheets_tag}/
    metadata.json      <- SheetRecord[] + PieceRecord[] (Pydantic -> JSON)
    matches.json       <- MatchResult[] (Pydantic -> JSON, sorted by similarity)
    contours/
      {sheet_id}_contours.npz   <- compressed numpy arrays
      {sheet_id}_corners.json   <- corner indices per piece
```

Contour binary storage (.npz + corners JSON) is efficient and does not need to change.

### What works

- `PieceService` aggregates metadata across all `cache/{tag}/metadata.json` files (list/get sheets and pieces).
- `PuzzleService` aggregates matches across all `cache/{tag}/matches.json` files (list/filter/count matches).
- `PieceMatcher` has `save_matches_json()` / `load_matches_json()` for round-tripping match data.
- `SheetManager` has `save_metadata()` / `load_metadata()` / `save_contour_cache()` for round-tripping sheet and piece data.
- The webapp UI (Jinja2 templates) renders sheets, pieces, and matches tables by calling the services above.
- The ingest endpoint (`POST /api/v1/pieces/ingest`) loads a dataset via ArUco config and persists metadata + contours.

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

### Step 1: Add the SQLite persistence module -> [detailed plan](./11_sqlite_persistence_module.md)

**Starting point:** No database code exists anywhere in the project. `sqlite3` is a Python stdlib module (no new dependencies needed).

**What changes:**
- Create a new module `src/snap_fit/persistence/sqlite_store.py` (or similar location TBD) that encapsulates all SQLite interaction.
- Define the schema: a `sheets` table (columns mirror `SheetRecord` fields), a `pieces` table (columns mirror `PieceRecord` fields, with `sheet_id` as FK), and a `matches` table (columns mirror `MatchResult` fields, with indexed columns for `seg_id1_piece_id`, `seg_id2_piece_id`, and `similarity`).
- Implement a `DatasetStore` class whose constructor takes a path to a `.db` file. Expose methods: `save_sheets()`, `save_pieces()`, `save_matches()`, `load_sheets()`, `load_pieces()`, `load_matches()`, `query_matches_for_piece()`, `query_matches_for_segment()`, `match_count()`.
- The store converts between Pydantic models and SQLite rows internally - callers never see raw SQL.

**Expected outcome:** A standalone module with no dependencies on the webapp or services layers. Can be tested in isolation.

**Validation:**
- Unit tests: round-trip `SheetRecord`, `PieceRecord`, and `MatchResult` objects through the store and assert equality.
- Scratch notebook cell: create a temporary `.db`, insert the OCA dataset's records, query them back, compare to JSON originals.

### Step 2: Add save/load SQLite methods to SheetManager and PieceMatcher -> [detailed plan](./12_domain_sqlite_methods.md)

**Starting point:** `SheetManager` has `save_metadata()` / `load_metadata()` (JSON). `PieceMatcher` has `save_matches_json()` / `load_matches_json()` (JSON).

**What changes:**
- Add `SheetManager.save_metadata_db(db_path, data_root)` and `SheetManager.load_metadata_db(db_path)` that delegate to `DatasetStore`.
- Add `PieceMatcher.save_matches_db(db_path)` and `PieceMatcher.load_matches_db(db_path)` that delegate to `DatasetStore`.
- The JSON methods stay in place (no removal yet) so existing workflows keep working during the transition.

**Expected outcome:** Both domain classes can persist to and reload from SQLite in addition to JSON.

**Validation:**
- Unit tests: round-trip through the new methods, compare results to JSON round-trip.
- Scratch notebook cell: load OCA via SheetManager, save to both JSON and SQLite, use `load_metadata_db()` and compare record-by-record.

### Step 3: Migrate the services layer to use SQLite -> [detailed plan](./13_services_sqlite_migration.md)

**Starting point:** `PieceService` and `PuzzleService` read JSON files on every call, instantiate throwaway `PieceMatcher` objects, and aggregate by looping over tag directories.

**What changes:**
- Update `PieceService.ingest_sheets()` to also (or instead) write a `{tag_dir}/dataset.db` file via `DatasetStore`, alongside (initially) the existing JSON files.
- Rewrite `PieceService.list_sheets()`, `list_pieces()`, `get_sheet()`, `get_piece()`, `get_pieces_for_sheet()` to open the `.db` file and query directly rather than loading full JSON into memory.
- Rewrite `PuzzleService.list_matches()`, `get_matches_for_piece()`, `get_matches_for_segment()`, `match_count()` to query the `.db` with SQL WHERE/LIMIT clauses. This eliminates the per-request full-file load and the Python-side linear scan.
- `_all_tag_dirs()` helper stays but now looks for `dataset.db` instead of (or in addition to) `metadata.json`.

**Expected outcome:** Services read from SQLite. The webapp endpoints return the same data as before but with O(log n) indexed lookups instead of O(n) full-file scans.

**Validation:**
- Existing webapp test suite passes (smoke tests in `tests/webapp/`).
- Start the dev server (`uv run uvicorn ...`), browse `/sheets`, `/pieces`, `/matches` in the UI - same data, no regressions.
- Scratch notebook cell: call `PieceService.list_pieces()` and `PuzzleService.list_matches()` and confirm results match the JSON-era output.

### Step 4: Write a one-shot migration script for existing cache data -> [detailed plan](./14_cache_data_migration.md)

**Starting point:** Existing datasets live in `cache/{tag}/metadata.json` + `cache/{tag}/matches.json`. No `.db` files exist yet.

**What changes:**
- Create a small migration script (or a management command / notebook cell) that, for each tag directory: reads `metadata.json` + `matches.json`, creates `dataset.db` via `DatasetStore`, and writes all records.
- Run the migration on the `oca` dataset (and any other existing datasets).
- After confirmed successful migration, remove the stale flat `cache/metadata.json` and `cache/matches.json` files at the root level (these were leftovers from before the tag-directory refactor and are not used by the webapp).

**Expected outcome:** Every `cache/{tag}/` directory now has a `dataset.db` alongside (temporarily) the old JSON files. The flat root-level JSON files are cleaned up.

**Validation:**
- Scratch notebook: load `dataset.db` and `metadata.json` side by side, assert record counts and field values match.
- Webapp UI: verify `/sheets`, `/pieces/{id}`, `/matches` all work identically.

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
