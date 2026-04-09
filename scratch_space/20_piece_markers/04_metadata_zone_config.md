# Step 04 - `MetadataZoneConfig` + `SlotGridConfig`

> **Status:** not started
> **Target files:** `src/snap_fit/config/aruco/metadata_zone_config.py`, `src/snap_fit/config/aruco/sheet_aruco_config.py`
> **Depends on:** nothing

---

## Objective

Define Pydantic config models that control the QR metadata strip and slot grid
on generated board images. These are pure data models with no rendering logic.

## Data models

### `SlotGridConfig`

```python
from pydantic import Field

from snap_fit.data_models.base_model_kwargs import BaseModelKwargs


class SlotGridConfig(BaseModelKwargs):
    """Defines a grid of piece slots within the board interior."""

    cols: int = Field(default=8)
    rows: int = Field(default=6)
    label_inset_px: int = Field(default=4)
```

### `MetadataZoneConfig`

```python
from typing import Literal

from pydantic import Field

from snap_fit.data_models.base_model_kwargs import BaseModelKwargs


class MetadataZoneConfig(BaseModelKwargs):
    """Controls QR strip and slot grid on generated board images."""

    enabled: bool = True
    qr_n_codes: int = 3
    qr_ecc: Literal["L", "M", "Q", "H"] = "M"
    text_enabled: bool = True
    slot_grid: SlotGridConfig = Field(default_factory=SlotGridConfig)
```

### Integration with `SheetArucoConfig`

Add optional field to existing config:

```python
# In src/snap_fit/config/aruco/sheet_aruco_config.py
class SheetArucoConfig(BaseModelKwargs):
    min_area: int = 80_000
    crop_margin: int | float | None = None
    detector: ArucoDetectorConfig
    metadata_zone: MetadataZoneConfig | None = None   # <-- NEW
```

When `metadata_zone` is `None`, all existing behavior is unchanged. This is a
fully backward-compatible addition.

### Sample JSON config

```json
{
    "min_area": 80000,
    "detector": { "...": "..." },
    "metadata_zone": {
        "enabled": true,
        "qr_n_codes": 3,
        "qr_ecc": "M",
        "text_enabled": true,
        "slot_grid": {
            "cols": 8,
            "rows": 6,
            "label_inset_px": 4
        }
    }
}
```

## File touchmap

| File | Change |
|------|--------|
| `src/snap_fit/config/aruco/metadata_zone_config.py` | **NEW** - `SlotGridConfig`, `MetadataZoneConfig` |
| `src/snap_fit/config/aruco/sheet_aruco_config.py` | Add `metadata_zone: MetadataZoneConfig \| None = None` field |

## Test strategy

- **Default construction:** `MetadataZoneConfig()` uses sensible defaults
- **JSON round-trip:** `model_validate_json(model.model_dump_json())` round-trips
- **Backward compat:** `SheetArucoConfig` without `metadata_zone` still works
- **Test file:** `tests/config/test_metadata_zone_config.py`

## Acceptance criteria

- [ ] Both models validate and serialize correctly
- [ ] `SheetArucoConfig` accepts `metadata_zone=None` (default) with no behavior change
- [ ] Existing JSON configs (e.g. `oca_SheetArucoConfig.json`) still load without error
