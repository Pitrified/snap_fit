---
status: draft
---

# Phase 5 - Promote the src gaps found in the seed pair

## Overview

A checkpoint, expected to be near-empty for the green pair but kept as a distinct
phase so the pattern is set for later capabilities that will genuinely need it:
when a pipeline wants to define logic, that logic goes into `src` first (D3).
Context: [00_start.md](00_start.md), depends on
[02_generate_board.md](02_generate_board.md) and
[03_ingest_sheet.md](03_ingest_sheet.md). Decision D3.

## Goals

1. Ensure no pipeline carries non-trivial logic in its cells.
2. Whatever the seed pair could not express as flat `src` calls lands in `src`
   with tests.

## Plan

1. Review `generate_board` and `ingest_sheet` for any cell that defines a
   function or class, or does real computation rather than a flat call/loop.
2. For each such piece: move it into the appropriate `src` module, add a test,
   and reduce the notebook cell to a call. The green-background logic already
   lives in `src` (feature 23), so this phase is expected to find little or
   nothing; record "none found" explicitly if so.
3. Run the suite (`uv run pytest`) and the pipeline import check.

## Out of scope

- `16_support.py` promotion; that is a backlog item in phase 6 (D12), not a gap
  from the seed pair.
- Backlog capabilities (phase 6).

## Done when

- No pipeline defines non-trivial logic; anything that did is in `src` with a
  test, or the phase records that none was found.
- The suite and `make pipelines-check` pass.
