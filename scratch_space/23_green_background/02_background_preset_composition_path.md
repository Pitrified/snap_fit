---
status: draft
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

- Implement preset-driven background colorization in the composition flow.
- Verify resulting board images preserve marker contrast and QR strip legibility.
- Keep fallback behavior aligned with current output for default preset.

## Out of scope

- HSV preprocessing changes.
- Any dataset migration work.

## Done when

- Board generation and composition can produce preset backgrounds using the
  agreed config contract.
- Default preset output remains compatible with current workflows.
