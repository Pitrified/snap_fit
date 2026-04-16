# docs/index.md - Documentation Catalog

> **LLM-maintained file.** Update status, path, and last-updated fields whenever a doc page is
> created, changed, or confirmed stale. Append new rows; never delete rows for missing modules
> (mark them `missing` instead). Use `docs/log.md` for the change narrative.

---

## Guides

| Guide | Path | Status | Last updated | Notes |
|-------|------|--------|--------------|-------|
| Getting started | guides/getting_started.md | complete | 2026-04-07 | Do not edit directly |
| FastAPI webapp | guides/fastapi.md | complete | 2026-04-07 | |
| Updating docs | guides/update_docs.md | complete | 2026-04-07 | Meta guide for this workflow |
| Coordinate spaces | guides/coordinate_spaces.md | complete | 2026-04-16 | Image cropping, slot assignment, 4 coordinate spaces |

---

## Library - by submodule

Status values: `missing` · `stub` · `draft` · `complete`

### puzzle/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| puzzle (overview) | library/puzzle/index.md | complete | 2026-04-07 | SheetManager, Piece, Sheet relationships |
| puzzle/sheet | library/puzzle/sheet.md | complete | 2026-04-07 | |
| puzzle/sheet_manager | library/puzzle/sheet_manager.md | complete | 2026-04-07 | Central registry |
| puzzle/piece | library/puzzle/piece.md | complete | 2026-04-07 | |
| puzzle/piece_matcher | library/puzzle/piece_matcher.md | complete | 2026-04-07 | Matching pipeline |
| puzzle/sheet_aruco | library/puzzle/sheet_aruco.md | complete | 2026-04-07 | |
| puzzle/puzzle_generator | library/puzzle/puzzle_generator.md | complete | 2026-04-07 | |
| puzzle/puzzle_rasterizer | library/puzzle/puzzle_rasterizer.md | complete | 2026-04-07 | |
| puzzle/puzzle_config | library/puzzle/puzzle_config.md | complete | 2026-04-07 | |

### image/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| image (overview) | library/image/index.md | complete | 2026-04-07 | |
| image/contour | library/image/contour.md | complete | 2026-04-07 | |
| image/segment | library/image/segment.md | complete | 2026-04-07 | |
| image/segment_matcher | library/image/segment_matcher.md | complete | 2026-04-07 | Affine matching |
| image/process | library/image/process.md | complete | 2026-04-07 | |
| image/shape_detector | library/image/shape_detector.md | complete | 2026-04-07 | |

### grid/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| grid (overview) | library/grid/index.md | complete | 2026-04-07 | |
| grid/grid_model | library/grid/grid_model.md | complete | 2026-04-07 | |
| grid/placement_state | library/grid/placement_state.md | complete | 2026-04-07 | |
| grid/orientation | library/grid/orientation.md | complete | 2026-04-07 | |
| grid/scoring | library/grid/scoring.md | complete | 2026-04-07 | |
| grid/types | library/grid/types.md | complete | 2026-04-07 | |

### solver/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| solver (overview) | library/solver/index.md | complete | 2026-04-07 | |
| solver/naive_linear_solver | library/solver/naive_linear_solver.md | complete | 2026-04-07 | |

### aruco/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| aruco (overview) | library/aruco/index.md | complete | 2026-04-07 | |
| aruco/detector | library/aruco/detector.md | complete | 2026-04-07 | |
| aruco/board | library/aruco/board.md | complete | 2026-04-07 | |

### config/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| config (overview) | library/config/index.md | complete | 2026-04-07 | EdgePos, CornerPos, SegmentShape, ArUco configs |

### data_models/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| data_models (overview) | library/data_models/index.md | complete | 2026-04-07 | PieceId, SegmentId, records, MatchResult, BaseModelKwargs |

### params/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| params (overview) | library/params/index.md | complete | 2026-04-07 | SnapFitParams singleton, SnapFitPaths |

### persistence/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| persistence (overview) | library/persistence/index.md | complete | 2026-04-07 | SQLite DatasetStore |

### webapp/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| webapp (overview) | library/webapp/index.md | complete | 2026-04-07 | FastAPI app factory, routers, services |

---

## Coverage summary

- Total modules tracked: 35
- Complete: 35
- In progress (stub/draft): 0
- Missing: 0
