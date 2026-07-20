---
status: draft
---

# Phase 5 - Tests and compatibility decision gate

## Overview

Validate behavior end to end and then make an explicit keep-compatibility or
break-and-reingest decision using measured outcomes.
Renumbered from phase 4 on 2026-07-12 when board config resolution was
inserted as phase 4.
Context: [00_start.md](00_start.md), depends on
[03_hsv_green_mask_preprocess_option.md](03_hsv_green_mask_preprocess_option.md)
and
[04_board_config_resolution_at_ingest.md](04_board_config_resolution_at_ingest.md).

## Goals

1. Produce the green validation data (G5, Q10: both synthetic and real).
2. Add targeted tests for board presets, HSV preprocessing, and detection on
   green boards.
3. Run the mask-mode experiments (D17) and recommend `as_threshold` versus
   `flatten_to_white` from measured extraction quality.
4. Decide whether compatibility preservation is worth the complexity.

## Plan

1. Using the phase 4 notebook wiring in
   `scratch_space/20_piece_markers/01_print_read_board.ipynb`
   (the notebook that already uses `BoardImageComposer`; Q7/G1 entry point),
   generate and save a green board under `data/aruco_boards/` with its config
   JSONs, ready for printing and for the loader helper to find.
2. Build the synthetic set: composite existing piece crops onto the green
   board render, run the full ingest pipeline, assert pieces are extracted
   (Q10: synth proves the pipeline exists).
3. Print the green board, photograph real pieces on it, and run ingest
   (Q10: real images show what happens in the real world).
4. Add the detector-on-green test from G6: render a green-preset board, run
   `ArucoDetector.rectify()`, expect successful rectification. Confirm the D16
   magenta border does not reintroduce a false foreground in the mask.
5. Mask-mode experiments (D17, note 3): on the synthetic and real green sets,
   run ingest with the mask disabled (baseline), `as_threshold`, and
   `flatten_to_white`, in the same notebook. Compare extracted piece count,
   contour cleanliness at the green-to-piece boundary, and false pieces from
   background speckle. The `flatten_to_white` idea is the one to beat: paint the
   green-adjacent pixels white so the untouched existing pipeline sees a clean
   sheet. Record which mode to recommend as the default.
6. Apply and verify the phase 4 notebook wiring (deferred there because it is
   only testable with real green data). Exercise the note 1 ingest notebooks
   end to end on a green sample: the decode-by-id path
   (`20_piece_markers/00_sample.ipynb`, `01_print_read_board.ipynb`) calling
   `load_sheet_config_by_id`, the print-time `derive_background_mask` call, and
   at least one reload-by-tag path (`aruco_setup/04_load_sheets.ipynb` or
   `fastapi_scaffold/01_db_ingestion.ipynb`), confirming the reload-by-tag path
   needs no green-specific edits.
7. Run the repository verification suite and focused dataset checks against
   existing white-background datasets.
8. Record a compatibility decision with rationale and affected folders.

## Out of scope

- Final docs and operator-facing migration notes.
- Building a generic composable preprocess-step framework; the experiments use
  the D17 mode switch only.

## Done when

- Synthetic and real green captures both pass ingest with pieces extracted.
- The detector rectifies a rendered green board (test enforced).
- The mask-mode experiments are run and a recommended default mode is recorded
  with the measurements behind it.
- At least one reload-by-tag ingest notebook is shown to handle a green board
  with no green-specific code.
- Existing white-background tests and datasets still pass.
- A clear compatibility decision is written with actionable follow-up.
