# Step 2: Add SQLite methods to SheetManager and PieceMatcher

> Part of [10_ui_scaling.md](./10_ui_scaling.md) - SQLite migration plan
> Depends on: [Step 1](./11_sqlite_persistence_module.md) (DatasetStore exists and is tested)

---

## Starting point

`SheetManager` and `PieceMatcher` already have JSON persistence methods:

**SheetManager** (`src/snap_fit/puzzle/sheet_manager.py`):
- `to_records(data_root) -> dict` - converts in-memory Sheet/Piece objects to JSON-serializable dicts
- `save_metadata(path, data_root)` - calls `to_records()` then writes JSON
- `load_metadata(path)` [static] - reads JSON back as raw dicts (no object reconstruction)
- `save_contour_cache(cache_dir)` - writes `.npz` + `_corners.json` per sheet (binary, not affected by this migration)
- `load_contour_for_piece(piece_id, cache_dir)` [static] - loads binary contour data (not affected)

**PieceMatcher** (`src/snap_fit/puzzle/piece_matcher.py`):
- `save_matches_json(path)` - serializes `_results` list to JSON with `by_alias=True` for the `similarity_manual_` field
- `load_matches_json(path)` - deserializes JSON back into `_results` list and rebuilds `_lookup` dict
- `get_matched_pair_keys()` - returns the set of already-matched pairs (for incremental matching)
- `match_incremental(new_piece_ids)` - matches new pieces vs existing, skipping known pairs
- `clear()` - wipes all results

Both classes currently import only from `data_models/` and `config/`. Adding SQLite methods means they will also import `DatasetStore` from `persistence/`.

---

## What changes

### SheetManager: two new methods

**`save_metadata_db(db_path, data_root=None)`**

- Converts sheets and pieces to `SheetRecord` / `PieceRecord` lists (reuses existing `to_records()` logic but as Pydantic model instances, not raw dicts).
- Opens `DatasetStore(db_path)` and calls `store.save_sheets(sheet_records)` + `store.save_pieces(piece_records)`.
- Mirrors `save_metadata()` but writes to SQLite instead of JSON.

Note: `to_records()` currently returns raw dicts (via `model_dump(mode="json")`). The new method needs actual `SheetRecord` / `PieceRecord` instances. Rather than duplicating the conversion logic, consider adding an internal helper:

```python
def _to_record_objects(self, data_root: Path | None = None) -> tuple[list[SheetRecord], list[PieceRecord]]:
    sheets = [SheetRecord.from_sheet(s, data_root) for s in self.sheets.values()]
    pieces = [PieceRecord.from_piece(p) for s in self.sheets.values() for p in s.pieces]
    return sheets, pieces
```

Then `to_records()` can call `_to_record_objects()` and dump to dicts, and `save_metadata_db()` passes the objects directly to the store.

**`load_metadata_db(db_path)` [static]**

- Opens `DatasetStore(db_path)` and calls `store.load_sheets()` + `store.load_pieces()`.
- Returns `dict` with `{"sheets": list[SheetRecord], "pieces": list[PieceRecord]}` - same shape as `load_metadata()` but with Pydantic objects instead of raw dicts.
- Alternatively, return the same raw-dict format for backward compatibility. Decision: return Pydantic objects. The services layer (step 3) will be updated to consume them directly, and the JSON `load_metadata()` returns raw dicts that need `model_validate()` anyway - this is cleaner.

### PieceMatcher: two new methods

**`save_matches_db(db_path)`**

- Opens `DatasetStore(db_path)` and calls `store.save_matches(self._results)`.
- Mirrors `save_matches_json()` but writes to SQLite.

**`load_matches_db(db_path)`**

- Opens `DatasetStore(db_path)` and calls `store.load_matches()`.
- Rebuilds `_results` list and `_lookup` dict from the returned `MatchResult` objects.
- Mirrors `load_matches_json()` behavior.

### No changes to existing methods

