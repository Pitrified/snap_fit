# implementation tracking

Tracked work for adding an optional green board background and the minimum
pipeline changes needed to keep ArUco detection and piece extraction reliable.
Analysis, rationale, and open questions are in
[00_start.md](00_start.md).

## Key decisions

- Follow the simplest implementation path first.
- Use named presets for board background options.
- Implement optional HSV background-mask override before building generic
  color-threshold scaffolding.
- Treat backward compatibility as preferred, not mandatory. If broken,
  document impacted datasets with WARNING.md.
- Keep detector warp-border color semantics independent from board background.
- Keep the QR payload stable in Phase 1 and resolve background preset through
  board_config_id unless a later phase proves that is insufficient.
- Refactor Sheet preprocess params into a config object (D12) as part of the
  mask plumbing, resolving the REFA comment in sheet.py.
- Implement board config resolution at ingest (D14): the QR board_config_id
  loads the stored JSON from data/aruco_boards/{id}/ and its preset drives the
  mask automatically; no hand-built configs when ingesting physical photos.
  The flow lives in the driver (notebook/service) via loader and derivation
  helpers; SheetAruco/Sheet never touch JSON on disk.
- background_mask nests inside the new SheetPreprocessConfig (Q11), amending
  its phase 1 top-level placement; code-only, no dataset JSON uses it yet.
- The board generation notebook is the operator entry point for green boards
  (D11); validation uses synthetic plus real captures (D15).
- Phase 4 covers every photo-ingest notebook, not just the print notebook:
  reload-by-tag drivers (04_load_sheets, fastapi db_ingestion,
  sheet_manager/02_usage) inherit the mask through their saved config; the
  metadata-aware 20_piece_markers/00_sample uses the decode-by-id loader.
- The mask is a mode switch (D17): `as_threshold` (D13) or `flatten_to_white`
  (paint green pixels white, run the existing pipeline); phase 5 picks the
  default from measured extraction quality.
- The detector out-of-warp border fill moves from green to magenta (D16),
  scheduled in phase 3, so the green mask cannot swallow it.

## Phases

| #  | Phase                                  | Plan                                        | Status  |
| -- | -------------------------------------- | ------------------------------------------- | ------- |
| 1  | Minimal config contract                | [01_minimal_config_contract.md](01_minimal_config_contract.md) | done |
| 2  | Background preset composition path     | [02_background_preset_composition_path.md](02_background_preset_composition_path.md) | done |
| 3  | HSV green-mask preprocess option       | [03_hsv_green_mask_preprocess_option.md](03_hsv_green_mask_preprocess_option.md) | draft |
| 4  | Board config resolution at ingest      | [04_board_config_resolution_at_ingest.md](04_board_config_resolution_at_ingest.md) | draft |
| 5  | Tests and compatibility decision gate  | [05_tests_and_compatibility_decision_gate.md](05_tests_and_compatibility_decision_gate.md) | draft |
| 6  | Docs and dataset warnings (if needed)  | [06_docs_and_dataset_warnings_if_needed.md](06_docs_and_dataset_warnings_if_needed.md) | draft |

Status values: draft / planned / in progress / done / superseded / discarded.

## Log

Append-only. Newest at the bottom.

- 2026-07-12 : bootstrapped tracked development for 23_green_background; deep-read docs and cross-checked code paths for board generation, composition, detection, and sheet preprocess.
- 2026-07-12 : proposed five phases in tracking only; intentionally deferred creating phase sub-plan files until scope answers are provided.
- 2026-07-12 : folded user ANS and NOTE into the plan; shifted strategy to named presets + simple HSV mask first, with compatibility as non-blocking.
- 2026-07-12 : audited existing dataset artifacts (data configs, cache metadata/matches, dataset.db) and recorded risk profile for additive versus breaking config changes.
- 2026-07-12 : no new questions emerged from the audit; expanded the tracked plan into five phase sub-plan files.
- 2026-07-12 : reclassified phases 1-5 from planned to draft; each phase now requires an explicit draft-to-plan pass before execution begins.
- 2026-07-12 : completed draft-to-plan pass for phase 1; locked additive config contract with explicit defaults and compatibility decision gate.
- 2026-07-12 : renamed the mask contract to background_mask and explicitly kept the QR payload stable for phase 1.
- 2026-07-12 : implemented phase 1 additive config contract in code, added contract regression tests, and marked phase 1 done.
- 2026-07-12 : completed draft-to-plan pass for phase 2; locked colorization approach (luminance-scaled preset BGR) in BoardImageComposer.compose(), confirmed single call site, and documented the green-preset / warp-border-artifact interaction as non-blocking.
- 2026-07-12 : implemented phase 2; added _colorize_background() to BoardImageComposer with the preset BGR table, added regression tests (white byte-identical, markers black, background exact preset color), verified lint/type-check clean, and marked phase 2 done.
- 2026-07-12 : gap assessment after phases 1-2; verified p1/p2 commits match their sub-plans and the 9 regression tests pass; recorded gaps G1-G7 and questions Q7-Q10 in 00_start.md (no production caller for the preset, background_mask plumbing to Sheet.preprocess undesigned, mask semantics unspecified, board_config_id resolution unimplemented, no green validation data plan, no detector-on-green test).
- 2026-07-12 : folded in the G1-G7 and Q7-Q10 answers as D11-D15; inserted new phase 4 (board config resolution at ingest, from G4) and renumbered tests to phase 5 and docs to phase 6; expanded the phase 3 draft with the preprocess config refactor (Q8) and threshold-step-only mask semantics (Q9); rewrote the proposed phase sequence in 00_start.md (G7); opened Q11 (background_mask placement after refactor) and Q12 (auto-enable precedence rule).
- 2026-07-12 : folded in Q11 (mask nests in SheetPreprocessConfig) and Q12 (auto-enable precedence confirmed); surveyed the actual driver usage pattern (webapp services and 01_print_read_board.ipynb load full SheetArucoConfig JSON from disk and hand it to SheetAruco; the notebook already saves both config JSONs next to the board PNGs at print time) and recorded it in 00_start.md; rewrote phase 4 as driver-level loader + derivation helpers plus notebook wiring - SheetAruco/Sheet get no disk-config code; corrected the phase 5 entry-point notebook to 01_print_read_board.ipynb.
- 2026-07-20 : folded in three review notes. Note 1: surveyed all photo-ingest notebooks (04_load_sheets, fastapi db_ingestion, sheet_manager/02_usage reload by tag; 20_piece_markers/00_sample decodes by id) and widened phase 4 and phase 5 to cover them, not just 01_print_read_board. Note 2: scheduled the detector border recolor green->magenta as D16 inside phase 3. Note 3: turned the mask into a mode switch (D17) with as_threshold and a new flatten_to_white strategy (paint green pixels white, run the existing pipeline unchanged), added the mask-mode experiments to phase 5.
