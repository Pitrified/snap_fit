# Step 1: SQLite persistence module

> Part of [10_ui_scaling.md](./10_ui_scaling.md) - SQLite migration plan

---

## Starting point

No database code exists in the project. All persistence is JSON-based:

- `SheetManager.save_metadata()` writes `metadata.json` with `SheetRecord[]` + `PieceRecord[]`
- `PieceMatcher.save_matches_json()` writes `matches.json` with `MatchResult[]`
- `sqlite3` is a Python stdlib module - no new dependencies needed in `pyproject.toml`

The data models are already Pydantic and well-structured:

- `SheetRecord` - 6 flat fields (sheet_id, img_path, piece_count, threshold, min_area, created_at)
- `PieceRecord` - 7 fields, some JSON-serialized dicts/lists (corners, segment_shapes, flat_edges, contour_region)
- `MatchResult` - 4 fields with nested `SegmentId` objects containing `PieceId` sub-objects
- `PieceId` - frozen Pydantic model (sheet_id: str, piece_id: int)
- `SegmentId` - frozen Pydantic model (piece_id: PieceId, edge_pos: EdgePos)

---

## What changes

### New module location

```
src/snap_fit/persistence/
    __init__.py
    sqlite_store.py
```

This is a new package at the same level as `puzzle/`, `webapp/`, `data_models/`, etc. It has no imports from `webapp/` or `puzzle/` - only from `data_models/` and `config/`.

### `DatasetStore` class

A single class that manages one SQLite database file (one per dataset tag). The constructor opens (or creates) the database and ensures the schema exists.

```python
class DatasetStore:
    def __init__(self, db_path: Path) -> None: ...
    def close(self) -> None: ...

    # Schema
    def _ensure_schema(self) -> None: ...

    # Sheets
    def save_sheets(self, records: list[SheetRecord]) -> None: ...
    def load_sheets(self) -> list[SheetRecord]: ...
    def load_sheet(self, sheet_id: str) -> SheetRecord | None: ...

    # Pieces
    def save_pieces(self, records: list[PieceRecord]) -> None: ...
    def load_pieces(self) -> list[PieceRecord]: ...
    def load_piece(self, piece_id: str) -> PieceRecord | None: ...
    def load_pieces_for_sheet(self, sheet_id: str) -> list[PieceRecord]: ...

    # Matches
    def save_matches(self, results: list[MatchResult]) -> None: ...
    def load_matches(
        self, limit: int | None = None, min_similarity: float | None = None
    ) -> list[MatchResult]: ...
    def query_matches_for_piece(
        self, piece_id: str, limit: int = 10
    ) -> list[MatchResult]: ...
    def query_matches_for_segment(
        self, piece_id: str, edge_pos: str, limit: int = 5
    ) -> list[MatchResult]: ...
    def match_count(self) -> int: ...
```

### Schema creation

`_ensure_schema()` runs `CREATE TABLE IF NOT EXISTS` for all three tables plus indexes. Called once from `__init__`. Uses `sqlite3.connect()` with `check_same_thread=False` for the FastAPI use case (each request creates its own `DatasetStore` instance, so thread safety is handled at the instance level).

### Row conversion design

The key design decision: how to map nested Pydantic models to flat SQLite rows and back.

**Sheets and pieces** are straightforward. Fields that hold dicts/lists (`corners`, `segment_shapes`, `flat_edges`, `contour_region`) are stored as JSON text columns and round-tripped via `json.dumps()` / `json.loads()`.

**Matches** require flattening the nested `SegmentId` -> `PieceId` hierarchy. A `MatchResult` like:

```python
MatchResult(
    seg_id1=SegmentId(piece_id=PieceId(sheet_id="s1", piece_id=0), edge_pos=EdgePos.LEFT),
    seg_id2=SegmentId(piece_id=PieceId(sheet_id="s2", piece_id=1), edge_pos=EdgePos.TOP),
    similarity=13.85,
    similarity_manual_=None,
)
```

becomes a row:

```
(seg_id1_sheet_id="s1", seg_id1_piece_idx=0, seg_id1_edge_pos="left",
 seg_id2_sheet_id="s2", seg_id2_piece_idx=1, seg_id2_edge_pos="top",
 similarity=13.85, similarity_manual=NULL)
```

The store handles this flattening/unflattening internally with two private helpers:

```python
def _match_to_row(self, m: MatchResult) -> tuple: ...
def _row_to_match(self, row: sqlite3.Row) -> MatchResult: ...
```

`_row_to_match` reconstructs the nested `SegmentId(PieceId(...), EdgePos(...))` from flat columns.

### Bulk writes

`save_sheets()`, `save_pieces()`, and `save_matches()` use `executemany()` with `INSERT OR REPLACE` for idempotent writes. This means calling `save_matches()` twice with the same data is safe, and re-ingestion overwrites stale records.

