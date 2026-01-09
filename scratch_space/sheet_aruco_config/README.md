# Sheet aruco config

## Overview

This planning artifact describes options to introduce a `SheetArucoConfig` (Pydantic) and the precise set
of repository "users" (files/tests/notebooks/docs) that must be found and updated for a refactor.

Implementation approaches (pick one):

- Option A — New `SheetArucoConfig` (recommended)

  - What: Create `SheetArucoConfig` containing `min_area`, `crop_margin`, and an embedded `ArucoDetectorConfig`.
  - Change: `SheetAruco.__init__(..., config: SheetArucoConfig)` and remove `min_area` from `load_sheet` signature.
  - Pros: Clean, single source of truth for sheet-related params; easy to pass config around.
  - Cons: Requires updating all call sites and tests at once.

- Option B — Wrapper + backwards compat

  - What: Add `SheetArucoConfig` but allow `SheetAruco.__init__` to accept either `ArucoDetectorConfig` or `SheetArucoConfig`.
  - Change: `load_sheet` keeps `min_area` for one release (deprecated), while new code reads from `config`.
  - Pros: Lower-risk rollout; callers can migrate gradually.
  - Cons: More branching logic; longer deprecation window.

- Option C — Minimal API change (deprecate param only)
  - What: Keep current public API; add a `SheetArucoConfig` for future use but do not change `load_sheet` now.
  - Change: Add config class and docs; migrate internals later.
  - Pros: Lowest immediate churn.
  - Cons: Defers work and keeps inconsistent APIs longer.

Choose one option before continuing. Below is a full, precise plan for Option A (the more comprehensive refactor). If you prefer Option B or C, I will adapt the plan after you pick.

## Plan

The following is a sequential, actionable checklist to implement Option A. Each task is small and verifiable.

1. Create feature branch `feat/sheet-aruco-config` (developer action).
2. Add new Pydantic model file `src/snap_fit/config/aruco/sheet_aruco_config.py` defining:

- `min_area: int`
- `crop_margin: int | float`
- `detector: ArucoDetectorConfig`

3. Update `src/snap_fit/puzzle/sheet_aruco.py`:

- Add import for `SheetArucoConfig`.
- Change `__init__` to accept `config: SheetArucoConfig` and store it on `self.config`.
- Change `load_sheet(self, img_fp: Path, min_area: int = 80_000) -> Sheet` to `load_sheet(self, img_fp: Path) -> Sheet`.
- Replace any uses of local `min_area` with `self.config.min_area`.

4. Update tests (unit tests and fixtures):

- `tests/aruco/test_aruco_detector.py`: adjust fixtures to build `SheetArucoConfig` or pass through `ArucoDetectorConfig` into the new config.
- `tests/config/aruco/test_aruco_configs.py`: add tests for `SheetArucoConfig` defaults and validation.

5. Update documentation and examples:

- `docs/roadmap/roadmap.md` — update description and migration notes.
- `scratch_space/*` READMEs and notebooks that instantiate `SheetAruco` (explicit list below) — update examples to construct `SheetArucoConfig` and call `load_sheet(img_fp)` without `min_area`.
  - `scratch_space/streamline_sheet_aruco/README.md`
  - `scratch_space/aruco_setup/04_load_sheets.ipynb`
  - `scratch_space/segment_shape/01_segment_shape.ipynb`
  - `scratch_space/weird_edge_shape_detection/01_data_exploration.ipynb`
  - `scratch_space/sheet_manager/02_usage.ipynb`
  - `scratch_space/sheet_loader_refactor/README.md`

6. Run tests and iterate:

- `uv run pytest tests/ -q` — fix failing tests.
- `uv run ruff format .` and `uv run ruff check .`.
- `uv run pyright` (type-check) if available.

7. Add migration notes and deprecation guidance:

- Insert `# TODO/DEPRECATED` comments where `min_area` previously appeared.
- Add a short migration note to `docs/roadmap/roadmap.md` and this README.

8. Finalize and prepare PR:

- Ensure tests pass, format code, and add changelog entry referencing `feat/sheet-aruco-config`.

Files to update (precise list to open/patch):

- `src/snap_fit/puzzle/sheet_aruco.py`
- `src/snap_fit/config/aruco/aruco_detector_config.py` (import check)
- `src/snap_fit/config/aruco/sheet_aruco_config.py` (new)
- `tests/aruco/test_aruco_detector.py`
- `tests/config/aruco/test_aruco_configs.py`
- `docs/roadmap/roadmap.md`
- Notebooks and scratch READMEs listed in step 5.

Now that you've chosen Option A, I will update the `manage_todo_list` to this checklist and mark the branch creation as `in-progress` (ready for me to create if you want). If you'd like, I can also create the branch and scaffold the new config file next — confirm and I'll proceed. 4. Replace any local references to `min_area` with `self.config.min_area`.
