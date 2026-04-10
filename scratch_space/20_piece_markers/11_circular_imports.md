# Circular imports and lazy exports

## overview

**Root cause**: `data_models/__init__.py` eagerly imported `SheetRecord`, which imported `SheetMetadata` from `aruco.sheet_metadata`. But sheet_metadata.py imports `data_models.basemodel_kwargs`, which triggers `data_models/__init__.py` to run first - creating a partial-module cycle whenever the notebook imports `snap_fit.aruco.sheet_metadata` as its first `snap_fit` import.

**Fix**: __init__.py - `SheetRecord` is now a lazy export via module `__getattr__`. It's only actually imported when first accessed, by which point sheet_metadata.py is fully initialized. All existing callers (`from snap_fit.data_models import SheetRecord`) continue to work transparently.

could we just move basemodel_kwargs out of data_models and into a more basic utils module that has no dependencies? That would be simpler than the lazy import hack, and would also make it easier to use the basemodel kwargs in non-data-model classes without importing the whole data_models package.

## plan

### Goal

Move `BaseModelKwargs` from `snap_fit.data_models.basemodel_kwargs` into a new `snap_fit.utils.basemodel_kwargs` module that has no `snap_fit` dependencies. This severs the circular chain and lets `data_models/__init__.py` import `SheetRecord` eagerly again, removing the `__getattr__` lazy-export hack.

### Why this is cleaner than the lazy-import hack

The lazy `__getattr__` is an invisible runtime indirection - type checkers and IDEs can miss it, and it leaves the architectural problem (data_models depending on aruco) in place. Moving `BaseModelKwargs` to a dependency-free `utils` layer gives it a home that matches its nature: it is a generic Pydantic helper, not a domain data model.

### Circular chain (current)

```
data_models/__init__.py
  └─ imports SheetRecord (eager, old code) / lazy __getattr__ (current hack)
       └─ sheet_record.py imports SheetMetadata
            └─ aruco/sheet_metadata.py imports BaseModelKwargs
                 └─ data_models/basemodel_kwargs.py
                      └─ triggers data_models/__init__.py  ← CYCLE
```

### After the fix

```
data_models/__init__.py  ← imports SheetRecord eagerly (no cycle)
  └─ sheet_record.py imports SheetMetadata
       └─ aruco/sheet_metadata.py imports BaseModelKwargs
            └─ utils/basemodel_kwargs.py  ← no snap_fit imports at all
```

### Steps

**1. Create `src/snap_fit/utils/__init__.py`**  
Empty file (package marker).

**2. Create `src/snap_fit/utils/basemodel_kwargs.py`**  
Copy the `BaseModelKwargs` class verbatim from `data_models/basemodel_kwargs.py`. The only import it needs is `from pydantic import BaseModel`.

**3. Replace `src/snap_fit/data_models/basemodel_kwargs.py` with a re-export shim**  
Keep the file so existing `from snap_fit.data_models.basemodel_kwargs import BaseModelKwargs` calls continue to work without touching every caller immediately.

```python
# backward-compat shim - import from the canonical location instead
from snap_fit.utils.basemodel_kwargs import BaseModelKwargs

__all__ = ["BaseModelKwargs"]
```

**4. Update the 5 direct callers to import from the new canonical path**  
Each file currently has `from snap_fit.data_models.basemodel_kwargs import BaseModelKwargs`. Change to `from snap_fit.utils.basemodel_kwargs import BaseModelKwargs`.

| File |
|---|
| `src/snap_fit/aruco/sheet_metadata.py` |
| `src/snap_fit/config/aruco/aruco_board_config.py` |
| `src/snap_fit/config/aruco/aruco_detector_config.py` |
| `src/snap_fit/config/aruco/metadata_zone_config.py` |
| `src/snap_fit/config/aruco/sheet_aruco_config.py` |

**5. Restore eager import in `src/snap_fit/data_models/__init__.py`**  
Remove the `__getattr__` function and restore the direct import. Also add `BaseModelKwargs` to the public exports so callers that do `from snap_fit.data_models import BaseModelKwargs` work (none currently do this, but it is the expected place to find it).

```python
from snap_fit.data_models.match_result import MatchResult
from snap_fit.data_models.piece_id import PieceId
from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.data_models.segment_id import SegmentId
from snap_fit.data_models.sheet_record import SheetRecord
from snap_fit.utils.basemodel_kwargs import BaseModelKwargs

__all__ = ["BaseModelKwargs", "MatchResult", "PieceId", "PieceRecord", "SegmentId", "SheetRecord"]
```

### Verification

```bash
uv run pytest && uv run ruff check . && uv run pyright
```

### Optional follow-up (not in this task)

Once all callers have been updated in step 4 and tests pass, `src/snap_fit/data_models/basemodel_kwargs.py` can be deleted entirely - it is only a shim at that point.
