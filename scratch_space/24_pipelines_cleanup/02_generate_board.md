---
status: done
---

# Phase 2 - generate_board notebook

## Overview

The first real pipeline, and the one that proves the shape and conventions on a
concrete case. Board generation as a notebook because the value is interactive:
tweak parameters, see the composed board.
Context: [00_start.md](00_start.md), depends on
[01_conventions.md](01_conventions.md). Decisions D6, D7, D14, D15.

Reference (read, do not copy - D2):
[../23_green_background/generate_green_board.py](../23_green_background/generate_green_board.py).
That script is current and already the target shape, so the notebook is a thin
re-expression of it, not a migration of stale code. The one thing to change on
the way in: the reference defines a `_verify()` function; the notebook flattens
that into inline cells so nothing non-trivial is defined in a cell (D3).

## Goals

1. `pipelines/generate_board.ipynb`: a thin, runnable board-generation notebook.
2. Prove the conventions from phase 1 hold on a real entry (header, thin cells,
   `make pipelines-check` picks up the notebook, `make nbstrip` cleans it).

## What the reference does (so the cells map to it)

`generate_green_board.py` in order:

1. `get_snap_fit_params()`, make `save_dir = params.paths.aruco_board_fol / id`.
2. Build `ArucoBoardConfig(background_preset="green")`,
   `MetadataZoneConfig(qr_n_codes=3, slot_grid=SlotGridConfig(cols=4, rows=3), ...)`,
   `SheetArucoConfig(min_area=5_000, detector=ArucoDetectorConfig(board=...),
   metadata_zone=...)`.
3. `sheet_aruco_config = derive_background_mask(sheet_aruco_config)` so the saved
   ingest JSON already carries the enabled mask (D14, Q12).
4. `composer = BoardImageComposer(board_config, metadata_zone)`; loop
   `TOTAL_SHEETS`, build a `SheetMetadata` per sheet, `composer.compose(metadata)`,
   `cv2.imwrite` to `sheet_XX.png`.
5. Save `{id}_ArucoBoardConfig.json` (`board_config.model_dump()`) and
   `{id}_SheetArucoConfig.json` (`sheet_aruco_config.model_dump_json()`).
6. `_verify`: decode each PNG's QR round-trips, and the reloaded
   `SheetArucoConfig` has `preprocess.background_mask.enabled`.

## Plan

Author the notebook fresh (D2) via the vscode-notebook MCP server, or
`NotebookEdit` if no kernel is open (D15, D20) - never by hand-writing `.ipynb`
JSON. Cell layout, thin and flat (D6):

1. **Header markdown cell.** What it does (compose an ArUco board set with QR
   metadata and a slot grid, save the PNGs and the two config JSONs), what it
   needs (nothing but `src`; writes into the gitignored `data/aruco_boards/`),
   what it produces (the file list under `data/aruco_boards/{id}/`), and the
   recreation note that replaces committing data (D13). Link
   [docs/guides/green_background.md](../../docs/guides/green_background.md) for
   the why (preset/mask rationale); do not re-explain it here (D10).
2. **Imports cell** (its own dedicated cell). Exactly the reference imports:
   `derive_background_mask`, `BoardImageComposer`, `SheetMetadata`,
   `SheetMetadataDecoder`, `ArucoBoardConfig`, `ArucoDetectorConfig`,
   `MetadataZoneConfig`, `SlotGridConfig`, `SheetArucoConfig`,
   `get_snap_fit_params`, plus `cv2`. Keep imports isolated in this one cell so
   `scripts/check_pipeline_imports.py` (which extracts and runs only the import
   cells) exercises this notebook cleanly - this is the phase-1 freshness contract.
3. **Parameter cell** (D14, Q12). Defaults to the green preset; alternatives
   present but commented for a one-line swap. Decide the exposed knobs here, in
   the writing, not earlier. Starting set to expose, from the reference constants
   and configs:
   - `BOARD_CONFIG_ID` / `TAG` (default `"greendemo"`),
   - `TOTAL_SHEETS` (default 2),
   - `BACKGROUND_PRESET = "green"`  with `# "white"` commented for parity (D14),
   - slot grid `rows=3, cols=4`,
   - `MIN_AREA = 5_000` with the scale comment kept: greendemo pieces are
     10k-16k px^2 rectified, far below the 80k global default, so this is
     board-scale-specific and must travel with the config,
   - `qr_n_codes` and other `MetadataZoneConfig`/ArUco-ring knobs left commented
     as "swap here" hints rather than surfaced, unless writing shows a real need.
4. **Config-build cell(s).** Construct `ArucoBoardConfig`, `MetadataZoneConfig`,
   `SheetArucoConfig` from the parameter cell, then
   `sheet_aruco_config = derive_background_mask(sheet_aruco_config)`. Green/blue
   auto-enables the mask; white leaves it off - the same call is correct for both
   presets (D14), which is what makes this notebook not green-only.
5. **Compose-and-save cell.** `save_dir.mkdir(parents=True, exist_ok=True)`,
   `composer = BoardImageComposer(...)`, a flat `for i in range(TOTAL_SHEETS)`
   loop that builds `SheetMetadata`, calls `composer.compose(metadata)`, and
   `cv2.imwrite`s `sheet_{i:02d}.png`; then write the two config JSONs
   (`ArucoBoardConfig.model_dump()` and `SheetArucoConfig.model_dump_json()`).
6. **Display cell.** Show the composed board(s) inline for visual validation -
   convert BGR->RGB and render with matplotlib. This is the interactive payoff
   that justifies a notebook over the script (D6).
7. **Validation cells** (flatten the reference `_verify`, no `def` - D3). One
   flat cell decoding each saved PNG with `SheetMetadataDecoder().decode(img)`
   and asserting the QR round-trips with the expected `board_config_id`; one
   flat cell reloading the saved `SheetArucoConfig` and asserting
   `preprocess.background_mask` is enabled for the green preset. Assertions, not
   a helper.
8. **Wire-up in phase-1 scaffolding.** Add the `generate_board` row to the
   `pipelines/README.md` index table (Does / Needs / Guide); flip the "Board
   generation" row in `pipelines/backlog.md` from `candidate` to `promoted` with
   the entry name.

## Guardrails

- If any cell needs a `def`/`class` beyond a flat loop, stop: that logic belongs
  in `src` first (D3), and it becomes a phase-5 promotion, flagged not inlined.
  The reference already keeps all real logic in `src`, so this is not expected
  here - the only inline thing is the flattened verify assertions.
- No generated board data is committed (D13); the PNGs and JSONs land under the
  gitignored `data/aruco_boards/{id}/`. The header's recreation note is the
  portable substitute.

## Out of scope

- Ingest (phase 3).
- Removing the `23_green_background` generation script (phase 4).
- Any `src` change (phase 5); this entry is expected to need none.

## Done when

- `pipelines/generate_board.ipynb` runs top to bottom against the current API
  and produces a board set (`sheet_XX.png` + both config JSONs) under
  `data/aruco_boards/{id}/`, with the composed board shown inline and the QR /
  mask-enabled assertions passing.
- Cells are thin and call into `src`; no `def`/`class` is defined inline.
- Outputs are stripped (`make nbstrip`), `pipelines/README.md` indexes it, the
  backlog row is `promoted`, and `make pipelines-check` passes with the new
  notebook.
