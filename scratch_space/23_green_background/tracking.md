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

## Phases

| #  | Phase                                  | Plan                                        | Status  |
| -- | -------------------------------------- | ------------------------------------------- | ------- |
| 1  | Minimal config contract                | [01_minimal_config_contract.md](01_minimal_config_contract.md) | done |
| 2  | Background preset composition path     | [02_background_preset_composition_path.md](02_background_preset_composition_path.md) | draft |
| 3  | HSV green-mask preprocess option       | [03_hsv_green_mask_preprocess_option.md](03_hsv_green_mask_preprocess_option.md) | draft |
| 4  | Tests and compatibility decision gate  | [04_tests_and_compatibility_decision_gate.md](04_tests_and_compatibility_decision_gate.md) | draft |
| 5  | Docs and dataset warnings (if needed)  | [05_docs_and_dataset_warnings_if_needed.md](05_docs_and_dataset_warnings_if_needed.md) | draft |

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
