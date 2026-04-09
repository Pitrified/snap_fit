# Step 09 - Wire into `Sheet`, `SheetAruco`, Records

> **Status:** not started
> **Target files:** multiple (see touchmap)
> **Depends on:** Steps 02, 05, 06, 08

---

## Objective

This is the integration step that wires all the new components into the existing
pipeline. It modifies `Sheet`, `SheetAruco`, `SheetRecord`, and `PieceRecord` to
carry metadata and slot labels through from ingestion to persistence.

## Changes

### 9.1 `Sheet` - add `metadata` attribute

```python
# In src/snap_fit/puzzle/sheet.py

class Sheet:
    def __init__(self, ...):
        ...
        self.metadata: SheetMetadata | None = None  # set by SheetAruco.load_sheet()
```

No import at module level to avoid circular deps - use `TYPE_CHECKING` guard:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from snap_fit.aruco.sheet_metadata import SheetMetadata
```

### 9.2 `Sheet.build_pieces()` - assign slot labels

After contour detection, map each piece's centroid to a slot label if the slot
grid is available. This requires knowing the board config (via metadata_zone on
SheetArucoConfig) and the board geometry.

```python
# In build_pieces(), after creating each Piece:
# If slot_grid is available, assign label based on centroid
if slot_grid is not None:
    cx, cy = contour.centroid
    slot = slot_grid.slot_for_centroid(cx, cy)
    if slot:
        piece.label = slot_grid.label_for_slot(*slot)
```

**Design question:** How does `Sheet` get access to the `SlotGrid`? Options:
1. Pass `SlotGrid` as an optional parameter to `build_pieces()` or `find_pieces()`
2. Store it on `Sheet` (set by `SheetAruco` alongside metadata)
3. Compute it from metadata + board config

Recommendation: Option 2 - `SheetAruco.load_sheet()` creates the `SlotGrid`
from its config and attaches it to the sheet.

```python
# In Sheet.__init__
self.slot_grid: SlotGrid | None = None  # set by SheetAruco
```

### 9.3 `Piece` - add `label` attribute

```python
# In src/snap_fit/puzzle/piece.py (or wherever Piece is defined)
class Piece:
    def __init__(self, ...):
        ...
        self.label: str | None = None  # e.g. "A1", set during build_pieces()
```

### 9.4 `SheetAruco.load_sheet()` - decode metadata, attach slot grid

```python
# Modified load_sheet() in src/snap_fit/puzzle/sheet_aruco.py
def load_sheet(self, img_fp: Path) -> Sheet:
    img_orig = load_image(img_fp)

    # Decode metadata BEFORE rectification
    metadata = SheetMetadataDecoder().decode(img_orig)
    if metadata is None:
        lg.warning(f"No sheet metadata QR found in {img_fp.name}")

    # Existing rectification + cropping
    rectified = self.aruco_detector.rectify(img_orig)
    ...

    sheet = Sheet(img_fp=img_fp, min_area=self.config.min_area, image=img_final)
    sheet.metadata = metadata

    # Attach slot grid if metadata_zone is configured
    if self.config.metadata_zone and self.config.metadata_zone.enabled:
        from snap_fit.aruco.slot_grid import SlotGrid
        sheet.slot_grid = SlotGrid(
            self.config.metadata_zone.slot_grid,
            self.config.detector.board,
        )

    return sheet
```

### 9.5 `SheetRecord` - add `metadata` field

```python
# In src/snap_fit/data_models/sheet_record.py
from snap_fit.aruco.sheet_metadata import SheetMetadata

class SheetRecord(BaseModel):
    ...
    metadata: SheetMetadata | None = None

    @classmethod
    def from_sheet(cls, sheet: Sheet, data_root: Path | None = None) -> SheetRecord:
        ...
        return cls(
            ...
            metadata=sheet.metadata,
        )
```

### 9.6 `PieceRecord` - add `label` field

```python
# In src/snap_fit/data_models/piece_record.py
class PieceRecord(BaseModel):
    ...
    label: str | None = None  # e.g. "A1"

    @classmethod
    def from_piece(cls, piece: Piece) -> PieceRecord:
        ...
        return cls(
            ...
            label=getattr(piece, "label", None),
        )
```

## File touchmap

| File | Change |
|------|--------|
| `src/snap_fit/puzzle/sheet.py` | Add `metadata` and `slot_grid` attributes |
| `src/snap_fit/puzzle/sheet.py` | Use `slot_grid` in `build_pieces()` for label assignment |
| `src/snap_fit/puzzle/piece.py` | Add `label: str \| None` attribute |
| `src/snap_fit/puzzle/sheet_aruco.py` | Decode metadata pre-rectification; attach `slot_grid` |
| `src/snap_fit/data_models/sheet_record.py` | Add `metadata: SheetMetadata \| None` field |
| `src/snap_fit/data_models/piece_record.py` | Add `label: str \| None` field |

## Backward compatibility

All new fields are `None`-defaulted. Existing code paths that do not provide
metadata or slot grids continue to work exactly as before:
- `Sheet` without metadata: `metadata=None`, `slot_grid=None`, no labels assigned
- `SheetRecord` without metadata: `metadata=None` in JSON output
- `PieceRecord` without label: `label=None`

Existing JSON cache files will deserialize correctly since the new fields have
defaults.

## Test strategy

- **Unit: Sheet with metadata:** Create Sheet, set metadata, verify attribute
- **Unit: build_pieces with slot_grid:** Synthetic contours at known positions, verify labels
- **Unit: SheetRecord round-trip:** Serialize with metadata, deserialize, verify
- **Unit: PieceRecord round-trip:** Serialize with label, deserialize, verify
- **Integration: load_sheet with QR:** Compose a board with metadata, save, load via SheetAruco, verify `sheet.metadata`
- **Backward compat:** Load existing cache JSON, verify no errors
- **Test files:** `tests/puzzle/test_sheet.py`, `tests/data_models/test_sheet_record.py`, `tests/data_models/test_piece_record.py`

## Acceptance criteria

- [ ] `sheet.metadata` is populated after `SheetAruco.load_sheet()` on boards with QR
- [ ] `sheet.metadata` is `None` for boards without QR (with warning logged)
- [ ] Pieces get labels when slot grid is available
- [ ] `SheetRecord` and `PieceRecord` serialize/deserialize the new fields
- [ ] All existing tests pass without modification
- [ ] Existing JSON cache files load without error
