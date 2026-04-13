# 02 - Dataset Selector & Settings Page

> **Status:** done
> **Depends on:** -
> **Main plan ref:** Preliminary changes #1

---

## Objective

Add a "current dataset" concept so all UI pages and solver routes operate on a
single selected dataset. Currently all services scan every `cache/{tag}/` subdir
and aggregate results, which is correct for browsing but wrong for the solver
(a solve session targets one dataset).

---

## Current state

- `Settings` in `src/snap_fit/webapp/core/settings.py` has `cache_dir` and `data_dir`
  but no `current_dataset` field.
- `PieceService` and `PuzzleService` iterate all subdirs of `cache_path` looking for
  `dataset.db` files. They have no dataset-scoped mode.
- No settings page exists in the UI.
- Nav in `base.html` has: Home, Sheets, Pieces, Matches.

---

## Plan

### Step 1: Add `current_dataset` to Settings

In `src/snap_fit/webapp/core/settings.py`:

```python
class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8000
    cache_dir: str = "cache"
    data_dir: str = "data"
    current_dataset: str | None = None   # NEW - tag name, e.g. "oca"

    def available_datasets(self) -> list[str]:
        """List tag names that have a dataset.db in cache_path."""
        return sorted(
            p.parent.name
            for p in self.cache_path.glob("*/dataset.db")
        )
```

`current_dataset` starts as `None` (no dataset selected). The UI shows all data
(backward compatible). When set, services scope queries to that tag only.

### Step 2: Make it runtime-settable

`Settings` is a singleton via `get_settings()`. Add a mutable `_current_dataset`
class attribute (not a Pydantic field) so it can be changed at runtime without
restarting the server:

```python
_current_dataset_override: str | None = None

@property
def active_dataset(self) -> str | None:
    return self._current_dataset_override or self.current_dataset

def set_dataset(self, tag: str | None) -> None:
    self._current_dataset_override = tag
```

### Step 3: Add `POST /api/v1/settings/dataset` endpoint

New router file `src/snap_fit/webapp/routers/settings.py`:

```python
router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/datasets", summary="List available datasets")
async def list_datasets(settings: ...) -> list[str]:
    return settings.available_datasets()

@router.get("/current", summary="Get current dataset")
async def get_current(settings: ...) -> dict:
    return {"dataset": settings.active_dataset}

@router.post("/dataset", summary="Set current dataset")
async def set_dataset(body: SetDatasetRequest, settings: ...) -> dict:
    settings.set_dataset(body.tag)
    return {"dataset": settings.active_dataset}
```

Schema:
```python
class SetDatasetRequest(BaseModel):
    tag: str | None = None  # None to clear selection
```

### Step 4: Add settings page to UI

New template `webapp_resources/templates/settings.html`:
- Dropdown of available datasets (from `GET /api/v1/settings/datasets`)
- Current selection highlighted
- Submit button calls `POST /api/v1/settings/dataset` and refreshes

Add `GET /settings` route in `ui.py` router.

### Step 5: Update nav

In `webapp_resources/templates/base.html`, add:
- "Settings" link in nav bar
- "Solver" link in nav bar (for sub-plan 08)
- Show current dataset badge in the header if one is selected

### Step 6: Scope services (implemented)

When `settings.active_dataset` is set, `PieceService` and `PuzzleService` filter
their iteration helpers to that tag only:

- `PieceService.__init__` accepts `dataset_tag: str | None = None`; `_all_tag_dirs()`
  returns only `cache_dir / dataset_tag` when set, otherwise all sub-directories.
- `PuzzleService.__init__` accepts `dataset_tag: str | None = None`; `_all_db_paths()`
  returns only `cache_dir / dataset_tag / dataset.db` when set, otherwise scans all.
- All four `get_piece_service` / `get_puzzle_service` dependency factories (in
  `piece_ingestion.py`, `puzzle_solve.py`, and `ui.py`) now pass
  `dataset_tag=settings.active_dataset` to the constructors.

---

## File touchmap

| File | Change |
|------|--------|
| `src/snap_fit/webapp/core/settings.py` | Add `current_dataset`, `available_datasets()`, `set_dataset()` |
| `src/snap_fit/webapp/routers/settings.py` | **NEW** - settings API router (`settings_router.py`) |
| `src/snap_fit/webapp/schemas/settings.py` | **NEW** - `SetDatasetRequest` |
| `src/snap_fit/webapp/services/piece_service.py` | Add `dataset_tag` param; scope `_all_tag_dirs()` |
| `src/snap_fit/webapp/services/puzzle_service.py` | Add `dataset_tag` param; scope `_all_db_paths()` |
| `src/snap_fit/webapp/routers/ui.py` | Add `GET /settings`; pass `active_dataset` to service factories |
| `src/snap_fit/webapp/routers/piece_ingestion.py` | Pass `active_dataset` to `PieceService` factory |
| `src/snap_fit/webapp/routers/puzzle_solve.py` | Pass `active_dataset` to `PuzzleService` factory |
| `src/snap_fit/webapp/main.py` | Register settings router |
| `webapp_resources/templates/settings.html` | **NEW** - settings page |
| `webapp_resources/templates/base.html` | Add Settings + Solver nav links, dataset badge |

---

## Test strategy

- Unit test: `settings.available_datasets()` with a mock cache dir
- Unit test: `settings.set_dataset()` + `settings.active_dataset` round-trip
- Integration test: `POST /api/v1/settings/dataset` then `GET /api/v1/settings/current`
- Manual: start server, navigate to `/settings`, select a dataset, confirm badge appears
