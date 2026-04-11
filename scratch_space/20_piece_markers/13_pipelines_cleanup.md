# Pipelines cleanup

## Overview

spread in `scratch_space` there are some notebooks with code snippets that are useful to generate boards, ingest sheets, and in general interact with the codebase

we want to audit them and move any core functionality notebook into the `pipelines` directory

1. Identify notebooks in `scratch_space` that contain reusable code snippets or core functionality related to piece markers, board generation, or sheet ingestion, or other useful things
1. plan for moving them into `pipelines` with proper structure, naming (`01_feature, 02_name`), and documentation

## Audit

27 notebooks + 1 standalone script found across 16 subdirectories. Each notebook was read and classified as PIPELINE (reusable workflow), EXPLORATION (R&D/debugging), or MIXED (some reusable parts embedded in exploration).

### aruco_setup/

| Notebook                        | Classification | Summary                                                                                                         |
| ------------------------------- | -------------- | --------------------------------------------------------------------------------------------------------------- |
| `01_aruco_experiments.ipynb`    | EXPLORATION    | Raw cv2 ArUco GridBoard construction experiments, ring layout filtering. No snap_fit imports.                   |
| `02_verify_package.ipynb`       | EXPLORATION    | Validates `snap_fit.aruco` and `snap_fit.puzzle.sheet_aruco` modules; tests detector on distorted images.       |
| `03_generate_aruco_board.ipynb` | PIPELINE       | Board generation with `ArucoBoardGenerator`; saves config and image to `data_fol/aruco_boards/{tag}/`.          |
| `04_load_sheets.ipynb`          | PIPELINE       | Complete sheet ingestion: loads images with `SheetAruco`, detects ArUco, extracts pieces. Full ingest pipeline. |

### contour\_/

| Notebook               | Classification | Summary                                                                                                       |
| ---------------------- | -------------- | ------------------------------------------------------------------------------------------------------------- |
| `01_match_.ipynb`      | PIPELINE       | Segment matching workflow: loads sheets, splits contours into edges, matches segments using `SegmentMatcher`. |
| `02_match_debug.ipynb` | EXPLORATION    | Debug matching: detailed analysis of segment shape computation, affine transforms, corner indexing.           |

### contour_split_ellipse/

| Notebook           | Classification | Summary                                                                       |
| ------------------ | -------------- | ----------------------------------------------------------------------------- |
| `01_explore.ipynb` | EXPLORATION    | Data exploration for splitting contours via ellipse fitting. Legacy research. |

### opencv\_/

| Notebook                  | Classification | Summary                                                                                                        |
| ------------------------- | -------------- | -------------------------------------------------------------------------------------------------------------- |
| `01_shaper_.ipynb`        | EXPLORATION    | CV2 indexing exploration; corner/region visualization; debugging image coordinate systems.                     |
| `02_ingest_.ipynb`        | EXPLORATION    | Image ingestion example with contour extraction, but too exploratory & outdated for pipeline use.              |
| `sample_load.py` (script) | EXPLORATION    | Standalone script demonstrating image loading, thresholding, erosion, dilation. Superseded by `image.process`. |

### segment_shape/

| Notebook                 | Classification | Summary                                                                                            |
| ------------------------ | -------------- | -------------------------------------------------------------------------------------------------- |
| `01_segment_shape.ipynb` | EXPLORATION    | Explores segment shape classification logic (IN/OUT/EDGE/WEIRD) based on contour point thresholds. |

### segment_id_model/

| Notebook              | Classification | Summary                                                                                                    |
| --------------------- | -------------- | ---------------------------------------------------------------------------------------------------------- |
| `01_segment_id.ipynb` | EXPLORATION    | Prototype of `SegmentId` Pydantic model (frozen, hashable). Already ported to `src/snap_fit/data_models/`. |
| `02_usage.ipynb`      | PIPELINE       | Demonstrates `SegmentId` usage with serialization, set operations, dict keys. Good reference notebook.     |

### piece_matcher/

| Notebook                 | Classification | Summary                                                                                               |
| ------------------------ | -------------- | ----------------------------------------------------------------------------------------------------- |
| `01_piece_matcher.ipynb` | EXPLORATION    | Prototype `PieceMatcher` and `MatchResult` classes. Already ported to `src/snap_fit/puzzle/`.         |
| `02_usage.ipynb`         | PIPELINE       | Complete matching workflow: load sheets, initialize `PieceMatcher`, run `match_all()`, query results. |

### sheet_manager/

| Notebook             | Classification | Summary                                                                                                   |
| -------------------- | -------------- | --------------------------------------------------------------------------------------------------------- |
| `01_prototype.ipynb` | EXPLORATION    | Prototype `SheetManager` class with add/glob/access methods. Already ported to `src/snap_fit/puzzle/`.    |
| `02_usage.ipynb`     | PIPELINE       | Complete usage: load sheets via glob, save metadata/contours, persist matches. Real persistence workflow. |

