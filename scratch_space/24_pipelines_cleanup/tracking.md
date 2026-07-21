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
- The seed pair is authored as notebooks, not scripts (D6), because the value
  is interactive: tweaking generation parameters and validating ingest results.
- `pipelines/` is a mixed, flat, non-numbered folder (D7, D8); order and
  dependencies live in `pipelines/README.md`.
- Freshness is a periodic manual pass plus an import-only drift check, no CI
  execution (D9). Docs per entry are a file header plus the README index, with
  entries linking to existing guides rather than re-explaining (D10).
- The audit capability list becomes a `pipelines/backlog.md`, worked one item
  at a time with an explicit promote-or-reject per item (D11); the reject list
  is a durable artifact for re-evaluating future re-proposals (D17).
  `16_support.py` promotion is one such item (D12).
- No data is committed; each header documents how to recreate what it needs
  (D13).
- The seed pair is board generation + sheet ingest parameterized by preset, not
  green-only; white boards stay valid and default (D14). Named for the
  capability (`generate_board`, `ingest_sheet`), not "green".
- Agent-notebook interaction is an explicit convention (D15): use the
  vscode-notebook MCP server for live work, `NotebookEdit` as the no-kernel
  fallback, never hand-edit `.ipynb` JSON or shell out to nbconvert.
- The import-freshness check is one committed command emitting a report (D16),
  not logic re-derived each run.
- The green pair is the sole D4 exception: after the pipelines land, the two
  `23_green_background/` scripts are removed and the guide repointed (D18).
- Notebook output cleanup is a `make nbstrip` target over tracked notebooks, not
  a change to the `nbstripout --verify` gate (D19, rejects R4); the in-editor
  equivalent is the MCP `notebook_clear_all_outputs`.
- The agent-notebook convention lives at repo level in `AGENTS.md` +
  `.github/copilot-instructions.md`, covering all notebooks incl. future scratch
  experiments (D20). A repo-root `CLAUDE.md` importing copilot-instructions is
  added first as a prerequisite, own commit, no branch (D21), so it reaches
  Claude Code.
- `generate_board` defaults to the green preset with white and other knobs
  commented out for quick swap (D14, Q12).

## Phases

| #  | Phase                                    | Plan | Status |
| -- | ---------------------------------------- | ---- | ------ |
| 0  | Prerequisite: repo-root `CLAUDE.md` shim (own commit, D21) | tbd | draft |
| 1  | Conventions: README, repo agent-notes, backlog, nbstrip, import check | tbd | draft |
| 2  | `generate_board` notebook (preset-parameterized) | tbd | draft |
| 3  | `ingest_sheet` notebook                  | tbd  | draft  |
| 4  | Retire green scratch scripts, repoint guide (D18) | tbd | draft |
| 5  | Promote `src` gaps found in 2 and 3      | tbd  | draft  |
| 6  | Work the backlog, one item at a time     | tbd  | draft  |
| 7  | Keep README current; per-entry docs if needed | tbd | draft |

Status values: draft / planned / in progress / done / superseded / discarded.

Sub-plan files are intentionally not created yet (user hold). All open questions
Q1-Q14 are answered and folded in; the plan is decision-complete for a draft.
What remains are execution-time details owned by the sub-plans (see the final
review note in the Log), not user decisions.

## Log

Append-only. Newest at the bottom.

