# `puzzle`

> Module: `src/snap_fit/puzzle/`
> Related tests: `tests/puzzle/`

## Purpose

The puzzle subpackage is the core domain layer of snap_fit. It handles loading photos of puzzle sheets, detecting individual pieces and their contours, matching interlocking edges between pieces, and generating synthetic puzzles for testing.

## Submodule Overview

| Module | Description |
|--------|-------------|
| [`sheet`](sheet.md) | Loads a photo, preprocesses it, and detects piece contours |
| [`piece`](piece.md) | Represents a single puzzle piece with corners, segments, and orientation |
| [`sheet_manager`](sheet_manager.md) | Central registry holding all loaded sheets and pieces |
| [`piece_matcher`](piece_matcher.md) | Matches segments across pieces and caches similarity scores |
| [`sheet_aruco`](sheet_aruco.md) | ArUco-based perspective correction before piece detection |
| [`puzzle_config`](puzzle_config.md) | Configuration models for synthetic puzzle generation |
| [`puzzle_generator`](puzzle_generator.md) | Generates jigsaw puzzle geometry as SVG |
| [`puzzle_rasterizer`](puzzle_rasterizer.md) | Rasterizes SVG puzzles into OpenCV-compatible numpy arrays |

## Typical Workflow

```python
from pathlib import Path
from snap_fit.puzzle.sheet import Sheet
from snap_fit.puzzle.sheet_manager import SheetManager
from snap_fit.puzzle.piece_matcher import PieceMatcher

# 1. Load sheets
manager = SheetManager()
sheet = Sheet(img_fp=Path("data/sample/sheet_01.jpg"))
manager.add_sheet(sheet, "sheet_01")

# 2. Match all segments
matcher = PieceMatcher(manager)
matcher.match_all()

# 3. Get best matches
top_matches = matcher.get_top_matches(n=20)
for m in top_matches:
    print(f"{m.seg_id1} <-> {m.seg_id2}: {m.similarity:.2f}")
```

## Related Modules

- [`image`](../image/index.md) - contour and segment extraction used by Sheet and Piece
- [`grid`](../grid/index.md) - grid model and orientations used for piece type classification
- [`solver`](../solver/index.md) - consumes SheetManager and PieceMatcher to solve puzzles
- [`config`](../config/index.md) - EdgePos, CornerPos, SegmentShape enums used throughout
