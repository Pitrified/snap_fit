# implementation tracking

Moving the state-of-the-art workflows out of `scratch_space` and into the
empty `pipelines/` folder: a small set of well kept, current, one-job entries
whose logic lives in `src` and whose cells are mostly flat loops. Analysis and
decisions in [00_start.md](00_start.md); the inventory that informs it is in
[00.1_audit_notebooks.md](00.1_audit_notebooks.md).

Early stage: everything here is draft, and the phases are a sketch pending the
open questions in `00_start.md`.

## Key decisions

- `pipelines/` is small, current, and trustworthy rather than comprehensive
  (D1). Coverage for its own sake reintroduces unmaintained files.
- Entries are authored fresh against the current API, never migrated from
  `scratch_space` (D2). This rejects the migration mapping table in
  `20_piece_markers/13_pipelines_cleanup.md`, whose inventory is still useful
  but whose plan would produce a mesh of stale things uplifted randomly.
- Logic lives in `src`, pipelines iterate (D3). A pipeline that needs to define
  functions means `src` is missing something, and that promotion comes first.
- `scratch_space/` is left alone as the development and R&D record (D4). Its
  notebooks are code-heavy and stale because that is what prototypes are; they
  are not broken pipelines awaiting repair.
- The `23_green_background/` scripts are the template for the target shape and
  the first pipeline candidates: thin, single-purpose, all logic in `src`, and
  validated on real captures.

## Phases

| #  | Phase                                   | Plan | Status |
| -- | --------------------------------------- | ---- | ------ |
| 1  | Settle conventions and structure        | tbd  | draft  |
| 2  | Seed pipelines with board generation    | tbd  | draft  |
| 3  | Add the photo ingest counterpart        | tbd  | draft  |
| 4  | Promote the `src` gaps found in 2 and 3 | tbd  | draft  |
| 5  | Extend to the remaining agreed capabilities | tbd | draft |
| 6  | Index and docs tie-in                   | tbd  | draft  |

Status values: draft / planned / in progress / done / superseded / discarded.

Sub-plan files are intentionally not created yet: the phase split depends on
the answers to Q1-Q8.

## Log

Append-only. Newest at the bottom.

- 2026-07-21 : bootstrapped the plan folder from the user's sketch (useful code should not be in scratch_space; `pipelines/` holds state-of-the-art one-job entries; logic in `src`, notebooks are flat loops; long scripts get promoted).
- 2026-07-21 : found the prior audit at `scratch_space/20_piece_markers/13_pipelines_cleanup.md` (27 notebooks classified PIPELINE/EXPLORATION/MIXED, proposed `pipelines/` tree, migration mapping table). Kept its inventory as reference, rejected its migration plan per the user's correction that pipelines must not be a mesh of old things uplifted randomly.
- 2026-07-21 : ran a fresh mechanical audit into `00.1_audit_notebooks.md`: 28 notebooks, 4855 LOC, 37 inline def/class, 4 scripts. Notable findings: cell size is the clearest non-pipeline signal (442-line and 216-line cells exist); `20_piece_markers/16_support.py` is 268 LOC of coordinate-transform logic living outside `src`; the two `23_green_background/` scripts are already the target shape; 26/28 notebooks still import cleanly and only one uses a removed API, so staleness is currently shallow; no notebook stores outputs.
- 2026-07-21 : recorded D1-D5 and R1-R3, opened Q1-Q8 (first pipeline, notebook-vs-script, structure, freshness mechanism, docs tie-in, which capabilities qualify, what to do with 16_support.py, and whether pipelines can run without the gitignored `data/`). Phases sketched in this file only, no sub-plan files yet.
