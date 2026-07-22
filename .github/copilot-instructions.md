# snap_fit - Copilot Instructions

## Project overview

snap_fit is a computer vision project that digitizes and solves physical jigsaw puzzles. It processes photos of puzzle sheets, detects piece contours and edge segments using OpenCV, calibrates spatial scale with ArUco markers, matches interlocking edges by shape similarity, and assembles the solution via a grid-aware solver. Python 3.14, managed with **uv**.

## Running & tooling

```bash
uv run uvicorn snap_fit.webapp.main:app --reload   # run the FastAPI dev server
uv run pytest                                       # run tests
uv run ruff check .                                 # lint (ruff, ALL rules enabled - see ruff.toml)
uv run pyright                                      # type-check (src/, tests/, scripts/)
make lint                                           # ruff check + ruff format --check + pyright (mirrors pre-commit)
uv run pre-commit run --all-files                # run pre-commit hooks (ruff, black, isort, nbstripout, etc)
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

## Coordinate spaces and image cropping

When working on piece image cropping, slot assignment, or overlay visualization, always consult [docs/guides/coordinate_spaces.md](../../docs/guides/coordinate_spaces.md). Key rules:

- The pipeline has four coordinate spaces: board-image, object-coord, rectified, and cropped-sheet. Piece coordinates (`sheet_origin`, `contour_region`, `padded_size`) are in **cropped-sheet** space.
- Never apply cropped-sheet coordinates to the original photo. Load the processed sheet image from `cache/{tag}/sheets/{sheet_id}.jpg` instead.
- `SlotGrid` works in board-image space. Convert via `Sheet.crop_offset` before/after calling `slot_for_centroid()` or `slot_centers()`.

## Style rules

- Never use em dashes (`--` or `---` or Unicode `\u2014` and `\u2013`). Use a hyphen `-` or rewrite the sentence.

## Testing & scratch space

- Tests live in `tests/` (mirrors `src/snap_fit/` structure).
- `scratch_space/` holds numbered exploratory notebooks and scripts (e.g., `aruco_setup/`, `contour_/`, `grid_model/`). These are not part of the package; ruff ignores `ERA001`/`F401`/`T20` there.
- `pipelines/` holds current, trusted, one-job workflows (the maintained counterpart to `scratch_space/`). See `pipelines/README.md`.

## Notebooks (any `.ipynb`, in pipelines or scratch)

Applies to every agent working with notebooks in this repo, so notebook edits stay clean instead of becoming malformed JSON or a pile of `nbconvert` runs.

- Live work goes through the VS Code notebook MCP server (`notebook_list_cells`, `notebook_insert_cell`, `notebook_edit_cell`, `notebook_run_cell`, `notebook_get_cell_output`, ...): structured cell operations against the running kernel, with the notebook open in VS Code.
- When no notebook/kernel is open, use the native `NotebookEdit` tool for structural cell edits.
- Never hand-edit `.ipynb` JSON with a text editor, and do not shell out to `nbconvert` to author or run notebooks unless necessary.
- Clean outputs before committing with `make nbstrip` (the `nbstripout` pre-commit hook only verifies and blocks a dirty commit, it does not strip). In-editor, the MCP `notebook_clear_all_outputs` is the equivalent.

## Linting notes

- `ruff.toml` targets Python 3.13 with `select = ["ALL"]`. Key ignores: `COM812`, `D104`, `D203`, `D213`, `D413` (docstring style), `FIX002`/`TD002`/`TD003` (TODO formatting), `RET504`.
- Notebooks (`.ipynb`) additionally ignore `ERA001`, `F401`, `T20`. Scratch notebooks (`scratch_space/**/*.ipynb`) are excluded from ruff entirely; pipeline notebooks are linted.
- Tests additionally allow `ARG001`, `INP001`, `S101` (assert), `SLF001` (private access), `PLR2004` (magic values).
- `scripts/` allows `INP001`, `T20`, `S102`, `BLE001` (CLI utilities); it is in the pyright include.
- `max-args = 10` (pylint); imports use `force-single-line = true`.
- The scope is shared: `make lint`, the pre-commit ruff/ruff-format/pyright hooks, and the editor all read `ruff.toml` and `[tool.pyright]`, so they report the same thing. The pre-commit ruff hooks use `types_or: [python, pyi, jupyter]`.

## End-of-task verification

After every code change, run the full verification suite before considering the task done:

```bash
uv run pytest && uv run ruff check . && uv run pyright && uv run pre-commit run --all-files
# make nbstrip  # strip outputs from tracked notebooks before committing (see Notebooks section)
```