### grid_model/

| Notebook              | Classification | Summary                                                                                                           |
| --------------------- | -------------- | ----------------------------------------------------------------------------------------------------------------- |
| `01_grid_model.ipynb` | PIPELINE       | `GridModel` tutorial: orientation arithmetic, piece classification, rotation computation, canonical orientations. |
| `02_scoring.ipynb`    | PIPELINE       | Demonstrates `score_edge()` and `score_grid()` functions; validates neighbor alignment scoring.                   |

### puzzle_generator/

| Notebook                    | Classification | Summary                                                                                             |
| --------------------------- | -------------- | --------------------------------------------------------------------------------------------------- |
| `01_puzzle_generator.ipynb` | PIPELINE       | `PuzzleGenerator` introduction: config, label generation, piece creation, SVG output.               |
| `02_usage.ipynb`            | PIPELINE       | Full workflow: configure generator, create pieces, export SVG, rasterize to image.                  |
| `03_generate_sheets.ipynb`  | PIPELINE       | Full pipeline: generate puzzle config, create pieces, compose onto board image, export final sheet. |

### naive_linear_solver/

| Notebook             | Classification | Summary                                                                                |
| -------------------- | -------------- | -------------------------------------------------------------------------------------- |
| `01_prototype.ipynb` | PIPELINE       | Complete `NaiveLinearSolver` implementation with visualization and debugging.          |
| `02_usage.ipynb`     | PIPELINE       | Solver usage: initialize from sheets, run solve, inspect results, visualize placement. |

### feature_sample/

| Notebook          | Classification | Summary                                                  |
| ----------------- | -------------- | -------------------------------------------------------- |
| `01_sample.ipynb` | EXPLORATION    | Minimal stub notebook for feature development templates. |

### fastapi_scaffold/

| Notebook                | Classification | Summary                                                                                            |
| ----------------------- | -------------- | -------------------------------------------------------------------------------------------------- |
| `01_db_ingestion.ipynb` | EXPLORATION    | Strategic planning for SQLite data ingestion layer. Not runnable code - analysis and design notes. |

### weird_edge_shape_detection/

| Notebook                    | Classification | Summary                                                                                                   |
| --------------------------- | -------------- | --------------------------------------------------------------------------------------------------------- |
| `01_data_exploration.ipynb` | EXPLORATION    | Root-cause analysis of WEIRD shape prevalence; visualizes failure modes; proposes adaptive threshold fix. |

### 20_piece_markers/

| Notebook          | Classification | Summary                                                                                                                       |
| ----------------- | -------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `00_sample.ipynb` | PIPELINE       | Sheet metadata, QR code generation/decoding, slot grid labeling with `MetadataZoneConfig`, `SheetMetadata`, `QRChunkHandler`. |

### Classification summary

- **PIPELINE**: 16 notebooks
- **EXPLORATION**: 11 notebooks + 1 script
- Total: 27 notebooks + 1 script across 16 directories

## Plan

### Proposed `pipelines/` structure

Group pipeline notebooks by workflow domain, numbered for ordering. Each notebook should be self-contained and runnable top-to-bottom.

```
pipelines/
  01_board_generation/
    01_generate_aruco_board.ipynb    <- aruco_setup/03_generate_aruco_board.ipynb
  02_sheet_ingestion/
    01_load_sheets.ipynb             <- aruco_setup/04_load_sheets.ipynb
    02_sheet_manager.ipynb           <- sheet_manager/02_usage.ipynb
  03_segment_matching/
    01_segment_matching.ipynb        <- contour_/01_match_.ipynb
    02_piece_matcher.ipynb           <- piece_matcher/02_usage.ipynb
  04_grid_and_solver/
    01_grid_model.ipynb              <- grid_model/01_grid_model.ipynb
    02_grid_scoring.ipynb            <- grid_model/02_scoring.ipynb
    03_naive_solver.ipynb            <- naive_linear_solver/02_usage.ipynb
  05_puzzle_generation/
    01_puzzle_generator.ipynb        <- puzzle_generator/01_puzzle_generator.ipynb
    02_rasterize.ipynb               <- puzzle_generator/02_usage.ipynb
    03_generate_sheets.ipynb         <- puzzle_generator/03_generate_sheets.ipynb
  06_data_models/
    01_segment_id.ipynb              <- segment_id_model/02_usage.ipynb
  07_sheet_identity/
    01_piece_markers.ipynb           <- 20_piece_markers/00_sample.ipynb
```

### Mapping table

