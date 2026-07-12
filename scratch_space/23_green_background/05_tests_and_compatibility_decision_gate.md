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
3. Decide whether compatibility preservation is worth the complexity.

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
   `ArucoDetector.rectify()`, expect successful rectification.
5. Run the repository verification suite and focused dataset checks against
   existing white-background datasets.
6. Record a compatibility decision with rationale and affected folders.

## Out of scope

- Final docs and operator-facing migration notes.

## Done when

- Synthetic and real green captures both pass ingest with pieces extracted.
- The detector rectifies a rendered green board (test enforced).
- Existing white-background tests and datasets still pass.
- A clear compatibility decision is written with actionable follow-up.
