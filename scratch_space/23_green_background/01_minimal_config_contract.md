---
status: draft
---

# Phase 1 - Minimal config contract

## Overview

Define the smallest config surface needed for this feature so implementation
can proceed without premature abstraction.
Context: [00_start.md](00_start.md).

## Goals

1. Specify named background presets for board rendering.
2. Specify optional HSV green-mask preprocess toggles and parameters.
3. Preserve existing field names and defaults unless an explicit break is
   chosen later.

## Plan

- Propose exact field names and default values for board and sheet configs.
- Validate that proposed fields are additive against existing JSON samples.
- Record compatibility policy for additive versus breaking changes.

## Out of scope

- Implementing rendering or preprocessing code.
- Building generic color-threshold pipelines beyond the agreed HSV scope.

## Done when

- Config contract is documented in this phase and accepted as the plan of
  record.
- Contract clearly separates mandatory behavior from optional behavior.
