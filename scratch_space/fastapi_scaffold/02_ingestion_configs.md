# Handle configs for sheets set

in
`scratch_space/fastapi_scaffold/01_ingestion_db.md`
`scratch_space/fastapi_scaffold/01_db_ingestion.ipynb`
there are some implementation to load sheets and save in cache

but the pattern to set config is not the latest version
eg `Load new data` from
`scratch_space/contour_/02_match_debug.ipynb`

`data/oca` and `data/milano1` are the only two datasets following the latest pattern

please

1. update the code in `scratch_space/fastapi_scaffold/01_db_ingestion.ipynb` to follow the latest pattern
2. update the webapp ingestion endpoint to use the latest pattern
3. add a UI element in the webapp to trigger the ingestion of a new dataset, which will call the ingestion endpoint

USER UPDATE: cache folder has a flat structure, propagate the `sheets_tag` logic everywhere in the cache handling

### Task 4 — Propagate `sheets_tag` into cache paths

**Problem:** All datasets currently share a single `cache/metadata.json`, `cache/matches.json` and `cache/contours/` — datasets overwrite each other on ingest.

**Target structure:**

```
cache/
  {sheets_tag}/
    metadata.json
    matches.json
    contours/
```

**Files touched:**

- `src/snap_fit/webapp/services/piece_service.py`
- `src/snap_fit/webapp/services/puzzle_service.py`
- `scratch_space/fastapi_scaffold/01_db_ingestion.ipynb` (paths cell)

**Changes:**

`PieceService`:

- Remove flat `self.metadata_path` / `self.contour_cache_dir` instance attributes.
- Add `_tag_dir(sheets_tag) -> Path` helper returning `self.cache_dir / sheets_tag`.
- Add `_all_tag_dirs() -> list[Path]` helper returning all existing sub-directories of `self.cache_dir`.
- `ingest_sheets`: write metadata and contours into `_tag_dir(sheets_tag)`.
- `list_sheets` / `list_pieces`: iterate `_all_tag_dirs()` and aggregate.
- `get_piece` / `get_sheet` / `get_pieces_for_sheet`: iterate `_all_tag_dirs()` until found.

`PuzzleService`:

- Remove flat `self.matches_path` instance attribute.
- Add `_all_matches_paths() -> list[Path]` helper returning all `{tag}/matches.json` files found under `self.cache_dir`.
- `list_matches`, `get_matches_for_piece`, `get_matches_for_segment`, `match_count`: load and aggregate across all discovered matches files.
- `ingest_sheets` in `PieceService` also writes `cache/{tag}/matches.json` after running matching (currently the notebook does this manually — the service should mirror the same pattern for completeness; but since the service does not run matching, leave `matches.json` as the concern of a future matcher step and only scope metadata + contours here).

`Notebook`:

- Change `OUTPUT_DIR` from `snap_fit_paths.cache_fol` → `snap_fit_paths.cache_fol / sheets_tag`.
- `METADATA_PATH`, `CONTOUR_CACHE_DIR`, `MATCHES_PATH` inherit the tag automatically.

---

## Expanded Implementation Plan

### Background: Old vs. New Pattern

**Old pattern** (used in `01_db_ingestion.ipynb`):

- Hard-codes paths relative to `Path.cwd()`
- Defines a bare `load_sheet(path)` that calls `Sheet(img_fp=path, min_area=...)` directly
- Loops manually: `for img_path in sample_images: manager.add_sheet(sheet, img_path.stem)`
- No ArUco config; processes `.png` images in a `data/sample` folder

**Latest pattern** (from `02_match_debug.ipynb`, used for `data/oca` and `data/milano1`):

1. Use `get_snap_fit_paths()` for root-relative paths
2. Pick a `sheets_tag` ("oca", "milano1", …)
3. Load `SheetArucoConfig` from `data/{sheets_tag}/{sheets_tag}_SheetArucoConfig.json`
4. Create `SheetAruco(config)` and get the loader fn: `aruco_loader = sheet_aruco.load_sheet`
5. Use `manager.add_sheets(folder_path=img_fol, pattern="*.jpg", loader_func=aruco_loader)`

---

### Task 1 — Update `01_db_ingestion.ipynb`

**Changes:**

- **Imports cell**: add `SheetArucoConfig`, `SheetAruco`, `get_snap_fit_paths`; remove unused bare-`Sheet` import
- **Paths/config cell**: replace hard-coded `REPO_ROOT`/`DATA_ROOT` with `get_snap_fit_paths()`; add `sheets_tag` variable; load `SheetArucoConfig` from the tag-specific JSON
- **Load-sheets cell**: replace manual loop + bare `Sheet(...)` with `SheetAruco(config).load_sheet` as `loader_func` passed to `manager.add_sheets()`
- Keep Phase 2–5 cells unchanged (they operate on the already-populated manager)

---

### Task 2 — Update the webapp ingestion endpoint

**Files touched:**

- `src/snap_fit/webapp/schemas/piece.py` — `IngestRequest`
- `src/snap_fit/webapp/services/piece_service.py` — `PieceService.ingest_sheets`
- `src/snap_fit/webapp/routers/piece_ingestion.py` — `POST /ingest`

**Changes:**

- `IngestRequest`: replace `sheet_dir / threshold / min_area` with a single `sheets_tag: str`
  (config and image folder are derived from `data/{sheets_tag}/`)
- `PieceService.ingest_sheets(sheets_tag)`:
  - Resolve paths via `settings.data_path / sheets_tag`
  - Load `SheetArucoConfig` from `{sheets_tag}_SheetArucoConfig.json`
  - Build `aruco_loader = SheetAruco(config).load_sheet`
  - Call `manager.add_sheets(img_fol, pattern="*.jpg", loader_func=aruco_loader)`
- Router: remove `sheet_dir` path-validation block; pass `sheets_tag` to service

---

### Task 3 — Add UI element for dataset ingestion

**File touched:** `webapp_resources/templates/index.html`

**Change:** Add a new card with a small form:

- Text input for `sheets_tag` (e.g. "oca", "milano1")
- Submit button that POSTs `{"sheets_tag": "<value>"}` to `POST /api/v1/pieces/ingest`
- Shows a success/error message inline via JavaScript (no page reload)