For matches, the natural key for `OR REPLACE` would be the combination of both segment IDs. Add a UNIQUE constraint on `(seg_id1_sheet_id, seg_id1_piece_idx, seg_id1_edge_pos, seg_id2_sheet_id, seg_id2_piece_idx, seg_id2_edge_pos)` to support this. Alternatively, keep the auto-increment PK and `DELETE` before re-inserting within a transaction - simpler and fine for our batch-write pattern.

Decision: use `DELETE FROM matches` + `executemany INSERT` within a single transaction for `save_matches()`. This is simpler than managing composite unique constraints and matches the current JSON behavior (full overwrite on each save).

### Match queries use WHERE + LIMIT

The whole point of SQLite for matches is indexed lookups. The query methods push filtering into SQL:

- `query_matches_for_piece(piece_id)` -> `WHERE seg_id1_sheet_id = ? AND seg_id1_piece_idx = ? OR seg_id2_sheet_id = ? AND seg_id2_piece_idx = ? ORDER BY similarity LIMIT ?`
- `query_matches_for_segment(piece_id, edge_pos)` -> same but also filters on `edge_pos`
- `load_matches(limit, min_similarity)` -> `WHERE similarity >= ? ORDER BY similarity LIMIT ?`
- `match_count()` -> `SELECT COUNT(*) FROM matches`

The `piece_id` string has format `sheet_id:piece_idx`. The store parses this into the two components for the query. Alternatively, accept the already-split components. Decision: accept the string form (consistent with how services pass it) and split internally.

### Context manager support

`DatasetStore` should support `with` for clean resource management:

```python
def __enter__(self) -> DatasetStore: ...
def __exit__(self, *exc: object) -> None: ...
```

This ensures the connection is closed after use. Services can use `with DatasetStore(db_path) as store:` for each request.

---

## Expected outcome

- A standalone `src/snap_fit/persistence/sqlite_store.py` module that can be imported and used independently of the webapp or domain logic.
- The module converts between Pydantic models (`SheetRecord`, `PieceRecord`, `MatchResult`) and SQLite rows.
- No changes to any existing code. No removal of JSON methods.
- Full test coverage in `tests/persistence/test_sqlite_store.py`.

---

## Validation

### Unit tests (`tests/persistence/test_sqlite_store.py`)

Tests should use `tmp_path` fixture and create throwaway `.db` files.

| Test | What it checks |
|------|---------------|
| `test_create_store_creates_tables` | Open a fresh .db, verify tables exist via `sqlite_master` |
| `test_save_load_sheets_round_trip` | Save 3 SheetRecords, load them back, assert field equality |
| `test_save_load_pieces_round_trip` | Save PieceRecords with JSON fields (corners, segment_shapes), reload, assert dicts match |
| `test_save_load_matches_round_trip` | Save MatchResults with nested SegmentId/PieceId, reload, assert full equality including `similarity_manual_` |
| `test_load_sheet_by_id` | Save multiple sheets, query one by ID, verify correct record returned |
| `test_load_pieces_for_sheet` | Save pieces from 2 sheets, query by sheet_id, verify only correct pieces returned |
| `test_query_matches_for_piece` | Save 20+ matches, query for one piece_id, verify only relevant matches returned and sorted |
| `test_query_matches_for_segment` | Same but narrowed to specific edge_pos |
| `test_match_count` | Save N matches, verify count returns N |
| `test_load_matches_with_limit` | Save 100 matches, load with limit=10, verify 10 returned |
| `test_load_matches_with_min_similarity` | Save matches with varying scores, filter by threshold |
| `test_save_matches_overwrites` | Save matches twice, verify no duplicates (second write replaces first) |
| `test_context_manager` | Use `with DatasetStore(...) as store:`, verify it works and closes cleanly |

### Scratch notebook cell

A cell in the existing `01_db_ingestion.ipynb` (or a new notebook) that:

1. Loads the existing `cache/oca/metadata.json` and `cache/oca/matches.json` using the current JSON methods
2. Creates a temporary `DatasetStore` (e.g. `/tmp/test_oca.db`)
3. Feeds the loaded records into `save_sheets()`, `save_pieces()`, `save_matches()`
4. Reads them back via `load_sheets()`, `load_pieces()`, `load_matches()`
5. Compares counts and spot-checks a few records for field equality
6. Runs `query_matches_for_piece()` for one piece and verifies the results are the same as filtering the JSON list manually

---

## Design decisions summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Module location | `src/snap_fit/persistence/` | Clean separation; no coupling to webapp or puzzle layers |
| One DB per dataset tag | `cache/{tag}/dataset.db` | Mirrors the existing per-tag directory structure |
| JSON columns for nested data | `corners`, `segment_shapes`, etc. as TEXT | Avoids normalizing into many tables; these fields are not queried by individual key |
| Flattened match columns | `seg_id1_sheet_id`, `seg_id1_piece_idx`, `seg_id1_edge_pos` | Enables indexed WHERE clauses; the whole point of the migration |
| Batch write strategy | DELETE + INSERT in transaction | Simpler than UPSERT with 6-column composite key; matches the full-overwrite JSON pattern |
| Thread safety | One connection per `DatasetStore` instance | FastAPI creates a new service per request; no shared connections |
