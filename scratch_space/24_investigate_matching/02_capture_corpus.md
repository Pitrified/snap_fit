---
status: planned
---

# Phase 2 - Corpus and annotation hand-off

## Overview

Every later phase compares the same physical piece across capture conditions, or
against hand-authored truth. Both need one thing first: all 12 photos ingested
once, with every piece keyed by `(sheet_index, label)` rather than by filename or
by the per-capture ordinal.

The phase then ends by producing the annotation sheet, the single hand-off that
phases 3 and 4 depend on. That artifact is the real deliverable. If it is
awkward to fill in, the whole plan stalls there.

Context: [`00_start.md`](00_start.md), depends on
[`01_fix_interior_overcrop.md`](01_fix_interior_overcrop.md) (contours must not
be truncated before anything is measured from them).

## Goals

1. All 12 photos ingested, pieces and segments persisted, joinable by
   `(sheet_index, label)`.
2. Each capture tagged with its condition, so later phases group by condition
   rather than parsing filenames.
3. Structural assertions that catch a labelling regression instead of silently
   joining on the wrong piece.
4. An annotation sheet that makes the hand pass quick and unambiguous.

## Plan

### Corpus

- Ingest all 12 from `data/greendemo_small/sheets`, decoding the QR per photo to
  resolve the config, as `pipelines/ingest_sheet.ipynb` already does for one.
- Key every piece by `(sheet_index, label)` (D2). `PieceId.piece_id` is a
  descending-area ordinal and reorders between captures, so it is recorded but
  never joined on.
- Persist pieces and segments. `DatasetStore` in
  [sqlite_store.py](../../src/snap_fit/persistence/sqlite_store.py) already
  handles this shape; use it rather than inventing a format.
- Record the capture condition per photo from EXIF: app (HDR+ tag present or
  not), 35mm equivalent, digital zoom ratio, subject distance. The condition is
  the grouping key for phase 5 (D6).

### Assertions

Run as part of the ingest, not as a separate audit:

- exactly 4 pieces per capture,
- exactly 4 distinct labels per capture, matching `{A1, A2, B1, B2}`,
- for each sheet, the 4 captures agree on each label's board-space centroid to
  within a small tolerance. 4 px is the observed worst case, so assert at ~8 px
  to leave room without letting a real mix-up through.

### Annotation sheet

The artifact that goes to the human. It carries two questions over the same 12
pieces, so it is one sheet, not two (D12):

- the 12 piece crops rendered at a consistent scale (they are ~100x100 px in
  rectified space, so upscale for viewing), each tagged `s{N}:{LABEL}`,
- each piece's four edges marked and named `TOP` / `RIGHT` / `BOTTOM` / `LEFT`
  in the same orientation the code uses, so a written answer maps to an
  `EdgePos` without interpretation,
- each edge pre-filled with the majority-vote shape across the four conditions,
  with the 10 known split segments flagged for attention (D13),
- a text stub to fill in: confirmed shape per segment, and pairs written as
  `s0:A1 RIGHT <-> s2:B1 LEFT`.

Pick the crop from whichever condition survives phase 5's ranking least badly,
or from `x1` as the provisional default: it and `x5` agree with each other
throughout the bbox table, and `x1` has the least digital upscale.

## Out of scope

- Deciding which condition is best. Phase 5; here we only need crops good enough
  to annotate from.
- Any change to shape classification. Phase 3.
- Building the truth file itself. Phase 4 consumes what comes back.
- Promotion to `pipelines/` (D9), even though bulk ingest is a standing backlog
  candidate there. That call is made after the investigation, not during it.

## Done when

- All 12 photos ingest and persist in one run, with the assertions passing.
- Every piece is retrievable by `(sheet_index, label)` and carries its capture
  condition.
- The annotation sheet exists and has been handed over.
- `uv run pytest && uv run ruff check . && uv run pyright && uv run pre-commit run --all-files`
  passes.
