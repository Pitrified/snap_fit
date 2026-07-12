---
status: draft
---

# Phase 4 - Board config resolution at ingest

## Overview

Implement the flow the G4 answer describes: the QR payload carries a board
config name, the matching JSON is found on disk, and loading it reveals the
background preset. The operator should not rebuild the board config by hand
when ingesting a physical photo.

Per the driver-level note (2026-07-12): this flow lives entirely in the
driver (notebook or service). SheetAruco and Sheet never touch JSON on disk;
they receive a fully resolved config, exactly as the webapp services and
`01_print_read_board.ipynb` already do (see the ingest driver usage pattern
in [00_start.md](00_start.md)).
Inserted 2026-07-12 from gap G4; former phases 4 and 5 became 5 and 6.
Context: [00_start.md](00_start.md), depends on
[03_hsv_green_mask_preprocess_option.md](03_hsv_green_mask_preprocess_option.md).

## Goals

1. Give drivers a one-call way to resolve `SheetMetadata.board_config_id`
   to the configs stored in `data/aruco_boards/{id}/`.
2. Make the saved `SheetArucoConfig` carry the mask automatically, so a green
   board cannot silently ingest with the mask disabled.
3. Keep SheetAruco/Sheet free of any disk-config knowledge, and keep photos
   without QR metadata working exactly as today.

## Plan

1. Loader helper (library-level, pure IO, e.g. next to the config models or
   in params/paths): map a board_config_id to
   `snap_fit_paths.aruco_board_fol / id / f"{id}_SheetArucoConfig.json"`
   (and the `_ArucoBoardConfig.json` sibling) and parse it.
   Missing id or file raises a descriptive named exception the driver can
   catch and fall back from - old board folders may lack a stored config.
2. Derivation helper applying the Q12 precedence when a sheet config is
   built or loaded: board preset green/blue with no explicit mask ->
   enable `background_mask` with default HSV bounds; an explicit
   `background_mask` (including enabled=false) always wins.
   This runs at config-build/save time in the print step and again as a
   safety net when a driver loads a config whose preset and mask disagree.
3. Notebook wiring in `01_print_read_board.ipynb`:
   - Print time: pass `background_preset` through to the composer and run
     the derivation helper before saving the config JSONs, so the saved
     `SheetArucoConfig` already contains the enabled mask.
   - Ingest time: decode the QR with `SheetMetadataDecoder` first, then use
     the decoded `board_config_id` with the loader helper to pick the config
     (today the notebook reuses the in-memory variable; make the flow
     actually driven by the decoded id).
4. No QR payload change (D10 holds; Q6 stays answered "no").
5. Unit tests for the helpers: loader hit, missing-id exception, Q12
   auto-enable rule, and explicit-config-wins precedence (both directions).

## Out of scope

- QR payload changes.
- Any disk access from SheetAruco, Sheet, or the preprocess path.
- Migrating existing board folders that lack a stored config JSON.
- Webapp changes: dataset folders keep carrying their own
  `{tag}_SheetArucoConfig.json`; a green dataset simply saves one with the
  mask enabled (produced by the print-time step).
- Validation on real photos (phase 5).

## Done when

- A driver can go from a raw photo to a resolved SheetArucoConfig with two
  helper calls (decode QR, load by id) and no hand-built config.
- A config saved for a green board contains the enabled mask
  (test enforced via the derivation helper).
- Photos without decodable metadata behave exactly as before: the driver
  falls back to its existing config path.
- SheetAruco and Sheet contain no new disk-config code.