- 2026-07-21 : bootstrapped the plan folder from the user's sketch (useful code should not be in scratch_space; `pipelines/` holds state-of-the-art one-job entries; logic in `src`, notebooks are flat loops; long scripts get promoted).
- 2026-07-21 : found the prior audit at `scratch_space/20_piece_markers/13_pipelines_cleanup.md` (27 notebooks classified PIPELINE/EXPLORATION/MIXED, proposed `pipelines/` tree, migration mapping table). Kept its inventory as reference, rejected its migration plan per the user's correction that pipelines must not be a mesh of old things uplifted randomly.
- 2026-07-21 : ran a fresh mechanical audit into `00.1_audit_notebooks.md`: 28 notebooks, 4855 LOC, 37 inline def/class, 4 scripts. Notable findings: cell size is the clearest non-pipeline signal (442-line and 216-line cells exist); `20_piece_markers/16_support.py` is 268 LOC of coordinate-transform logic living outside `src`; the two `23_green_background/` scripts are already the target shape; 26/28 notebooks still import cleanly and only one uses a removed API, so staleness is currently shallow; no notebook stores outputs.
- 2026-07-21 : recorded D1-D5 and R1-R3, opened Q1-Q8 (first pipeline, notebook-vs-script, structure, freshness mechanism, docs tie-in, which capabilities qualify, what to do with 16_support.py, and whether pipelines can run without the gitignored `data/`). Phases sketched in this file only, no sub-plan files yet.
- 2026-07-21 : folded in the Q1-Q8 answers as D6-D13. Outcomes: seed = green-background pair as notebooks (D6); mixed flat non-numbered folder with README-driven order (D7, D8); freshness = manual pass + import drift check, no CI run (D9); docs = file header + README, link to guides (D10); audit becomes `pipelines/backlog.md` worked one item at a time (D11); 16_support.py is its own backlog item to dissect before promoting (D12); no committed data, headers document recreation (D13). Refined the phase sketch and phases table accordingly. Surfaced Q9-Q11 (notebook import-check mechanism; backlog file location/shape; whether the green scratch scripts stay after the notebooks exist). Sub-plans still not written, per user hold.
- 2026-07-22 : folded in two user notes plus the now-answered Q9-Q11. New decisions: seed pair is preset-parameterized (white still valid and default), named generate_board / ingest_sheet not "green" (D14); agent-notebook interaction is an explicit convention using the vscode-notebook MCP server, NotebookEdit fallback, never raw JSON or nbconvert (D15); import-freshness is one committed report command (D16, Q9); backlog is pipelines/backlog.md with a durable reject list (D17, Q10); the green scratch scripts are the one D4 exception and get removed + guide repointed once the pipelines land (D18, Q11). Checked the vscode-notebook MCP server live (responds; ~16 cell-level tools, runs the open notebook's kernel, reads outputs/images) and recorded the capability comparison in 00_start analysis. Added a retire-scratch phase (now phase 4). Surfaced Q12-Q13 (preset default; where the agent-notes live). Added nbconvert/nbstripout to cSpell. Sub-plans still not written, per user hold.
- 2026-07-22 : resolved the two final-pass items. Branch: the CLAUDE.md shim (phase 0) commits on this short-lived feat/pipeline-sketch branch, which merges to main soon, so the repo-wide shim reaches main quickly (D21 updated). Added a "superseded in part by D14" note on D6 (the pair is generate_board / ingest_sheet, preset-parameterized, not green-only; the notebook/interactive reasoning still holds). No commit made, no sub-plans, per user hold.
- 2026-07-22 : final review pass. Folded the answered Q14 as D21: add a repo-root CLAUDE.md importing @.github/copilot-instructions.md, as a prerequisite (phase 0), own commit, no branch. Firmed D16: the import check is a `make pipelines-check` target and the notebook case is feasible (audit already ran it, 26/28), with two conventions locked in phase 1 (script pipelines guard main(); the check imports, never executes bodies). Reviewed 00_start and tracking for remaining open questions: none block. Residual items are execution-time details owned by the sub-plans, not user decisions: where exactly the import-check/nbstrip targets live (both make targets), the per-item promote-vs-reject bar for the backlog (principle is D1, applied per item), and whether the green guide's inline code examples are trimmed or kept when repointed in phase 4. Recorded these as notes, not new questions.
- 2026-07-22 : folded in the nbstripout-cleanup note and the answered Q12-Q13. Confirmed the hook is `nbstripout --verify` (blocks a dirty commit, does not strip) and the repo already has a Makefile plus AGENTS.md and .github/copilot-instructions.md but no CLAUDE.md. Decided output cleanup is a `make nbstrip` target over `git ls-files '*.ipynb'`, keeping the verify gate, with the MCP `notebook_clear_all_outputs` as the in-editor equivalent (D19; rejected flipping the hook to auto-strip, R4). Q12: generate_board defaults to green with white/ring-size/grid-count commented for quick swap (folded into D14). Q13 -> D20: the agent-notebook convention lives repo-level (AGENTS.md + copilot-instructions.md) so it covers future scratch experiments too, pipelines links to it. Surfaced Q14: no CLAUDE.md exists, so repo instructions do not reach Claude Code; adding a CLAUDE.md import shim may be a spin-off. Added nbstrip to cSpell. Sub-plans still not written, per user hold.
