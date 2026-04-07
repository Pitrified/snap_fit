# `persistence`

> Module: `src/snap_fit/persistence/`
> Related tests: `tests/persistence/`

## Purpose

SQLite-backed storage for sheet metadata, piece records, and match results. The `DatasetStore` class provides a clean interface between Pydantic models and flat SQLite rows, with one database file per dataset.

## Usage

### Minimal example

```python
from pathlib import Path
from snap_fit.persistence.sqlite_store import DatasetStore

# Create/open a database (schema auto-created)
with DatasetStore(Path("cache/oca/dataset.db")) as store:
    # Save records
    store.save_sheets(sheet_records)
    store.save_pieces(piece_records)
    store.save_matches(match_results)

    # Query
    sheets = store.load_sheets()
    pieces = store.load_pieces()
    matches = store.load_matches(min_similarity=0.0)

    # Filtered queries
    piece = store.load_piece("sheet_01:3")
    piece_matches = store.query_matches_for_piece("sheet_01:3", limit=10)
    seg_matches = store.query_matches_for_segment("sheet_01:3", "top", limit=5)
    count = store.match_count()
```

## API Reference

### `DatasetStore`

Context manager wrapping a single SQLite database file. Creates tables and indexes on first open.

**Schema:**

- `sheets` table: `sheet_id` (PK), `img_path`, `piece_count`, `threshold`, `min_area`, `created_at`
- `pieces` table: `piece_id` (PK), `sheet_id` (FK), `piece_idx`, `corners` (JSON), `segment_shapes` (JSON), `oriented_piece_type`, `flat_edges` (JSON), `contour_point_count`, `contour_region` (JSON)
- `matches` table: auto-increment ID, segment IDs (sheet, piece_idx, edge_pos for both sides), `similarity`, `similarity_manual`

**Indexes:** on `matches` for both segment sides and on `similarity`.

| Method | Description |
|--------|-------------|
| `save_sheets(records)` | Upsert sheet records |
| `save_pieces(records)` | Upsert piece records |
| `save_matches(results)` | Delete existing + insert match results |
| `load_sheets()` | All `SheetRecord` objects |
| `load_pieces()` | All `PieceRecord` objects |
| `load_sheet(sheet_id)` | Single sheet by ID |
| `load_piece(piece_id)` | Single piece by ID |
| `load_matches(min_similarity, limit)` | Filtered matches |
| `query_matches_for_piece(piece_id, limit)` | Matches involving a piece |
| `query_matches_for_segment(piece_id, edge_pos, limit)` | Matches for a segment |
| `match_count()` | Total number of matches |

## Common Pitfalls

- **save_matches deletes first**: Calling `save_matches()` deletes all existing matches before inserting. This is a full replace, not an upsert.
- **JSON-in-columns**: Fields like `corners`, `segment_shapes`, `flat_edges`, and `contour_region` are stored as JSON strings in TEXT columns. They are deserialized back to Python types on load.
- **Piece ID format**: Piece IDs are stored as `"sheet_id:piece_idx"` strings. The `_parse_piece_id()` helper splits on the last `:` to handle sheet IDs that may contain colons.

## Related Modules

- [`data_models`](../data_models/index.md) - `SheetRecord`, `PieceRecord`, `MatchResult` that are stored
- [`puzzle/sheet_manager`](../puzzle/sheet_manager.md) - calls `save_metadata_db()` and `load_metadata_db()`
- [`puzzle/piece_matcher`](../puzzle/piece_matcher.md) - calls `save_matches_db()` and `load_matches_db()`
- [`webapp/services`](../webapp/index.md) - uses `DatasetStore` for all data access
