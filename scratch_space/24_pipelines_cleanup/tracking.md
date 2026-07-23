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
| 0  | Prerequisite: repo-root `CLAUDE.md` shim (own commit, D21) | [00.2_claude_shim.md](00.2_claude_shim.md) | done |
| 1  | Conventions: README, repo agent-notes, backlog, nbstrip, import check | [01_conventions.md](01_conventions.md) | done |
| 2  | `generate_board` notebook (preset-parameterized) | [02_generate_board.md](02_generate_board.md) | done |
| 3  | `ingest_sheet` notebook                  | [03_ingest_sheet.md](03_ingest_sheet.md)  | draft  |
| 4  | Retire green scratch scripts, repoint guide (D18) | [04_retire_green_scratch.md](04_retire_green_scratch.md) | draft |
| 5  | Promote `src` gaps found in 2 and 3      | [05_promote_src_gaps.md](05_promote_src_gaps.md)  | draft  |
| 6  | Work the backlog, one item at a time     | [06_work_the_backlog.md](06_work_the_backlog.md)  | draft  |
| 7  | Keep README current; per-entry docs if needed | [07_readme_upkeep.md](07_readme_upkeep.md) | draft |

Status values: draft / planned / in progress / done / superseded / discarded.

All eight sub-plan files exist (status draft). Phase 0 is `00.2_claude_shim.md`
because `00_start.md` and `00.1_audit_notebooks.md` already hold the `00` slot;
phases 1-7 are files `01`-`07`, so file numbers match phase numbers. All open
questions Q1-Q14 are answered; the plan is decision-complete for a draft.

## Log

Append-only. Newest at the bottom.

