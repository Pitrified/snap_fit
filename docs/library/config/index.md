# `config`

> Module: `src/snap_fit/config/`
> Related tests: `tests/config/`

## Purpose

Shared enumerations and type definitions used throughout snap_fit. Defines the vocabulary for edge positions, corner positions, and segment shapes that all other modules reference.

## Usage

### Minimal example

```python
from snap_fit.config.types import EdgePos, CornerPos, SegmentShape

# Iterate over all edge positions of a piece
for edge in EdgePos:
    print(edge.value)  # "left", "bottom", "right", "top"

# Check a segment shape
if shape == SegmentShape.IN:
    print("This edge has an inward tab")
```

### Edge-to-corner mapping

```python
from snap_fit.config.types import EDGE_ENDS_TO_CORNER, EdgePos

# Get which corners bound the LEFT edge
start_corner, end_corner = EDGE_ENDS_TO_CORNER[EdgePos.LEFT]
# start_corner = CornerPos.TOP_LEFT, end_corner = CornerPos.BOTTOM_LEFT
```

## API Reference

### `CornerPos`

Enum with four values: `TOP_LEFT`, `BOTTOM_LEFT`, `BOTTOM_RIGHT`, `TOP_RIGHT`. Used to identify the four corners of a puzzle piece.

### `EdgePos`

Enum with four values: `LEFT`, `BOTTOM`, `RIGHT`, `TOP`. Used to identify which side of a piece a segment belongs to.

### `SegmentShape`

StrEnum classifying a segment's shape: `IN` (inward tab), `OUT` (outward tab), `EDGE` (flat boundary), `WEIRD` (ambiguous classification).

### `EDGE_ENDS_TO_CORNER`

Dict mapping each `EdgePos` to the tuple of `(start_corner, end_corner)` that bounds it. Used by `Contour.split_contour()` to determine where to split.

## ArUco configs

The `config/aruco/` sub-package contains Pydantic configuration models for ArUco marker detection:

- `ArucoBoardConfig` - board layout (marker count, size, spacing, dictionary)
- `ArucoDetectorConfig` - detector parameters (adaptive threshold settings, rect margin), embeds an `ArucoBoardConfig`
- `SheetArucoConfig` - top-level config for sheet processing (min_area, crop_margin), embeds an `ArucoDetectorConfig`

All three extend `BaseModelKwargs` and can be loaded from JSON files:

```python
from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig

config = SheetArucoConfig.model_validate_json(config_path.read_text())
```

## Common Pitfalls

- **SegmentShape is a StrEnum**: Values are lowercase strings (`"in"`, `"out"`, `"edge"`, `"weird"`), not the uppercase member names. Use `.value` when serializing.
- **EDGE_ENDS_TO_CORNER traversal order**: The corners are listed in the order the contour is traversed (clockwise), not in any spatial sorting order.

## Related Modules

- [`data_models`](../data_models/index.md) - uses `EdgePos` and `CornerPos` in `SegmentId` and `PieceRecord`
- [`image/segment`](../image/segment.md) - uses `SegmentShape` for shape classification
- [`grid/orientation`](../grid/orientation.md) - maps flat `EdgePos` values to piece orientations
