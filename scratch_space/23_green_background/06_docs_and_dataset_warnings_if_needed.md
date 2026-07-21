---
status: done
---

# Phase 6 - Docs and dataset warnings if needed

## Outcome (2026-07-21)

No dataset warnings were needed: phase 5 closed the gate as keep-compatibility
(D19), so no WARNING.md files were written and no re-ingest is required.
The phase reduced to a docs pass, done with the repo's `docs-write` procedure
(`.github/skills/docs-write/SKILL.md`): write pages, then update
`docs/index.md` and `docs/log.md`.

Written:

- `docs/guides/green_background.md` (new guide): the screen-displayed board
  workflow end to end - generate a board set with the green preset, photograph
  it, ingest by decoding the QR and resolving the stored config by
  `board_config_id`, and use the QR `sheet_index` plus the slot label as the
  manual tracking key (D20/D21). Carries the hard-won pitfalls: `min_area`,
  the mask value floor, and why a green board is unusable with the mask off.

Updated:

- `docs/library/puzzle/sheet.md` - was stale: it documented the `threshold`
  attribute and a "threshold is hard-coded" pitfall that D12 removed. Now
  documents `SheetPreprocessConfig`, the mask, and both modes.
- `docs/library/puzzle/sheet_aruco.md` - preprocess threading, resolver-based
  ingest, `min_area` guidance.
- `docs/library/aruco/board.md` - background presets and the composer split.
- `docs/library/aruco/index.md` - the untracked modules (composer,
  sheet_metadata, slot_grid, board_config_resolver) and the resolution flow.
- `docs/library/config/index.md` - `SheetPreprocessConfig`,
  `BackgroundMaskConfig`, OpenCV HSV scale pitfall.
- `docs/index.md` catalog rows and a `docs/log.md` ingest entry.

Verified: 0 broken relative links across the touched pages. No mkdocs config
exists in the repo, so no nav registration was required.

## Overview

Publish the final operational guidance after compatibility decisions are made,
including dataset warnings only when the breaking path is selected.
Renumbered from phase 5 on 2026-07-12 when board config resolution was
inserted as phase 4.
Context: [00_start.md](00_start.md), depends on
[05_tests_and_compatibility_decision_gate.md](05_tests_and_compatibility_decision_gate.md).

## Goals

1. Update developer docs for new board preset and preprocessing options.
2. If breaking, add WARNING.md in each impacted dataset folder.
3. Provide concise re-ingest guidance where required.

## Plan

- Update relevant docs pages and usage notes.
- Create dataset warning files only for confirmed impacted datasets.
- Record final decisions and outcomes in tracking log.

## Out of scope

- Additional feature work beyond documented scope.

## Done when

- Docs describe final behavior and configuration.
- Breaking-path warnings exist where needed, or are explicitly marked not
  required.
