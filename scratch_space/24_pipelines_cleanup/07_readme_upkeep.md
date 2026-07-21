---
status: draft
---

# Phase 7 - README upkeep and per-entry docs if needed

## Overview

The standing maintenance phase, never fully "done" while the folder lives. Keeps
`pipelines/README.md` matching reality and runs the freshness pass, adding a
dedicated docs page only when an entry actually earns one.
Context: [00_start.md](00_start.md). Decisions D9, D10.

## Goals

1. `pipelines/README.md` always matches the folder contents.
2. Drift is caught by the agreed mechanism, not left to rot.

## Plan

1. As each entry lands (phases 2, 3, 6), update the README index row and its
   order/dependency note in the same change (D8, D10).
2. Periodic freshness pass (D9): run `make pipelines-check`, read the report,
   and fix or date any entry that drifted. This is manual and periodic, not CI.
3. Per-entry docs page only if D10's trigger is hit: an entry became complex or
   widely used. Otherwise the file header plus the README index is the
   documentation, and the entry links to an existing guide for the why.

## Out of scope

- Adding docs pages by default (D10).
- CI execution of pipelines (D9).

## Done when

- The README index matches the folder at every point an entry is added.
- A freshness pass has been run at least once and its result recorded in the
  tracking Log.
- Any entry that crossed the D10 complexity trigger has a docs page; the rest do
  not.
