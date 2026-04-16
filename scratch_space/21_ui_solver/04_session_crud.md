# 04 - Session CRUD & PlacementState Persistence

> **Status:** done
> **Depends on:** 02 (dataset selector)
> **Main plan ref:** Phase 2

---

## Objective

Implement the interactive solve session lifecycle: create, read, update (place/undo),
delete. Sessions wrap `PlacementState` + `GridModel` and persist to SQLite so they
survive server restarts.

---

## Current state

- `PlacementState` in `src/snap_fit/grid/placement_state.py` is fully functional
  (place, remove, get_placement, get_position, clone, empty_positions, etc.) but
  has no serialization methods.
- `interactive.py` router has a single stub `GET /session` returning a hardcoded
  `SessionInfo(session_id="placeholder", active=False)`.
- `SessionInfo` schema has only `session_id: str` and `active: bool`.
- No `InteractiveService` exists.
- `DatasetStore` (SQLite) has `sheets`, `pieces`, `matches` tables. No `sessions` table.

---

## Plan

### Step 1: PlacementState serialization

Add `to_dict()` and `from_dict()` to `PlacementState`:

```python
# In src/snap_fit/grid/placement_state.py

def to_dict(self) -> dict[str, tuple[str, int]]:
    """Serialize placements to a JSON-friendly dict.

    Returns:
        Mapping of "ro,co" -> ("sheet_id:piece_idx", orientation_deg).
    """
    return {
        f"{pos.ro},{pos.co}": (str(piece_id), orientation.value)
        for pos, (piece_id, orientation) in self._placements.items()
    }

@classmethod
def from_dict(
    cls,
    grid: GridModel,
    data: dict[str, tuple[str, int]],
) -> PlacementState:
    """Reconstruct from serialized dict.

    Args:
        grid: The GridModel for validation.
        data: Output of to_dict().
    """
    state = cls(grid)
    for pos_str, (pid_str, orient_val) in data.items():
        ro, co = pos_str.split(",")
        pos = GridPos(ro=int(ro), co=int(co))
        piece_id = PieceId.from_str(pid_str)
        orientation = Orientation(orient_val)
        state.place(piece_id, pos, orientation)
    return state
```

This requires `PieceId.from_str()`. Check if it exists - if not, add:

```python
# In src/snap_fit/data_models/piece_id.py
@classmethod
def from_str(cls, s: str) -> PieceId:
    """Parse 'sheet_id:piece_idx' format."""
    sheet_id, piece_idx = s.rsplit(":", 1)
    return cls(sheet_id=sheet_id, piece_id=int(piece_idx))
```

### Step 2: Session schema

Replace `SessionInfo` and add richer models.

In `src/snap_fit/webapp/schemas/interactive.py`:

```python
from datetime import datetime

from pydantic import BaseModel

class CreateSessionRequest(BaseModel):
    dataset_tag: str
    grid_rows: int | None = None   # None = auto-infer from piece count
    grid_cols: int | None = None

class PlaceRequest(BaseModel):
    piece_id: str
    position: str         # "ro,co"
    orientation: int      # 0, 90, 180, 270

class SuggestionRequest(BaseModel):
    override_pos: str | None = None   # "ro,co" or None for auto

class SolveSessionResponse(BaseModel):
    session_id: str
    dataset_tag: str
    grid_rows: int
    grid_cols: int
    placement: dict[str, tuple[str, int]]
    rejected: dict[str, list[str]]
    placed_count: int
    total_cells: int
    complete: bool
    score: float | None = None
    created_at: datetime
    updated_at: datetime

class SuggestionCandidate(BaseModel):
    piece_id: str
    piece_label: str | None = None
    orientation: int
    score: float
    neighbor_scores: dict[str, float]

class SuggestionBundle(BaseModel):
    slot: str
    candidates: list[SuggestionCandidate]
    current_index: int = 0
```

### Step 3: SQLite sessions table

In `src/snap_fit/persistence/sqlite_store.py`, add:

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    dataset_tag TEXT NOT NULL,
    grid_rows INTEGER NOT NULL,
    grid_cols INTEGER NOT NULL,
    placement TEXT NOT NULL DEFAULT '{}',   -- JSON dict
    rejected TEXT NOT NULL DEFAULT '{}',    -- JSON dict
    complete INTEGER NOT NULL DEFAULT 0,
    score REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

Methods on `DatasetStore`:
- `save_session(session_id, data_dict) -> None`
- `load_session(session_id) -> dict | None`
- `load_sessions() -> list[dict]`
- `delete_session(session_id) -> None`
- `update_session(session_id, data_dict) -> None`

Placement and rejected are stored as JSON text columns. Serialization via
`json.dumps()` / `json.loads()`.

