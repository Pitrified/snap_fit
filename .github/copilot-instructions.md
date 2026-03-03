# snap_fit - Copilot Instructions

## Project overview

snap_fit is a computer vision project that digitizes and solves physical jigsaw puzzles. It processes photos of puzzle sheets, detects piece contours and edge segments using OpenCV, calibrates spatial scale with ArUco markers, matches interlocking edges by shape similarity, and assembles the solution via a grid-aware solver. Python 3.14, managed with **uv**.

## Running & tooling

```bash
uv run uvicorn snap_fit.webapp.main:app --reload   # run the FastAPI dev server
uv run pytest                                       # run tests
uv run ruff check .                                 # lint (ruff, ALL rules enabled - see ruff.toml)
uv run pyright                                      # type-check (src/ and tests/ only)
```

Credentials live at `~/cred/snap_fit/.env`. See `CONTRIBUTING.md` for the required keys (e.g. `SNAP_FIT_SAMPLE_ENV_VAR`).

## Architecture layers

| Layer         | Path                                         | Role                                                                                                              |
| ------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Web entry     | `src/snap_fit/webapp/main.py`                | `create_app()` FastAPI factory; mounts routers for piece ingestion, puzzle solving, interactive UI, and debug     |
| Routers       | `src/snap_fit/webapp/routers/`               | `piece_ingestion`, `puzzle_solve`, `interactive`, `debug`, `ui` - each maps HTTP endpoints to services            |
| Services      | `src/snap_fit/webapp/services/`              | Business logic called by routers; orchestrates sheet loading, matching, and solving                               |
| Puzzle        | `src/snap_fit/puzzle/`                       | `Sheet`, `Piece`, `SheetManager`, `PieceMatcher`, `PuzzleGenerator`, `PuzzleRasterizer`                           |
| Image         | `src/snap_fit/image/`                        | Contour and segment extraction (`contour.py`, `segment.py`), affine matching (`segment_matcher.py`, `process.py`) |
| Grid / Solver | `src/snap_fit/grid/`, `src/snap_fit/solver/` | `GridModel` (slot types + orientations), `PlacementState`, `NaiveLinearSolver`                                    |
| ArUco         | `src/snap_fit/aruco/`                        | `ArucoDetector`, `ArucoBoard` - marker detection for scale calibration                                            |
| Data models   | `src/snap_fit/data_models/`                  | Pydantic models: `PieceId`, `SegmentId`, `PieceRecord`, `SheetRecord`, `MatchResult`, `BaseModelKwargs`           |
| Config        | `src/snap_fit/config/`                       | Shared enums: `EdgePos`, `CornerPos`, `SegmentShape`; ArUco config types                                          |
| Params        | `src/snap_fit/params/`                       | Singleton `SnapFitParams`; `SnapFitPaths` for all filesystem refs                                                 |

## Key patterns

**`SnapFitParams` singleton**  
Access project-wide config and paths via `get_snap_fit_params()` from `src/snap_fit/params/snap_fit_params.py`. `SnapFitPaths` exposes `root_fol`, `cache_fol`, `data_fol`, `aruco_board_fol`, and `sample_img_fol`.

**`SheetManager` as the central registry**  
`SheetManager` holds all loaded `Sheet` objects keyed by sheet ID. Pass it to `PieceMatcher` for cross-sheet segment matching. Load sheets via `add_sheet()` or `add_sheets()` (glob a folder). Always ensure piece `PieceId.sheet_id` matches the sheet key.

**Segment matching pipeline**  
`SegmentMatcher(seg1, seg2)` estimates an affine transform aligning `seg1` onto `seg2`, then calls `compute_similarity()` which first checks shape compatibility (`SegmentShape`: `IN`/`OUT`/`EDGE`/`WEIRD`) and then returns a float score (lower is better; `1e6` signals an incompatible or missing pair). `PieceMatcher` caches results by `frozenset[SegmentId]`.

**FastAPI app factory**  
`create_app()` in `src/snap_fit/webapp/main.py` builds the app: applies CORS middleware, mounts `/static`, attaches Jinja2 templates to `app.state.templates`, and registers all routers under `/api/v1/`. Use `get_settings()` from `src/snap_fit/webapp/core/settings.py` for environment-driven config.

**`BaseModelKwargs`**  
Config classes extend `BaseModelKwargs` (not plain `BaseModel`) when their fields need to be forwarded as `**kwargs` to a third-party constructor. `to_kw(exclude_none=True)` flattens a nested `kwargs` dict at the top level.

**`GridModel` and orientations**  
`GridModel(rows, cols)` pre-computes slot types (corner / edge / inner) and their required `Orientation` values based on position. Use `grid_model.corners`, `.edges`, `.inners` for iteration, and `_slot_types[pos]` to look up an `OrientedPieceType`.

## Style rules

- Never use em dashes (`--` or `---` or Unicode `—`). Use a hyphen `-` or rewrite the sentence.

## Testing & scratch space

- Tests live in `tests/` (mirrors `src/snap_fit/` structure).
- `scratch_space/` holds numbered exploratory notebooks and scripts (e.g., `aruco_setup/`, `contour_/`, `grid_model/`). These are not part of the package; ruff ignores `ERA001`/`F401`/`T20` there.

## Linting notes

- `ruff.toml` targets Python 3.13 with `select = ["ALL"]`. Key ignores: `COM812`, `D104`, `D203`, `D213`, `D413` (docstring style), `FIX002`/`TD002`/`TD003` (TODO formatting), `RET504`.
- Notebooks (`.ipynb`) additionally ignore `ERA001`, `F401`, `T20`.
- Tests additionally allow `ARG001`, `INP001`, `S101` (assert), `SLF001` (private access), `PLR2004` (magic values).
- `max-args = 10` (pylint); imports use `force-single-line = true`.

## End-of-task verification

After every code change, run the full verification suite before considering the task done:

```bash
uv run pytest && uv run ruff check . && uv run pyright
```
