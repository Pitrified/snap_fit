# `puzzle/piece`

> Module: `src/snap_fit/puzzle/piece.py`
> Related tests: `tests/puzzle/`

## Purpose

Represents a single puzzle piece extracted from a sheet photo. A `Piece` holds the cropped image data, its contour, detected corners, four edge segments, and its classified `OrientedPieceType` (corner, edge, or inner with orientation).

## Usage

### Creating a piece from a contour

```python
from snap_fit.puzzle.piece import Piece

# Typically created by Sheet.build_pieces(), but can be constructed directly:
piece = Piece.from_contour(
    contour=contour_obj,
    full_img_orig=sheet.img_orig,
    full_img_bw=sheet.img_bw,
    img_fp=sheet.img_fp,
    piece_id=PieceId(sheet_id="s1", piece_id=0),
    pad=30,
)

# Access segments
for edge_pos, segment in piece.segments.items():
    print(f"{edge_pos.value}: shape={segment.shape}")

# Check piece classification
print(piece.oriented_piece_type)  # e.g. "CORNER@0deg"
print(piece.flat_edges)           # e.g. [EdgePos.TOP, EdgePos.LEFT]
```

### Accessing segments with rotation

```python
from snap_fit.grid.orientation import Orientation

# Get the segment that would be at TOP after rotating the piece 90 degrees
seg = piece.get_segment_at(EdgePos.TOP, rotation=Orientation.DEG_90)
```

## API Reference

### `Piece`

Holds image data and geometric metadata for a single puzzle piece.

Key attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `piece_id` | `PieceId` | Unique identifier |
| `contour` | `Contour` | The piece's contour with corner/segment data |
| `segments` | `dict[EdgePos, Segment]` | Four edge segments (LEFT, BOTTOM, RIGHT, TOP) |
| `corners` | `dict[CornerPos, tuple[int, int]]` | Four corner coordinates |
| `oriented_piece_type` | `OrientedPieceType` | Classification (CORNER/EDGE/INNER + orientation) |
| `flat_edges` | `list[EdgePos]` | Which edges are flat (boundary edges) |
| `img_orig` | `np.ndarray` | Cropped original color image |
| `img_bw` | `np.ndarray` | Cropped binary image |

Key methods:

- `from_contour(...)` - classmethod to create a piece by cutting from the full sheet image
- `get_segment_at(edge_pos, rotation)` - get the segment at a position accounting for rotation

### `PieceRaw`

Lightweight dataclass with just `contour`, `region`, and `area` (not used in the main pipeline).

## Common Pitfalls

- **Corner detection uses diagonal cross mask**: The `build_cross_masked()` method creates a thick X-shaped mask. Corner detection sweeps from each image corner inward along the diagonal. If pieces are positioned near image edges, corners may be misdetected.
- **Segment shapes depend on corner accuracy**: If corners are incorrectly located, segments will include points from the wrong edge, leading to incorrect `SegmentShape` classification.
- **pad parameter**: The `from_contour` classmethod adds padding around the bounding rectangle. Too little padding can clip piece geometry; too much wastes memory.

## Related Modules

- [`puzzle/sheet`](sheet.md) - creates Piece objects via `build_pieces()`
- [`image/contour`](../image/contour.md) - the `Contour` class that holds raw contour data
- [`image/segment`](../image/segment.md) - the `Segment` class for each edge
- [`grid/orientation`](../grid/orientation.md) - `OrientedPieceType` classification
- [`data_models`](../data_models/index.md) - `PieceRecord.from_piece()` for persistence