Migration for existing databases:
```python
_MIGRATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    ...
)
"""
```

### Step 4: InteractiveService

New file `src/snap_fit/webapp/services/interactive_service.py`:

```python
class InteractiveService:
    """Manages solve sessions with SQLite persistence."""

    def __init__(self, cache_path: Path, data_path: Path) -> None:
        self._cache_path = cache_path
        self._data_path = data_path

    def _store(self, tag: str) -> DatasetStore:
        return DatasetStore(self._cache_path / tag / "dataset.db")

    def create_session(
        self,
        dataset_tag: str,
        grid_rows: int | None = None,
        grid_cols: int | None = None,
    ) -> SolveSessionResponse:
        """Create a new solve session.

        If grid_rows/cols are None, infer from piece count using
        solver.utils.get_factor_pairs().
        """
        store = self._store(dataset_tag)
        pieces = store.load_pieces()

        if grid_rows is None or grid_cols is None:
            pairs = get_factor_pairs(len(pieces))
            if not pairs:
                raise ValueError(...)
            grid_rows, grid_cols = pairs[0]  # smallest valid grid

        session_id = str(uuid4())
        now = datetime.utcnow()
        session_data = {
            "session_id": session_id,
            "dataset_tag": dataset_tag,
            "grid_rows": grid_rows,
            "grid_cols": grid_cols,
            "placement": {},
            "rejected": {},
            "complete": False,
            "score": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        store.save_session(session_id, session_data)
        return SolveSessionResponse(**session_data, placed_count=0, total_cells=grid_rows*grid_cols)

    def get_session(self, dataset_tag: str, session_id: str) -> SolveSessionResponse | None:
        ...

    def place_piece(
        self,
        dataset_tag: str,
        session_id: str,
        piece_id: str,
        position: str,
        orientation: int,
    ) -> SolveSessionResponse:
        """Place a piece on the grid. Validates type compatibility."""
        ...

    def undo(self, dataset_tag: str, session_id: str) -> SolveSessionResponse:
        """Remove the last placed piece (undo stack)."""
        ...

    def delete_session(self, dataset_tag: str, session_id: str) -> None:
        ...

    def list_sessions(self, dataset_tag: str) -> list[SolveSessionResponse]:
        ...
```

Undo requires tracking placement order. Add an `undo_stack` field to the session
(list of position strings, most recent last). Store in SQLite as JSON text.

### Step 5: Interactive router

Rewrite `src/snap_fit/webapp/routers/interactive.py`:

```python
router = APIRouter(prefix="/interactive", tags=["interactive"])

@router.post("/sessions", summary="Create solve session")
async def create_session(req: CreateSessionRequest, ...) -> SolveSessionResponse:

@router.get("/sessions", summary="List sessions for dataset")
async def list_sessions(dataset_tag: str, ...) -> list[SolveSessionResponse]:

@router.get("/sessions/{session_id}", summary="Get session state")
async def get_session(session_id: str, dataset_tag: str, ...) -> SolveSessionResponse:

@router.post("/sessions/{session_id}/place", summary="Place a piece")
async def place_piece(session_id: str, req: PlaceRequest, dataset_tag: str, ...) -> SolveSessionResponse:

@router.post("/sessions/{session_id}/undo", summary="Undo last placement")
async def undo(session_id: str, dataset_tag: str, ...) -> SolveSessionResponse:

@router.delete("/sessions/{session_id}", summary="Delete session")
async def delete_session(session_id: str, dataset_tag: str, ...) -> dict:
```

The `dataset_tag` parameter comes from query params or from
`settings.active_dataset` (see sub-plan 02).

---

## File touchmap

| File | Change |
|------|--------|
| `src/snap_fit/grid/placement_state.py` | Add `to_dict()`, `from_dict()` |
| `src/snap_fit/data_models/piece_id.py` | Add `from_str()` if missing |
| `src/snap_fit/webapp/schemas/interactive.py` | Replace `SessionInfo` with full schema set |
| `src/snap_fit/persistence/sqlite_store.py` | Add `sessions` table DDL, CRUD methods |
| `src/snap_fit/webapp/services/interactive_service.py` | **NEW** - session management service |
| `src/snap_fit/webapp/routers/interactive.py` | Rewrite with full session CRUD endpoints |
| `src/snap_fit/webapp/main.py` | Verify router registration (already registered) |

---

## Test strategy

- Unit test: `PlacementState.to_dict()` / `from_dict()` round-trip
- Unit test: `PieceId.from_str()` parsing
- Unit test: `DatasetStore` session CRUD (create, load, update, delete)
- Unit test: `InteractiveService.create_session()` with mock data
- Integration test: full HTTP lifecycle - create, place, get, undo, delete
- Edge cases: place on occupied slot, undo on empty session, invalid orientation
