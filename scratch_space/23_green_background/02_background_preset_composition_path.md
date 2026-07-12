---
status: done
---

# Phase 2 - Background preset composition path

## Overview

Implement the simplest board background preset path at composition time while
keeping current white behavior available by default.
Context: [00_start.md](00_start.md), depends on
[01_minimal_config_contract.md](01_minimal_config_contract.md).

## Goals

1. Add background preset support where board image composition already occurs.
2. Keep ArUco marker visibility and metadata overlays intact.
3. Keep detector warp-border color semantics separate from board presets.

## Plan

1. Implement colorization in `BoardImageComposer.compose()`, the single
   production call site that turns the grayscale board into BGR (per D4:
   composition layer, not board generation).
2. Keep `ArucoBoardGenerator.generate_image()` unchanged and grayscale-only.
   `ArucoDetector` keeps constructing its own `ArucoBoardGenerator` from
   `config.board` purely for marker geometry; it does not render pixels, so
   `background_preset` has no effect on detection setup.
3. Add a small preset-to-BGR color table local to
   `board_image_composer.py`.
4. Replace the current identity `cv2.cvtColor(gray, COLOR_GRAY2BGR)` step
   with a `_colorize_background(gray)` helper that special-cases `white` as
   an unchanged identity path and applies per-channel luminance scaling for
   `green`/`blue`.
5. Add composer tests (new test file; none exist today) covering: default
   white output is byte-identical to today's `cvtColor` behavior, marker
   pixels stay black under every preset, and background pixels become the
   exact preset color.

## Current code path (confirmed)

- `ArucoBoardGenerator.generate_image()` is used in exactly two places:
  `ArucoDetector.__init__` (geometry only, for `matchImagePoints`) and
  `BoardImageComposer.compose()` (rendering). No other call sites exist in
  `src/` or `tests/`.
- `BoardImageComposer` itself has no existing tests and is not yet wired into
  any router/service, so this phase changes an isolated, low-risk surface.

## Proposed colorization approach

Preset color table (BGR, `cv2` convention):

| Preset | BGR           | Notes                                            |
| ------ | ------------- | ------------------------------------------------- |
| white  | (255, 255, 255) | Identity; must reproduce current output exactly. |
| green  | (0, 255, 0)   | Pure green; matches `ArucoDetector`'s existing warp `borderValue=(0, 255, 0)` (see below). |
| blue   | (255, 0, 0)   | Pure blue; reserved for quick visual experiments. |

Algorithm (vectorized, no per-pixel Python loop):

```python
colored[..., c] = round(gray * preset_bgr[c] / 255)
```

- When `gray == 255` (background): output equals the preset color exactly.
- When `gray == 0` (marker ink): output stays `(0, 0, 0)` regardless of preset,
  so marker contrast against the colored background is preserved.
- Anti-aliased border pixels (if any) blend linearly toward the preset color,
  proportional to their original grayscale value, so no new hard edges are
  introduced.
- For `white`, skip the scaling math entirely and keep the existing
  `cv2.cvtColor(gray, COLOR_GRAY2BGR)` call so default output is provably
  unchanged (covered by a test comparing bytes).

## Interaction with the detector warp-border artifact

- `ArucoDetector.correct_perspective()` already fills out-of-warp pixels with
  `borderValue=(0, 255, 0)`, i.e. the same BGR value proposed for the green
  preset.
- Per D9, these are kept semantically independent in this phase: the detector
  border color is not derived from `background_preset` and is not changed
  here.
- Flag as a noted implication, not a blocker: if a green board preset is
  combined with the green warp-border artifact, a downstream green-mask step
  (Phase 3) would treat both as background, which is actually convenient
  rather than a conflict. No action required in Phase 2.

## Overlay legibility (validation item, not a blocking redesign)

- Slot labels render in gray `(128, 128, 128)` text
  (`SlotGrid.render_labels`); the human-readable identity line renders in
  black `(0, 0, 0)` text (`SheetMetadataEncoder._place_text`); the QR strip
  itself overwrites its region with its own black/white pixels regardless of
  board background.
- These overlay colors are not changed in this phase. Legibility on `green`
  and `blue` presets is validated visually per D8 (real images plus targeted
  tests) in Phase 4. If legibility fails, adjusting overlay colors is a
  small, isolated follow-up and does not require reopening this phase's
  config contract.

## Out of scope

- HSV preprocessing changes (Phase 3).
- Any dataset migration work.
- Changing `ArucoDetector`'s warp-border color.
- Adapting slot-label or metadata-text color per preset.

## Done when

- Board generation and composition can produce preset backgrounds using the
  agreed config contract.
- Default preset output remains byte-identical to current workflows (test
  enforced).
- Marker pixels are provably black under every preset (test enforced).
- Background pixels match the exact preset BGR value away from markers/
  overlays (test enforced).
