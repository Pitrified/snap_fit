# `data_models`

> Module: `src/snap_fit/data_models/`
> Related tests: `tests/data_models/`

## Purpose

Pydantic models that define the core data vocabulary of snap_fit. These models are used for identity (`PieceId`, `SegmentId`), persistence (`PieceRecord`, `SheetRecord`, `MatchResult`), and configuration forwarding (`BaseModelKwargs`). All are frozen (immutable and hashable) where identity semantics are needed.

## Usage

### Creating identifiers

```python
from snap_fit.data_models import PieceId, SegmentId
from snap_fit.config.types import EdgePos

pid = PieceId(sheet_id="sheet_01", piece_id=3)
sid = SegmentId(piece_id=pid, edge_pos=EdgePos.TOP)

print(pid)  # "sheet_01:3"
print(sid)  # "sheet_01:3:top"
```

### Working with match results

```python
from snap_fit.data_models import MatchResult

match = MatchResult(seg_id1=sid_a, seg_id2=sid_b, similarity=12.5)

# Symmetric lookup key
pair_key = match.pair  # frozenset({sid_a, sid_b})

# Get the other side of a match
other = match.get_other(sid_a)  # returns sid_b
```

### Converting from domain objects to records

```python
from snap_fit.data_models import SheetRecord, PieceRecord

sheet_record = SheetRecord.from_sheet(sheet, data_root=Path("data/"))
piece_record = PieceRecord.from_piece(piece)
```

## API Reference

### `PieceId`

Frozen Pydantic model identifying a piece within a sheet. Fields: `sheet_id: str`, `piece_id: int`. Hashable for use as dict keys and set members.

### `SegmentId`

Frozen Pydantic model identifying a specific edge segment. Fields: `piece_id: PieceId`, `edge_pos: EdgePos`. Provides convenience properties `sheet_id` and `piece_id_int` for backward compatibility.

### `MatchResult`

Stores the result of matching two segments. Fields: `seg_id1`, `seg_id2`, `similarity: float`, `similarity_manual_: float | None`. Key properties:

- `pair` - frozenset of the two segment IDs for symmetric lookup
- `get_other(seg_id)` - returns the other segment in the pair
- `similarity_manual` - property that falls back to `similarity` when manual override is not set

### `PieceRecord`

DB-friendly metadata representation of a `Piece`. Stores corners, segment shapes, oriented piece type, flat edges, contour point count, and bounding region. Created via `PieceRecord.from_piece(piece)`.

### `SheetRecord`

DB-friendly metadata representation of a `Sheet`. Stores sheet_id, image path (relative to data root), piece count, threshold, min_area, and creation timestamp. Created via `SheetRecord.from_sheet(sheet, data_root)`.

### `BaseModelKwargs`

Pydantic base class with a `to_kw(exclude_none=False)` method that converts the model to a flat dict, merging any nested `kwargs` attribute at the top level. Used by ArUco config classes to forward constructor arguments.

## Common Pitfalls

- **MatchResult alias**: The `similarity_manual_` field uses the alias `"similarity_manual"` for serialization. When dumping to JSON, use `model_dump(by_alias=True)` to get the correct field name.
- **PieceId string format**: `str(piece_id)` produces `"sheet_id:piece_id"`. Parsing back requires splitting on the last `:` since sheet_id itself may contain colons.
- **Frozen models**: `PieceId` and `SegmentId` are frozen (immutable). You cannot modify their fields after creation - create a new instance instead.

## Related Modules

- [`config`](../config/index.md) - provides `EdgePos`, `CornerPos`, `SegmentShape` used by these models
- [`puzzle/piece`](../puzzle/piece.md) - domain object that `PieceRecord.from_piece()` converts from
- [`puzzle/sheet`](../puzzle/sheet.md) - domain object that `SheetRecord.from_sheet()` converts from
- [`persistence`](../persistence/index.md) - stores these records in SQLite
