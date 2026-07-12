---
status: planned
---

# Phase 1 - Minimal config contract

## Overview

Define the smallest config surface needed for this feature so implementation
can proceed without premature abstraction.
Context: [00_start.md](00_start.md).

## Goals

1. Specify named background presets for board rendering.
2. Specify optional HSV background-mask preprocess toggles and parameters.
3. Preserve existing field names and defaults unless an explicit break is
   chosen later.

## Plan

1. Lock board background preset config as a small additive field on
   ArucoBoardConfig.
2. Lock optional HSV background-mask config as a small additive nested field on
   SheetArucoConfig.
3. Validate additive compatibility against current sample configs.
4. Define explicit keep-compat versus break decision criteria.
5. Decide whether the QR payload itself needs a background preset field or if
  board_config_id remains the single source of truth.

## Proposed config contract

### A. Board background preset

Target model: ArucoBoardConfig

- New field: background_preset
- Type: literal string preset
- Allowed values: white, green, blue
- Default: white
- Semantics:
  - white preserves current output behavior.
  - green enables green background rendering path.
  - blue is reserved for quick visual experiments and parity with preset
    naming approach.

Proposed JSON shape (additive):

```json
{
  "markers_x": 5,
  "markers_y": 7,
  "marker_length": 100,
  "marker_separation": 100,
  "dictionary_id": 10,
  "margin": 20,
  "border_bits": 1,
  "background_preset": "white"
}
```

### B. Optional HSV background-mask preprocess

Target model: SheetArucoConfig

- New field: hsv_background_mask
- Type: optional nested object
- Default: null
- Semantics:
  - null means disabled and preserves current preprocess behavior.
  - object with enabled=false is explicit disabled.
  - object with enabled=true activates the override path.

Nested object contract:

- enabled: bool, default false
- lower_hsv: [h, s, v], default [35, 40, 40]
- upper_hsv: [h, s, v], default [95, 255, 255]

Proposed JSON shape (additive):

```json
{
  "min_area": 80000,
  "crop_margin": null,
  "detector": {
    "adaptive_thresh_win_size_min": 3,
    "adaptive_thresh_win_size_max": 23,
    "adaptive_thresh_win_size_step": 10,
    "rect_margin": 50,
    "board": {
      "markers_x": 5,
      "markers_y": 7,
      "marker_length": 100,
      "marker_separation": 100,
      "dictionary_id": 10,
      "margin": 20,
      "border_bits": 1,
      "background_preset": "green"
    }
  },
  "hsv_background_mask": {
    "enabled": true,
    "lower_hsv": [35, 40, 40],
    "upper_hsv": [95, 255, 255]
  }
}
```

## Additive compatibility check

- Existing ArucoBoardConfig JSON files do not include background_preset.
  Default white keeps behavior unchanged.
- Existing SheetArucoConfig JSON files do not include hsv_background_mask.
  Default null keeps preprocess unchanged.
- metadata_zone optionality differences across datasets remain unaffected.

## QR payload decision

Phase 1 keeps the QR payload stable.

- Do not add background_preset to the QR payload in this phase.
- Use board_config_id as the source of truth for the rendered board config,
  including the background preset.
- Revisit payload expansion only if a later phase needs to recover the preset
  without resolving the board config separately.

## Decision gate for compatibility versus break

Keep compatibility path when:

- Additive fields are sufficient for behavior and code remains simple.
- Defaults preserve current behavior for existing configs.

Allow controlled break when:

- Maintaining dual behavior creates complex branching or unclear ownership.
- Reliability or maintainability is materially improved by simplifying contract.

If break is chosen:

- Add WARNING.md in each impacted dataset folder.
- State required action: config migration and/or re-ingest.
- Record the break decision in tracking log before implementation proceeds.

## Out of scope

- Implementing rendering or preprocessing code.
- Building generic color-threshold pipelines beyond the agreed HSV scope.

## Done when

- Config contract is documented in this phase and accepted as the plan of
  record.
- Contract clearly separates mandatory behavior from optional behavior.
- Phase 2 can implement board composition changes without reopening config
  naming decisions.
- QR payload impact is explicitly settled for this phase.
