---
status: draft
---

# Phase 2 - generate_board notebook

## Overview

The first real pipeline, and the one that proves the shape and conventions on a
concrete case. Board generation as a notebook because the value is interactive:
tweak parameters, see the composed board.
Context: [00_start.md](00_start.md), depends on
[01_conventions.md](01_conventions.md). Decisions D6, D7, D14, D15.

## Goals

1. `pipelines/generate_board.ipynb`: a thin, runnable board-generation notebook.
2. Prove the conventions from phase 1 hold on a real entry.

## Plan

1. Author the notebook fresh (D2) using
   `23_green_background/generate_green_board.py` as the reference, via the
   vscode-notebook MCP server or `NotebookEdit` (D15), never by hand-writing
   `.ipynb` JSON.
2. Cell layout (D6, thin flat cells):
   - a header markdown cell: what it does, what it needs, what it produces, and
     a link to `docs/guides/green_background.md` for the why.
   - a parameter cell defaulting to the green preset, with the white preset and
     other knobs (ArUco ring size, grid piece count) present but commented out
     for a quick swap (D14, Q12). Which knobs to expose is decided here, in the
     writing, not earlier.
   - thin cells that call `BoardImageComposer` + `derive_background_mask` and
     save the PNGs and both config JSONs.
   - a display cell showing the composed board inline for visual validation.
3. Confirm all logic is called from `src`; the notebook defines nothing
   non-trivial (D3). If it must, that is a phase 5 promotion, flagged not
   inlined.
4. Add the entry to `pipelines/README.md` and mark the board-generation backlog
   row promoted.
5. Strip outputs before committing (`make nbstrip`), and confirm
   `make pipelines-check` still passes with the new notebook.

## Out of scope

- Ingest (phase 3).
- Removing the `23_green_background` generation script (phase 4).
- Committing any generated board data (D13); the header documents how to
  recreate it.

## Done when

- `pipelines/generate_board.ipynb` runs top to bottom against the current API
  and produces a board set with its config JSONs.
- Cells are thin and call into `src`; no non-trivial logic is defined inline.
- Outputs are stripped, the README indexes it, and `make pipelines-check` passes.
