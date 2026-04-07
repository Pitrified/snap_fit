# `puzzle/sheet_manager`

> Module: `src/snap_fit/puzzle/sheet_manager.py`
> Related tests: `tests/puzzle/`

## Purpose

`SheetManager` is the central registry for all loaded puzzle sheets. It provides lookup methods for sheets, pieces, and segments by ID, and handles persistence (JSON metadata, SQLite database, binary contour cache).

## Usage

### Minimal example

```python
from snap_fit.puzzle.sheet_manager import SheetManager
from snap_fit.puzzle.sheet import Sheet
from pathlib import Path

manager = SheetManager()

# Add individual sheets
sheet = Sheet(img_fp=Path("photo.jpg"))
manager.add_sheet(sheet, "photo_01")

# Or bulk-load from a folder
manager.add_sheets(
    folder_path=Path("data/oca/sheets/"),
    pattern="*.jpg",
    loader_func=lambda fp: Sheet(img_fp=fp),
)

# Query
all_pieces = manager.get_pieces_ls()
segment_ids = manager.get_segment_ids_all()
piece = manager.get_piece(PieceId(sheet_id="photo_01", piece_id=0))
```

### Persistence

```python
from pathlib import Path

# Save metadata to JSON
manager.save_metadata(Path("cache/metadata.json"), data_root=Path("data/"))

# Save metadata to SQLite
manager.save_metadata_db(Path("cache/dataset.db"), data_root=Path("data/"))

# Save binary contour cache
manager.save_contour_cache(Path("cache/contours/"))

# Load metadata (static methods)
records = SheetManager.load_metadata(Path("cache/metadata.json"))
records_db = SheetManager.load_metadata_db(Path("cache/dataset.db"))

# Load contour for a specific piece
contour, corners = SheetManager.load_contour_for_piece(piece_id, Path("cache/contours/"))
```

## API Reference

### `SheetManager`

Central registry for puzzle sheets.

Key methods:

| Method | Description |
|--------|-------------|
| `add_sheet(sheet, sheet_id)` | Register a sheet with a given ID |
| `add_sheets(folder, pattern, loader_func)` | Glob a folder and load sheets |
| `get_sheet(sheet_id)` | Retrieve sheet by ID |
| `get_piece(piece_id)` | Retrieve piece by `PieceId` |
| `get_segment(seg_id)` | Retrieve segment by `SegmentId` |
| `get_pieces_ls()` | Flat list of all pieces across sheets |
| `get_segment_ids_all()` | All segment IDs (4 per piece per sheet) |
| `get_segment_ids_other_pieces(seg_id)` | Segment IDs excluding the given piece |
| `save_metadata(path, data_root)` | Write JSON metadata |
| `save_metadata_db(db_path, data_root)` | Write SQLite metadata |
| `save_contour_cache(cache_dir)` | Write `.npz` + `.json` per sheet |
| `load_metadata(path)` | Static: read JSON metadata |
| `load_metadata_db(db_path)` | Static: read SQLite metadata |
| `load_contour_for_piece(piece_id, cache_dir)` | Static: load one piece's contour |

## Common Pitfalls

- **Sheet ID conflicts**: `add_sheet` warns but overwrites if the sheet_id already exists. Ensure IDs are unique across datasets.
- **PieceId consistency**: `add_sheet` patches the `sheet_id` in all child piece IDs to match the registered key. Do not rely on the original piece IDs after adding to the manager.
- **Contour cache format**: Each sheet produces two files: `{sheet_id}_contours.npz` (compressed numpy) and `{sheet_id}_corners.json`. Both are needed to reconstruct segments.

## Related Modules

- [`puzzle/sheet`](sheet.md) - the `Sheet` objects managed by `SheetManager`
- [`puzzle/piece_matcher`](piece_matcher.md) - consumes a `SheetManager` for segment lookups during matching
- [`data_models`](../data_models/index.md) - `SheetRecord` and `PieceRecord` used for persistence
- [`persistence`](../persistence/index.md) - `DatasetStore` used by `save_metadata_db()`
