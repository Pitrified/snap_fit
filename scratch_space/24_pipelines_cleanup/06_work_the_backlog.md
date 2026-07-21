---
status: draft
---

# Phase 6 - Work the backlog, one item at a time

## Overview

The open-ended phase. Each remaining backlog capability is assessed on its own
and either promoted to a pipeline (authored fresh) or rejected with a recorded
rationale. No megadump; the folder only grows by deliberate per-item decisions.
Context: [00_start.md](00_start.md), depends on
[01_conventions.md](01_conventions.md) (the backlog) and
[05_promote_src_gaps.md](05_promote_src_gaps.md). Decisions D1, D2, D11, D12, D17.

## Goals

1. Take `pipelines/backlog.md` from seeded to emptied: every candidate promoted
   or rejected.
2. Keep each promotion to the pipeline shape (thin, logic in `src`).

## Plan

Per backlog item, in an order chosen by value (not the audit's order):

1. Assess: is this worth a pipeline (D1), better left as docs, or redundant?
   Read the freshest reference notebook for the capability as context only (D2).
2. If rejected: mark the row rejected in `pipelines/backlog.md` with a one-line
   rationale (D17). The row stays as a durable record for future re-proposals.
3. If promoted: author a fresh entry (notebook or script per D7), all logic in
   `src` (promote first if missing, D3), header + README index (D10, D8), strip
   outputs, and confirm `make pipelines-check` passes.

Named items already identified:

- `16_support.py` (D12): its own assessment. Pinpoint the reusable core (the
  board / rectified / cropped coordinate transforms) versus the verification
  scaffolding, and promote only the core to `src` (a coordinate-transform
  helper) or to a `scripts/` folder. Do not relocate 268 lines wholesale.
- Candidate capabilities from the audit: bulk ingest to SQLite, segment
  matching, grid and scoring, solving, synthetic puzzle generation, sheet
  identity. Each gets its own assess-then-promote-or-reject pass.

## Out of scope

- Doing several items at once.
- Re-opening a rejected item without a new reason (the recorded rationale is the
  bar to clear).

## Done when

- Every `pipelines/backlog.md` row is promoted or rejected with a rationale.
- Each promoted entry meets the pipeline shape and passes `make pipelines-check`.
- `16_support.py`'s reusable core is in `src` (or `scripts/`) with the
  scaffolding left behind, or the item is explicitly rejected.
