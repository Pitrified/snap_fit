# 06 - Run Matching Endpoint

> **Status:** not started
> **Depends on:** -
> **Main plan ref:** Phase 4

---

## Objective

Add a `POST /api/v1/puzzle/run_matching` endpoint that triggers
`PieceMatcher.match_all()` for a dataset tag. This is a prerequisite for the
suggestion engine - match scores must exist before the solver can rank candidates.

Currently, matching must be done manually via notebook code. The webapp has no
way to trigger it.

---

## Current state

- `PieceMatcher.match_all()` exists and works. It iterates all segment pairs,
  calls `match_pair()` for each, and sorts results by similarity.
- `PieceMatcher.save_matches_db(db_path)` writes results to SQLite.
- `PieceMatcher.load_matches_db(db_path)` reads them back.
- `PuzzleService.solve_puzzle()` is a stub that returns `{"success": False}`.
- `puzzle_solve.py` router has `POST /solve` hooked to the stub.
- Matching for a full dataset (e.g. oca with ~48 pieces, 4 segments each =
  ~192 segments, ~18000 pairs) takes several minutes.

---

## Plan

### Step 1: Blocking implementation (prototype)

Start with a simple blocking endpoint. The user's browser shows a spinner.
For a dataset with 48 pieces this takes 2-5 minutes, which is acceptable for
a dev tool with a progress-spinner UI.

```python
# In src/snap_fit/webapp/routers/puzzle_solve.py

@router.post("/run_matching", summary="Run segment matching")
async def run_matching(
    request: RunMatchingRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> RunMatchingResponse:
    """Run PieceMatcher.match_all() for a dataset.

    This is a blocking call that may take several minutes.
    """
```

Schema:
```python
class RunMatchingRequest(BaseModel):
    dataset_tag: str
    force: bool = False  # re-run even if matches already exist

class RunMatchingResponse(BaseModel):
    success: bool
    message: str
    match_count: int
    duration_seconds: float
```

### Step 2: Service method

In `src/snap_fit/webapp/services/puzzle_service.py`, add:

```python
def run_matching(self, dataset_tag: str, force: bool = False) -> dict:
    """Execute segment matching for a dataset.

    1. Load sheets via SheetAruco + SheetManager
    2. If matches exist and not force, return early
    3. Create PieceMatcher(manager)
    4. Call match_all()
    5. Save to dataset.db via save_matches_db()
    6. Return summary
    """
    db_path = self._cache_path / dataset_tag / "dataset.db"
    store = DatasetStore(db_path)

    if not force:
        existing = store.load_matches(limit=1)
        if existing:
            return {"success": True, "message": "Matches already exist", "match_count": store.match_count(), "duration_seconds": 0}

    # Load sheets
    config_path = ...  # resolve from data/{tag}/{tag}_SheetArucoConfig.json
    sheet_aruco = SheetAruco.from_config(config_path)
    img_dir = ...  # data/{tag}/sheets/
    manager = SheetManager()
    manager.add_sheets(sheet_aruco, img_dir)

    # Run matching
    import time
    t0 = time.monotonic()
    matcher = PieceMatcher(manager)
    matcher.match_all()
    matcher.save_matches_db(db_path)
    duration = time.monotonic() - t0

    return {
        "success": True,
        "message": f"Matched {len(matcher._results)} pairs in {duration:.1f}s",
        "match_count": len(matcher._results),
        "duration_seconds": round(duration, 2),
    }
```

### Step 3: Config resolution

The service needs to find `SheetArucoConfig` and sheet image paths. This is
currently done by `PieceService.ingest_sheets()`. Extract the config resolution
logic into a shared helper:

```python
def resolve_dataset_paths(data_path: Path, tag: str) -> tuple[Path, Path]:
    """Resolve config JSON and sheets directory for a dataset tag.

    Returns:
        (config_path, sheets_dir)
    """
    config_path = data_path / tag / f"{tag}_SheetArucoConfig.json"
    sheets_dir = data_path / tag / "sheets"
    return config_path, sheets_dir
```

### Step 4: Match count check

Add `match_count()` to `DatasetStore` if not already present:

```python
def match_count(self) -> int:
    row = self._conn.execute("SELECT COUNT(*) FROM matches").fetchone()
    return row[0]
```

### Step 5: Wire to UI

Add a "Run Matching" button on the settings page or dataset detail page.
JavaScript calls `POST /api/v1/puzzle/run_matching` with the dataset tag,
shows a spinner, and displays the result.

```html
<button id="run-matching" onclick="runMatching()">Run Matching</button>
<div id="matching-status"></div>

<script>
async function runMatching() {
    const btn = document.getElementById('run-matching');
    btn.disabled = true;
    btn.textContent = 'Running...';
    const res = await fetch('/api/v1/puzzle/run_matching', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({dataset_tag: currentDataset})
    });
    const data = await res.json();
    document.getElementById('matching-status').textContent =
        `${data.match_count} matches in ${data.duration_seconds}s`;
    btn.disabled = false;
    btn.textContent = 'Run Matching';
}
</script>
```

### Future: Background job with polling

If blocking is too slow for larger datasets, switch to background execution:
1. `POST /run_matching` returns immediately with a `job_id`
2. The matching runs in a background thread / `asyncio.to_thread()`
3. `GET /matching_status/{job_id}` returns progress (% pairs done) and final result
4. JS polls every 2 seconds

Deferred until blocking proves insufficient.

---

## File touchmap

| File | Change |
|------|--------|
| `src/snap_fit/webapp/services/puzzle_service.py` | Add `run_matching()` method |
| `src/snap_fit/webapp/routers/puzzle_solve.py` | Add `POST /run_matching` endpoint |
| `src/snap_fit/webapp/schemas/puzzle.py` | Add `RunMatchingRequest`, `RunMatchingResponse` |
| `src/snap_fit/persistence/sqlite_store.py` | Add `match_count()` if missing |
| `webapp_resources/templates/settings.html` | Add "Run Matching" button (or separate page) |

---

## Test strategy

- Unit test: `run_matching()` with a small synthetic dataset (2-3 pieces)
- Unit test: `force=False` skips when matches exist
- Integration test: `POST /api/v1/puzzle/run_matching` returns match_count > 0
- Manual: run on `demo` dataset, verify matches appear in `/matches` page