All JSON methods remain in place:
- `SheetManager.save_metadata()`, `load_metadata()`, `to_records()` - unchanged
- `PieceMatcher.save_matches_json()`, `load_matches_json()` - unchanged
- `save_contour_cache()`, `load_contour_for_piece()` - unchanged (binary, not part of SQLite migration)

### Import additions

Both files gain one new import:

```python
from snap_fit.persistence.sqlite_store import DatasetStore
```

---

## Expected outcome

- `SheetManager` can save/load metadata to both JSON and SQLite.
- `PieceMatcher` can save/load matches to both JSON and SQLite.
- Existing tests continue to pass (no behavioral changes to existing methods).
- New tests validate the SQLite round-trip is equivalent to the JSON round-trip.
- The services layer and webapp are NOT changed yet - they still use JSON.

---

## Validation

### Unit tests

Extend existing test files rather than creating new ones.

**`tests/puzzle/test_sheet_manager.py`** - new tests:

| Test | What it checks |
|------|---------------|
| `test_save_metadata_db` | Save sheets+pieces via `save_metadata_db()`, verify `.db` file created, verify record counts via direct `DatasetStore.load_sheets/load_pieces` |
| `test_load_metadata_db` | Save via `save_metadata_db()`, then load back via `load_metadata_db()`, compare SheetRecord/PieceRecord fields to originals |
| `test_save_metadata_db_vs_json_parity` | Save the same SheetManager to both JSON (`save_metadata`) and SQLite (`save_metadata_db`), load both back, compare field-by-field |

**`tests/puzzle/test_piece_matcher.py`** - new tests:

| Test | What it checks |
|------|---------------|
| `test_save_matches_db` | Save matches via `save_matches_db()`, verify `.db` file created, verify match count via `DatasetStore.match_count()` |
| `test_load_matches_db` | Save + load via SQLite methods, verify `_results` length and `_lookup` keys match |
| `test_save_load_matches_db_round_trip` | Full round-trip including `similarity_manual_` alias handling |
| `test_save_matches_db_vs_json_parity` | Save same matcher to both JSON and SQLite, load both back, compare match lists |

### Scratch notebook cell

A notebook cell that exercises the dual-write pattern end-to-end:

1. Load the `oca` dataset into a `SheetManager` (via ArUco config as usual)
2. Run `PieceMatcher.match_all()` to generate matches
3. Save to JSON: `manager.save_metadata(json_path)` + `matcher.save_matches_json(json_path)`
4. Save to SQLite: `manager.save_metadata_db(db_path)` + `matcher.save_matches_db(db_path)`
5. Load both back and compare:
   - JSON metadata vs SQLite metadata (sheet count, piece count, field spot-check)
   - JSON matches vs SQLite matches (match count, top-5 similarity values)
6. Confirm the `.db` file is much smaller than equivalent JSON for matches (at scale)

---

## Design notes

### Why not add these methods to DatasetStore directly?

The domain classes (`SheetManager`, `PieceMatcher`) are the natural owners of save/load - they already have the JSON versions. Adding SQLite variants maintains the pattern: the domain class knows how to persist itself, and delegates the storage format to the appropriate backend.

`DatasetStore` stays a pure storage adapter (receives Pydantic models, writes SQL, reads SQL, returns Pydantic models). It has no knowledge of `SheetManager` or `PieceMatcher`.

### Return type for `load_metadata_db`

The JSON `load_metadata()` returns raw dicts because that was the path of least resistance (just `json.loads`). The SQLite `load_metadata_db()` returns Pydantic objects because `DatasetStore.load_sheets()` already returns `list[SheetRecord]`. This asymmetry is intentional and will be resolved in step 5 when the JSON methods are removed.

### Contour cache is NOT part of this step

`save_contour_cache()` and `load_contour_for_piece()` stay as-is. Binary numpy data (.npz) is not suitable for SQLite storage and is already efficient. The contour files continue to live alongside `dataset.db` in the same tag directory.
