---
status: draft
---

# Phase 3 - HSV green-mask preprocess option

## Overview

Add an optional HSV green-mask override step for sheet preprocessing to support
real photos captured on generated green boards.
Per Q8 this phase also performs the preprocess config refactor that the REFA
comment in `sheet.py` asks for, since the mask needs a plumbing path anyway.
Context: [00_start.md](00_start.md), depends on
[01_minimal_config_contract.md](01_minimal_config_contract.md) and
[02_background_preset_composition_path.md](02_background_preset_composition_path.md).

## Goals

1. Implement opt-in HSV masking behavior without forcing it on existing flows.
2. Introduce a preprocess config object that owns the currently hardcoded
   parameters (D12), resolving the REFA comment in `sheet.py`.
3. Ensure piece extraction remains stable on non-green captures when disabled.
4. Express the mask as a mode switch (D17) so phase 5 can experiment with the
   `as_threshold` and `flatten_to_white` strategies without another rewrite.
5. Recolor the detector out-of-warp border fill to magenta (D16) so the green
   mask cannot swallow it.

## Plan

1. Add a `SheetPreprocessConfig` pydantic model in
   `src/snap_fit/config/aruco/` alongside the existing sheet models,
   with fields matching today's hardcoded values as defaults:
   blur kernel (21), threshold (130), erosion kernel/iterations (3, 2),
   dilation kernel/iterations (3, 1), and `background_mask` nested inside it
   (Q11: moved from the SheetArucoConfig top level; code-only change since no
   dataset JSON uses the field yet).
2. Thread it: `SheetArucoConfig.preprocess` (default preserves behavior)
   -> `SheetAruco.load_sheet()` -> `Sheet.__init__` -> `Sheet.preprocess()`.
   `Sheet(` has a single production call site (`sheet_aruco.py:95`) and no
   direct test constructions, so the signature change is low-risk.
3. Implement the mask as a mode switch (D17). Add a `mode` field to
   `BackgroundMaskConfig` with two values:
   - `as_threshold` (D13, default): when enabled, it replaces only the
     threshold step (Q9). Pipeline becomes:
     blur -> [inRange(HSV) on the blurred BGR image] -> erode -> dilate -> flip.
     The `cv2.inRange` output already has the same polarity as
     `apply_threshold` (background white 255, pieces black 0), so the
     surrounding steps and `flip_colors_bw` stay untouched.
   - `flatten_to_white`: inRange selects the green pixels, those pixels are
     painted 255,255,255 in the blurred BGR image, and the existing
     grayscale -> threshold -> erode -> dilate -> flip runs unchanged on the
     flattened image. The downstream pipeline sees a clean white background and
     nothing else about it changes.
   Keep the machinery minimal: one mode field, a shared `inRange` call, and a
   branch, not a generic composable-step framework.
4. Recolor the detector border fill (D16): change `borderValue=(0, 255, 0)` to
   magenta in `ArucoDetector.correct_perspective()` (aruco_detector.py:114) so
   the green mask does not treat out-of-warp pixels as background. This is a
   self-contained detector change; no other detector behavior moves.
5. Add range validation and documentation to `BackgroundMaskConfig`:
   OpenCV hue scale is 0-179, saturation/value 0-255 (closes the G3 remainder).
6. Unit tests: disabled path byte-identical to current preprocess on a sample
   image; `as_threshold` turns a synthetic green background into background
   (white pre-flip) and keeps a non-green piece region as foreground;
   `flatten_to_white` yields the same extraction on a synthetic green frame and
   is byte-identical to the baseline on a white frame (green pixels absent, so
   nothing is repainted).

## Out of scope

- Generic multi-color segmentation framework.
- Board config resolution at ingest (phase 4).
- Real-photo validation (phase 5).

## Done when

- The HSV mask step is optional and configurable.
- Disabled behavior remains consistent with current baseline processing
  (test enforced).
- `Sheet.preprocess()` no longer hardcodes its parameters; defaults come from
  `SheetPreprocessConfig` and reproduce current output exactly.
- `BackgroundMaskConfig` validates HSV bounds and documents the OpenCV scale.
- The mask `mode` switch supports both `as_threshold` and `flatten_to_white`,
  each with a passing test; phase 5 chooses which to recommend.
- The detector out-of-warp border fill is magenta, not green (D16).
