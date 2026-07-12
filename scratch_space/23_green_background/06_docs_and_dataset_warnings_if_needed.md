---
status: draft
---

# Phase 6 - Docs and dataset warnings if needed

## Overview

Publish the final operational guidance after compatibility decisions are made,
including dataset warnings only when the breaking path is selected.
Renumbered from phase 5 on 2026-07-12 when board config resolution was
inserted as phase 4.
Context: [00_start.md](00_start.md), depends on
[05_tests_and_compatibility_decision_gate.md](05_tests_and_compatibility_decision_gate.md).

## Goals

1. Update developer docs for new board preset and preprocessing options.
2. If breaking, add WARNING.md in each impacted dataset folder.
3. Provide concise re-ingest guidance where required.

## Plan

- Update relevant docs pages and usage notes.
- Create dataset warning files only for confirmed impacted datasets.
- Record final decisions and outcomes in tracking log.

## Out of scope

- Additional feature work beyond documented scope.

## Done when

- Docs describe final behavior and configuration.
- Breaking-path warnings exist where needed, or are explicitly marked not
  required.
