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

---

## Library - by submodule

Status values: `missing` · `stub` · `draft` · `complete`

### puzzle/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| puzzle (overview) | library/puzzle/index.md | missing | - | SheetManager, Piece, Sheet relationships |
| puzzle/sheet | library/puzzle/sheet.md | missing | - | |
| puzzle/sheet_manager | library/puzzle/sheet_manager.md | missing | - | High priority - central registry |
| puzzle/piece | library/puzzle/piece.md | missing | - | |
| puzzle/piece_matcher | library/puzzle/piece_matcher.md | missing | - | High priority - matching pipeline |
| puzzle/sheet_aruco | library/puzzle/sheet_aruco.md | missing | - | |
| puzzle/puzzle_generator | library/puzzle/puzzle_generator.md | missing | - | |
| puzzle/puzzle_rasterizer | library/puzzle/puzzle_rasterizer.md | missing | - | |
| puzzle/puzzle_config | library/puzzle/puzzle_config.md | missing | - | |

### image/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| image (overview) | library/image/index.md | missing | - | |
| image/contour | library/image/contour.md | missing | - | |
| image/segment | library/image/segment.md | missing | - | |
| image/segment_matcher | library/image/segment_matcher.md | missing | - | High priority - affine matching |
| image/process | library/image/process.md | missing | - | |
| image/shape_detector | library/image/shape_detector.md | missing | - | |

### grid/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| grid (overview) | library/grid/index.md | missing | - | |
| grid/grid_model | library/grid/grid_model.md | missing | - | High priority |
| grid/placement_state | library/grid/placement_state.md | missing | - | |
| grid/orientation | library/grid/orientation.md | missing | - | |
| grid/scoring | library/grid/scoring.md | missing | - | |
| grid/types | library/grid/types.md | missing | - | |

### solver/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| solver (overview) | library/solver/index.md | missing | - | |
| solver/naive_linear_solver | library/solver/naive_linear_solver.md | missing | - | |

### aruco/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| aruco (overview) | library/aruco/index.md | missing | - | |
| aruco/detector | library/aruco/detector.md | missing | - | |
| aruco/board | library/aruco/board.md | missing | - | |

### config/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| config (overview) | library/config/index.md | missing | - | EdgePos, CornerPos, SegmentShape |

### data_models/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| data_models (overview) | library/data_models/index.md | missing | - | PieceId, SegmentId, records, MatchResult |

### params/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| params (overview) | library/params/index.md | missing | - | SnapFitParams singleton, SnapFitPaths |

### persistence/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| persistence (overview) | library/persistence/index.md | missing | - | |

### webapp/

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| webapp (overview) | library/webapp/index.md | missing | - | FastAPI app factory, routers, services |

---

## Coverage summary

- Total modules tracked: 35
- Complete: 0
- In progress (stub/draft): 0
- Missing: 35