| Pipeline path                                       | Source                                       | Action                                            |
| --------------------------------------------------- | -------------------------------------------- | ------------------------------------------------- |
| `01_board_generation/01_generate_aruco_board.ipynb` | `aruco_setup/03_generate_aruco_board.ipynb`  | Copy, clean up cell outputs, add markdown headers |
| `02_sheet_ingestion/01_load_sheets.ipynb`           | `aruco_setup/04_load_sheets.ipynb`           | Copy, clean up, add markdown headers              |
| `02_sheet_ingestion/02_sheet_manager.ipynb`         | `sheet_manager/02_usage.ipynb`               | Copy, clean up, add markdown headers              |
| `03_segment_matching/01_segment_matching.ipynb`     | `contour_/01_match_.ipynb`                   | Copy, clean up, add markdown headers              |
| `03_segment_matching/02_piece_matcher.ipynb`        | `piece_matcher/02_usage.ipynb`               | Copy, clean up, add markdown headers              |
| `04_grid_and_solver/01_grid_model.ipynb`            | `grid_model/01_grid_model.ipynb`             | Copy, clean up, add markdown headers              |
| `04_grid_and_solver/02_grid_scoring.ipynb`          | `grid_model/02_scoring.ipynb`                | Copy, clean up, add markdown headers              |
| `04_grid_and_solver/03_naive_solver.ipynb`          | `naive_linear_solver/02_usage.ipynb`         | Copy, clean up, add markdown headers              |
| `05_puzzle_generation/01_puzzle_generator.ipynb`    | `puzzle_generator/01_puzzle_generator.ipynb` | Copy, clean up, add markdown headers              |
| `05_puzzle_generation/02_rasterize.ipynb`           | `puzzle_generator/02_usage.ipynb`            | Copy, clean up, add markdown headers              |
| `05_puzzle_generation/03_generate_sheets.ipynb`     | `puzzle_generator/03_generate_sheets.ipynb`  | Copy, clean up, add markdown headers              |
| `06_data_models/01_segment_id.ipynb`                | `segment_id_model/02_usage.ipynb`            | Copy, clean up, add markdown headers              |
| `07_sheet_identity/01_piece_markers.ipynb`          | `20_piece_markers/00_sample.ipynb`           | Copy, clean up, add markdown headers              |

### Notebooks NOT moved (and why)

| Notebook                                               | Reason                                                        |
| ------------------------------------------------------ | ------------------------------------------------------------- |
| `aruco_setup/01_aruco_experiments.ipynb`               | Pure exploration, no snap_fit imports                         |
| `aruco_setup/02_verify_package.ipynb`                  | Verification/debugging, not a workflow                        |
| `contour_/02_match_debug.ipynb`                        | Debug-only analysis                                           |
| `contour_split_ellipse/01_explore.ipynb`               | Legacy research, not integrated                               |
| `opencv_/01_shaper_.ipynb`                             | CV2 coordinate debugging                                      |
| `opencv_/02_ingest_.ipynb`                             | Outdated, superseded by sheet ingestion pipeline              |
| `opencv_/sample_load.py`                               | Superseded by `image.process` module                          |
| `segment_shape/01_segment_shape.ipynb`                 | Exploration of classification logic                           |
| `segment_id_model/01_segment_id.ipynb`                 | Prototype, already ported to src                              |
| `piece_matcher/01_piece_matcher.ipynb`                 | Prototype, already ported to src                              |
| `sheet_manager/01_prototype.ipynb`                     | Prototype, already ported to src                              |
| `naive_linear_solver/01_prototype.ipynb`               | Large prototype; `02_usage.ipynb` is cleaner for pipeline use |
| `feature_sample/01_sample.ipynb`                       | Stub template                                                 |
| `fastapi_scaffold/01_db_ingestion.ipynb`               | Planning doc, not runnable code                               |
| `weird_edge_shape_detection/01_data_exploration.ipynb` | Debugging/root-cause analysis                                 |

### Cleanup steps per notebook

For each notebook moved to `pipelines/`:

1. Strip cell outputs (`uv run nbstripout <notebook>`)
2. Add a top markdown cell with: title, purpose, prerequisites, expected outputs
3. Verify imports resolve (run top-to-bottom)
4. Remove any hardcoded absolute paths (use `get_snap_fit_paths()` instead)
5. Add a `pipelines/README.md` with an index of all pipeline notebooks and their purpose

### Execution order (end-to-end workflow)

The pipeline folders are numbered to reflect the natural execution order for processing a real puzzle:

1. **Board generation** - create ArUco board config and print sheet
2. **Sheet ingestion** - photograph pieces on sheets, load and detect ArUco, extract pieces
3. **Segment matching** - match edges between pieces across sheets
4. **Grid and solver** - define grid model, score placements, solve puzzle
5. **Puzzle generation** - (synthetic) generate test puzzles for validation
6. **Data models** - reference notebooks for data model usage
7. **Sheet identity** - QR-based sheet metadata and slot labeling
