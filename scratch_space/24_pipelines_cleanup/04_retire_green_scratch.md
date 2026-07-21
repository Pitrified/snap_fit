---
status: draft
---

# Phase 4 - Retire the green scratch scripts

## Overview

The one deliberate exception to D4: once the `generate_board` and `ingest_sheet`
pipelines exist and run, the `23_green_background` scripts are redundant runnable
copies and are removed to prevent drift.
Context: [00_start.md](00_start.md), depends on
[02_generate_board.md](02_generate_board.md) and
[03_ingest_sheet.md](03_ingest_sheet.md). Decision D18 (from Q11).

## Goals

1. Remove the promoted-from scratch scripts.
2. Repoint the docs that reference them at the new pipelines.

## Plan

1. Delete `scratch_space/23_green_background/generate_green_board.py` and
   `ingest_green_sheet.py`. The rest of `23_green_background` stays as feature
   history (D4 still holds for it).
2. Update `docs/guides/green_background.md`: its "Generate the board set" and
   "Ingest" sections currently point at the scratch scripts. Repoint them at
   `pipelines/generate_board.ipynb` and `pipelines/ingest_sheet.ipynb`.
   Decide there whether to trim the guide's inline code examples to a link now
   that a runnable pipeline exists, or keep them as illustrative (residual item
   noted in the tracking Log).
3. Grep the repo for any other reference to the two script paths and fix or
   remove them (the phase 5 tracking of feature 23 mentions them; leave that
   historical record but do not leave a live pointer that now 404s).
4. Update `docs/index.md` last-updated and append a `docs/log.md` entry via the
   docs procedure.

## Out of scope

- Touching any other `scratch_space` folder (D4).
- New pipeline capabilities (phase 6).

## Done when

- The two scratch scripts are gone.
- `docs/guides/green_background.md` points at the pipelines, and no live
  reference to the deleted script paths remains.
- Docs index/log updated.
