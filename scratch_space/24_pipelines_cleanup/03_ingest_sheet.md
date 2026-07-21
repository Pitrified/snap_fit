---
status: draft
---

# Phase 3 - ingest_sheet notebook

## Overview

The ingest counterpart to phase 2, completing the current live workflow: from a
photo of a board to labelled pieces. A notebook because the value is validating
the results (piece count, labels, overlays) after a run.
Context: [00_start.md](00_start.md), depends on
[02_generate_board.md](02_generate_board.md). Decisions D6, D13, D14, D15.

## Goals

1. `pipelines/ingest_sheet.ipynb`: a thin, runnable photo-ingest notebook.
2. Show the ingest results clearly enough to validate a real capture.

## Plan

1. Author fresh (D2) from `23_green_background/ingest_green_sheet.py` as the
   reference, via the MCP server or `NotebookEdit` (D15).
2. Cell layout (thin flat cells):
   - a header markdown cell: what it does, what it needs (a photo, and a board
     config already on disk from `generate_board`), what it produces, and a link
     to the green guide. Per D13, the header documents how to recreate the data:
     run `generate_board`, display, photograph.
   - thin cells that decode the QR (`SheetMetadataDecoder`), resolve the config
     by id (`load_sheet_config_by_id`), and run `SheetAruco.load_sheet`.
   - a validation cell displaying piece count, slot labels, and an overlay on
     the rectified sheet.
   - white and green boards both work through the same cells (D14); the mask
     engages only for green/blue via the resolved config.
3. All logic from `src`; nothing non-trivial defined in the notebook (D3).
4. Add to `pipelines/README.md` (with its dependency on `generate_board` noted
   in the index) and mark the ingest backlog row promoted.
5. Strip outputs (`make nbstrip`); confirm `make pipelines-check` passes.

## Out of scope

- Retiring the `23_green_background` scripts (phase 4).
- Committing photo data (D13); the greendemo captures stay gitignored.
- Bulk ingest into SheetManager/SQLite (a separate backlog item, phase 6).

## Done when

- `pipelines/ingest_sheet.ipynb` runs top to bottom on a real photo set and
  displays piece count, labels, and an overlay.
- Cells are thin and call into `src`.
- Outputs stripped, README indexes it with its dependency, `make pipelines-check`
  passes.
