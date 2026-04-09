# Step 02 - `SheetMetadata` Pydantic Model

> **Status:** not started
> **Target file:** `src/snap_fit/aruco/sheet_metadata.py`
> **Depends on:** nothing

---

## Objective

Create a Pydantic model that represents the identity of a single printed sheet.
This model is the core data payload embedded in QR codes on each board and
attached to `Sheet` / `SheetRecord` after ingestion.

## Data model

```python
from datetime import date

from pydantic import Field

from snap_fit.data_models.base_model_kwargs import BaseModelKwargs


class SheetMetadata(BaseModelKwargs):
    """Identity metadata for a single printed puzzle sheet."""

    tag_name: str                                     # e.g. "oca", "milano1"
    sheet_index: int                                  # 0-based within the print run
    total_sheets: int | None = None                   # may be unknown at print time
    board_config_id: str                              # matches data/aruco_boards/{id}/
    printed_at: date = Field(default_factory=date.today)
```

### QR payload encoding

Compact CSV representation - keep payload under 14 bytes (QR V1 capacity at
ECC-M). Fields are comma-separated, no spaces, date as `YYYYMMDD`:

```python
def to_qr_payload(self) -> str:
    """Encode to compact CSV: 'oca,2,6,oca,20250115'."""
    ts = self.total_sheets if self.total_sheets is not None else ""
    return f"{self.tag_name},{self.sheet_index},{ts},{self.board_config_id},{self.printed_at:%Y%m%d}"

@classmethod
def from_qr_payload(cls, s: str) -> "SheetMetadata":
    """Decode from CSV payload string."""
    parts = s.split(",")
    return cls(
        tag_name=parts[0],
        sheet_index=int(parts[1]),
        total_sheets=int(parts[2]) if parts[2] else None,
        board_config_id=parts[3],
        printed_at=date(int(parts[4][:4]), int(parts[4][4:6]), int(parts[4][6:8])),
    )
```

### Payload size analysis

Example: `oca,2,6,oca,20250115` = 20 chars (fits V1 QR at ECC-L, or V2 at ECC-M).
With `total_sheets=None`: `oca,2,,oca,20250115` = 19 chars.
Worst case with long tag: `sample_puzzle_v2,12,24,sample_puzzle_v2,20260409` = 48 chars - needs V3 or lower ECC.

Consider: If long tags are common, truncate or hash the tag in the QR payload and
use a lookup at decode time. For now, short tags are the norm.

## File touchmap

| File | Change |
|------|--------|
| `src/snap_fit/aruco/sheet_metadata.py` | **NEW** - `SheetMetadata` class |

## Test strategy

- **Round-trip test:** `from_qr_payload(metadata.to_qr_payload()) == metadata`
- **Edge cases:** `total_sheets=None`, single-char tag, max-length tag
- **Payload size assertion:** payload length < 26 bytes for typical tags
- **Test file:** `tests/aruco/test_sheet_metadata.py`

## Acceptance criteria

- [ ] `SheetMetadata` model validates correctly with all field types
- [ ] `to_qr_payload()` produces correct CSV string
- [ ] `from_qr_payload()` round-trips without data loss
- [ ] `total_sheets=None` is handled gracefully in both encode and decode