- 2026-07-21 : bootstrapped the plan folder from the user's sketch (useful code should not be in scratch_space; `pipelines/` holds state-of-the-art one-job entries; logic in `src`, notebooks are flat loops; long scripts get promoted).
- 2026-07-21 : found the prior audit at `scratch_space/20_piece_markers/13_pipelines_cleanup.md` (27 notebooks classified PIPELINE/EXPLORATION/MIXED, proposed `pipelines/` tree, migration mapping table). Kept its inventory as reference, rejected its migration plan per the user's correction that pipelines must not be a mesh of old things uplifted randomly.
- 2026-07-21 : ran a fresh mechanical audit into `00.1_audit_notebooks.md`: 28 notebooks, 4855 LOC, 37 inline def/class, 4 scripts. Notable findings: cell size is the clearest non-pipeline signal (442-line and 216-line cells exist); `20_piece_markers/16_support.py` is 268 LOC of coordinate-transform logic living outside `src`; the two `23_green_background/` scripts are already the target shape; 26/28 notebooks still import cleanly and only one uses a removed API, so staleness is currently shallow; no notebook stores outputs.
- 2026-07-21 : recorded D1-D5 and R1-R3, opened Q1-Q8 (first pipeline, notebook-vs-script, structure, freshness mechanism, docs tie-in, which capabilities qualify, what to do with 16_support.py, and whether pipelines can run without the gitignored `data/`). Phases sketched in this file only, no sub-plan files yet.
- 2026-07-21 : folded in the Q1-Q8 answers as D6-D13. Outcomes: seed = green-background pair as notebooks (D6); mixed flat non-numbered folder with README-driven order (D7, D8); freshness = manual pass + import drift check, no CI run (D9); docs = file header + README, link to guides (D10); audit becomes `pipelines/backlog.md` worked one item at a time (D11); 16_support.py is its own backlog item to dissect before promoting (D12); no committed data, headers document recreation (D13). Refined the phase sketch and phases table accordingly. Surfaced Q9-Q11 (notebook import-check mechanism; backlog file location/shape; whether the green scratch scripts stay after the notebooks exist). Sub-plans still not written, per user hold.
- 2026-07-22 : folded in two user notes plus the now-answered Q9-Q11. New decisions: seed pair is preset-parameterized (white still valid and default), named generate_board / ingest_sheet not "green" (D14); agent-notebook interaction is an explicit convention using the vscode-notebook MCP server, NotebookEdit fallback, never raw JSON or nbconvert (D15); import-freshness is one committed report command (D16, Q9); backlog is pipelines/backlog.md with a durable reject list (D17, Q10); the green scratch scripts are the one D4 exception and get removed + guide repointed once the pipelines land (D18, Q11). Checked the vscode-notebook MCP server live (responds; ~16 cell-level tools, runs the open notebook's kernel, reads outputs/images) and recorded the capability comparison in 00_start analysis. Added a retire-scratch phase (now phase 4). Surfaced Q12-Q13 (preset default; where the agent-notes live). Added nbconvert/nbstripout to cSpell. Sub-plans still not written, per user hold.
- 2026-07-22 : aligned the lint tooling (user follow-up to phase 1). make lint, pre-commit, and the editor now share ruff.toml + [tool.pyright] scope. Excluded scratch notebooks from ruff (`extend-exclude = scratch_space/**/*.ipynb` + `force-exclude`) so all three stop flagging R&D notebooks (D4); added `jupyter` to the pre-commit ruff/ruff-format hooks so pipeline notebooks get linted at commit; added `scripts` to pyright include and expanded `make lint` to ruff check + ruff format --check + pyright. Whole-project pyright immediately caught a real latent bug from the phase-3 refactor: sheet_record.py:60 still read the removed `Sheet.threshold`; the pre-commit pyright hook missed it because it only checks staged files and sheet_record.py was never staged in that commit. Fixed it to `sheet.preprocess_config.threshold` and updated the tests that had masked it by setting `sheet.threshold` on mocks (test_sheet_record.py, test_sheet_manager.py). Verified: 405 pass, make lint clean, pre-commit run --all-files all-pass. Uncommitted, alongside phase 1.
- 2026-07-22 : phase 1 done (not committed; user asked to do p1, not commit it). Created pipelines/README.md (what a pipeline is, conventions, freshness, empty index) and pipelines/backlog.md (9 candidate rows seeded from the audit, promote/reject status). Added the notebook convention to .github/copilot-instructions.md only (per user edit to the sub-plan, not AGENTS.md): MCP server for live work, NotebookEdit fallback, never raw JSON/nbconvert, make nbstrip for outputs; also repointed the stale nbstripout hint to `make nbstrip`. Added scripts/check_pipeline_imports.py (imports scripts, execs only notebook import cells after stripping magics; reports and exits nonzero on failure) plus Makefile targets `nbstrip` and `pipelines-check`, and a scripts/** ruff ignore block (INP001/T20/S102/BLE001). Validated the checker: real main-guarded scripts pass, a fabricated bad import in both a script and a notebook fails with exit 1; make pipelines-check is green on the empty pipelines folder; make nbstrip is a clean no-op. Note: `ruff check .` surfaces 5 pre-existing lint errors in scratch_space notebooks (00_sample, 01_print_read_board), untouched here per D4 and not blocked by the python-only ruff hook.
- 2026-07-22 : phase 0 done. Added repo-root CLAUDE.md importing @.github/copilot-instructions.md (85-line target, resolves), so Claude Code now auto-loads the repo instructions. Committed on its own on feat/pipeline-sketch (D21). Phase 1 next.
- 2026-07-22 : wrote all eight sub-plan files (00.2_claude_shim, 01_conventions, 02_generate_board, 03_ingest_sheet, 04_retire_green_scratch, 05_promote_src_gaps, 06_work_the_backlog, 07_readme_upkeep), all status draft, and linked them from the phases table. Phase 0 named 00.2 to avoid colliding with 00_start/00.1_audit; phases 1-7 are files 01-07 so file number == phase number. Phases 0-3 detailed fully; 4-7 lighter but with goals and done-when. No code written, no commit.
- 2026-07-22 : resolved the two final-pass items. Branch: the CLAUDE.md shim (phase 0) commits on this short-lived feat/pipeline-sketch branch, which merges to main soon, so the repo-wide shim reaches main quickly (D21 updated). Added a "superseded in part by D14" note on D6 (the pair is generate_board / ingest_sheet, preset-parameterized, not green-only; the notebook/interactive reasoning still holds). No commit made, no sub-plans, per user hold.
- 2026-07-22 : final review pass. Folded the answered Q14 as D21: add a repo-root CLAUDE.md importing @.github/copilot-instructions.md, as a prerequisite (phase 0), own commit, no branch. Firmed D16: the import check is a `make pipelines-check` target and the notebook case is feasible (audit already ran it, 26/28), with two conventions locked in phase 1 (script pipelines guard main(); the check imports, never executes bodies). Reviewed 00_start and tracking for remaining open questions: none block. Residual items are execution-time details owned by the sub-plans, not user decisions: where exactly the import-check/nbstrip targets live (both make targets), the per-item promote-vs-reject bar for the backlog (principle is D1, applied per item), and whether the green guide's inline code examples are trimmed or kept when repointed in phase 4. Recorded these as notes, not new questions.
- 2026-07-22 : folded in the nbstripout-cleanup note and the answered Q12-Q13. Confirmed the hook is `nbstripout --verify` (blocks a dirty commit, does not strip) and the repo already has a Makefile plus AGENTS.md and .github/copilot-instructions.md but no CLAUDE.md. Decided output cleanup is a `make nbstrip` target over `git ls-files '*.ipynb'`, keeping the verify gate, with the MCP `notebook_clear_all_outputs` as the in-editor equivalent (D19; rejected flipping the hook to auto-strip, R4). Q12: generate_board defaults to green with white/ring-size/grid-count commented for quick swap (folded into D14). Q13 -> D20: the agent-notebook convention lives repo-level (AGENTS.md + copilot-instructions.md) so it covers future scratch experiments too, pipelines links to it. Surfaced Q14: no CLAUDE.md exists, so repo instructions do not reach Claude Code; adding a CLAUDE.md import shim may be a spin-off. Added nbstrip to cSpell. Sub-plans still not written, per user hold.
- 2026-07-23 : fleshed out phase 2 (02_generate_board.md, draft -> planned) into a concrete, decision-complete plan against the reference `23_green_background/generate_green_board.py`. Named the real symbols (BoardImageComposer, derive_background_mask, ArucoBoardConfig/MetadataZoneConfig/SlotGridConfig/SheetArucoConfig, SheetMetadata/Decoder) and laid out 8 thin cells: header, isolated imports cell (so scripts/check_pipeline_imports.py picks up the notebook), parameter cell (green default, white + min_area=5000 scale note + ring/qr knobs commented for swap), config-build + derive_background_mask, compose-and-save loop writing sheet_XX.png + two config JSONs, inline BGR->RGB display, and the flattened verify (QR round-trip + mask-enabled assertions, no `def` per D3, unlike the reference's `_verify`). Added guardrails (any needed def is a phase-5 src promotion; no data committed per D13) and the scaffolding wire-up (README index row, backlog row candidate -> promoted). No code written yet.
- 2026-07-23 : phase 2 done (02_generate_board.md -> done). Authored `pipelines/generate_board.ipynb` fresh (D2) via NotebookEdit (no kernel was open): 1 header markdown + 7 thin code cells, no `def`/`class` inline (D3). Confirmed the reference imports/signatures still resolve against current src (BoardImageComposer.compose/__init__ unchanged) and that background_preset is Literal["white","green","blue"] with _MASKED_PRESETS={"green","blue"}, so the mask-validation cell matches src. Verified: ruff clean on the notebook; `make pipelines-check` green (1/1, import cell isolated as designed); ran the code cells end-to-end in a headless process (not the notebook itself) - 2 boards composed 940x1340, PNGs + both config JSONs saved under the gitignored data/aruco_boards/greendemo (D13, confirmed check-ignore), QR round-trips on both, mask enabled mode=as_threshold. `make nbstrip` clean (notebook never executed in-place, no outputs). Wired scaffolding: README index row added, backlog "Board generation" row candidate -> promoted. Not committed. Note: full in-kernel run + inline board display is left for the user to eyeball with the notebook open in VS Code.
