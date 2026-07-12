---
status: draft
---

# Phase 3 - HSV green-mask preprocess option

## Overview

Add an optional HSV green-mask override step for sheet preprocessing to support
real photos captured on generated green boards.
Context: [00_start.md](00_start.md), depends on
[01_minimal_config_contract.md](01_minimal_config_contract.md) and
[02_background_preset_composition_path.md](02_background_preset_composition_path.md).

## Goals

1. Implement opt-in HSV masking behavior without forcing it on existing flows.
2. Keep preprocessing readable and avoid branching complexity.
3. Ensure piece extraction remains stable on non-green captures when disabled.

## Plan

- Add preprocess options and parameter handling per the phase 1 contract.
- Implement a focused HSV green-mask override before the existing binary path.
- Validate with representative oca and milano1 style captures and at least one
  green-background sample set.

## Out of scope

- Generic multi-color segmentation framework.
- Refactoring the entire sheet preprocessing stack.

## Done when

- The HSV mask step is optional and configurable.
- Disabled behavior remains consistent with current baseline processing.
