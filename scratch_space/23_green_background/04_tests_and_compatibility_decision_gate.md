---
status: draft
---

# Phase 4 - Tests and compatibility decision gate

## Overview

Validate behavior and then make an explicit keep-compatibility or break-and-
reingest decision using measured outcomes.
Context: [00_start.md](00_start.md), depends on
[02_background_preset_composition_path.md](02_background_preset_composition_path.md)
and
[03_hsv_green_mask_preprocess_option.md](03_hsv_green_mask_preprocess_option.md).

## Goals

1. Add targeted tests for board presets and HSV preprocessing behavior.
2. Run verification against existing dataset configs and sample outputs.
3. Decide whether compatibility preservation is worth the complexity.

## Plan

- Add or extend unit tests in aruco and puzzle coverage areas.
- Run repository verification suite and focused dataset checks.
- Record a compatibility decision with rationale and affected folders.

## Out of scope

- Final docs and operator-facing migration notes.

## Done when

- Tests cover the new behavior and pass.
- A clear compatibility decision is written with actionable follow-up.
