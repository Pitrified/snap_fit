---
status: draft
---

# Pipelines cleanup

## draft

Useful code should not live in `scratch_space`.

The empty `pipelines/` folder is where the state-of-the-art generation,
ingestion, and whatever-else workflows should live: well kept, up to date,
documented, each notebook or script doing one precise thing, easy to find.

Most of the logic belongs in `src`. A pipeline notebook should mostly be flat
loops that iterate over things and call into the library. A script that grows
too long is a candidate for promotion into `src`, or for becoming a notebook.

## analysis

### Current state

`pipelines/` is empty. Everything runnable lives in `scratch_space/`:
28 notebooks and 4 scripts, 4855 lines of notebook code, 37 `def`/`class`
definitions inline in cells. Full inventory in
[00.1_audit_notebooks.md](00.1_audit_notebooks.md).

The important framing, and the thing that shapes this whole effort: **most of
those notebooks are development notebooks**. They are code-heavy and largely
stale, and that is correct behavior for a prototype. They are not broken
pipelines waiting to be repaired. They are the R&D record.

### Prior art, and why its plan is not the plan

`scratch_space/20_piece_markers/13_pipelines_cleanup.md` already audited this
corpus and proposed a migration: a mapping table moving 13 chosen notebooks
into a numbered `pipelines/` tree, each "copy, clean up cell outputs, add
markdown headers".

Its inventory is still useful. Its plan is rejected (D2): copying old
development notebooks forward produces a directory of things that look
official but were written against a codebase that has since moved, with their
logic still in cells. That is a mesh of old things uplifted randomly, which is
the opposite of the goal.

### The shape being aimed at

A pipeline entry is thin because the library is not. Concretely:

- it does one precise thing, named so it can be found,
- its cells are short (roughly 5-20 lines), mostly flat loops,
- it imports from `src` and calls into it; it defines little or nothing,
- it runs top to bottom today, against the current API,
- it has a header saying what it does, what it needs, and what it produces.

`23_green_background/generate_green_board.py` and `ingest_green_sheet.py` are
the closest existing examples: thin, single-purpose, all logic in `src`, and
validated against real captures. They are the template, and the first
candidates.

The corollary is that writing a pipeline can be blocked on `src` not owning
some logic yet. When that happens, the promotion into `src` is the work, and
the pipeline is the thin thing that falls out afterwards.

### Agent interaction with notebooks (capability check 2026-07-21)

The pipelines will be edited and run by the AI agent as well as by hand, so the
mechanism matters: raw `.ipynb` is JSON, and hand-editing it or shelling out to
`nbconvert`/`nbstripout` produces exactly the mess this effort is trying to
avoid. Three mechanisms are available in the current VSCode setup:

- vscode-notebook MCP server (checked live, responds). ~16 cell-level tools
  operating on the *open* notebook by cell index: list/insert/edit/move/delete
  cells, `run_cell` against the running kernel, read outputs including images,
  clear outputs, kernel info, search. It targets the active notebook or a
  specific `notebook_uri`. This is the clean interactive path: structured cell
  ops, real kernel, no JSON handling. It requires the `.ipynb` to be open in
  VSCode (with no notebook open it says so and does nothing).
- `NotebookEdit` (native agent tool): structural cell edits to the `.ipynb`
  file by index without needing it open and without executing. The fallback for
  editing when no kernel/open notebook is in play.
- Raw `Write`/`Edit` on the `.ipynb` JSON, or `nbconvert` via the shell. These
  are the anti-patterns: fragile, output-noisy, and the source of the badly
  formatted notebook JSON and "mesh of nb runs" the user called out. (A
  scripted `nbstripout` still has a sanctioned use for output cleanup, D19.)

Direction: interactive work (tweak a param, run, read the plotted board) goes
through the MCP server; structural authoring when nothing is open uses
`NotebookEdit`; the raw-JSON and shell-nbconvert paths are avoided. A pre-commit
hook already strips outputs, so cells never need manual output cleanup. This is
written up as a convention rather than left implicit (D15).

## decisions

- D1: `pipelines/` holds a small number of high-quality, current, one-job
  entries. Being comprehensive is not a goal; being trustworthy is.
  Why: the value is that someone can open `pipelines/` and believe what they
  find, without checking its age against `src`.
- D2: Pipeline entries are authored fresh against the current API, not
  migrated from `scratch_space`.
  Why: the user's framing. Old development notebooks carry stale code and
  cell-resident logic; lifting them produces an official-looking mesh. Old
  notebooks may be read as reference while writing the new one, but the new
  file is written, not copied.
  Rejects the migration mapping table in `20_piece_markers/13_pipelines_cleanup.md`.
- D3: Logic lives in `src`; pipelines iterate. A pipeline that needs to define
  functions is a signal that `src` is missing something, and the promotion
  comes first.
  Why: stated rule. It also keeps the logic tested, since `src` has a suite and
  notebooks do not.
- D4: `scratch_space/` stays as it is, as the development and R&D record.
  Nothing is deleted or repaired there as part of this effort.
  Why: those notebooks are history and prototype evidence; their staleness is
  expected. Only genuinely useful, still-current code gets promoted out.
  Exception: the green pair scripts are removed once promoted (D18).
- D5: The audit informs the pipeline list but does not define it by mechanical
  translation. Each candidate is a deliberate choice.
  Why: follows from D1 and D2.
- D6: The seed is the green-background pair - board generation, then photo
  ingest - authored as notebooks, not scripts.
  Why: Q1. The value is interactive: an operator tweaks board-generation
  parameters and sees the composed board, and validates the ingest results
  (piece count, labels, overlays) after a run. That is a notebook use even
  though the underlying scripts already exist. The existing
  `23_green_background/` scripts are the reference the notebooks are written
  from, which is not a D2 violation since they are current, not stale.
- D7: Format is a per-entry choice. `pipelines/` is a mixed folder of notebooks
  and scripts; each new entry picks whichever fits its use.
  Why: Q2. Interactive/validation entries want a notebook; a pure batch step
  wants a script. No blanket rule.
- D8: Filenames are flat and not numbered. Order and dependencies live in
  `pipelines/README.md`. Subfolders are deferred until the count grows, and
  then cost only a move.
  Why: Q3. Numbering bakes an order into filenames that churns as entries are
  added; the README carries that instead and is easy to scan while small.
- D9: Freshness is a periodic manual pass plus a mechanical import check that
  catches blatant API drift. No CI execution of pipelines for now.
  Why: Q4. Running notebooks in CI needs data and time the project does not
  want to spend yet; an import-resolves check is cheap and catches the common
  breakage (a renamed or removed symbol). See Q9 for the notebook wrinkle.
- D10: Documentation per entry is a header in the file plus the
  `pipelines/README.md` index. No per-pipeline docs page by default.
  Why: Q5. A pipeline should be small enough not to need one. It links to an
  existing guide for the why (the green pipelines link to
  `docs/guides/green_background.md`) rather than re-explaining it. A dedicated
  docs page is added only if an entry later becomes complex or widely used.
- D11: The audit's capability list becomes a backlog file in `pipelines/`.
  Entries are promoted one at a time; each backlog item is explicitly assessed
  and either promoted to a real pipeline or rejected, until the backlog is
  emptied. No bulk migration.
  Why: Q6. This keeps D1 honest - the folder only ever grows by a deliberate
  per-item decision - while still recording every candidate so none is lost.
- D12: `20_piece_markers/16_support.py` is its own backlog item. Before moving
  it, pinpoint precisely what in it is useful and where it belongs (a
  coordinate-transform helper in `src`, or a `scripts/` folder), rather than
  relocating 268 lines wholesale.
  Why: Q7. It is the clearest "useful code outside src" case, but it is
  verification scaffolding; only the reusable core should land in `src`.
- D13: No dataset is committed as part of this effort. Each pipeline header
  documents the steps to recreate the data it needs. Whether to ship a minimal
  sample set (useful for CI and new users) is a per-pipeline decision, deferred
  to that pipeline.
  Why: Q8. `data/` is gitignored and large; the recreation steps are the
  portable substitute for now.
- D14: The seed pair is board generation and sheet ingest parameterized by
  background preset, not a green-only pair. White boards remain fully valid in
  both generation and ingest and stay the current default. "Green" is the
  motivating case, not a hardcoded mode.
  Why: user note. Naming follows: the entries are named for the capability
  (`generate_board`, `ingest_sheet`), not "green". A parameter cell selects the
  preset; the ingest side already handles a white board correctly because the
  mask only engages for green/blue via `derive_background_mask`.
  Refined per Q12: `generate_board` defaults to the green preset, with the white
  preset (and other knobs - ArUco ring size, grid piece count) present as
  commented-out alternatives in the parameter cell for a quick swap. Which knobs
  are exposed is decided when the pipeline is actually written, not now.
- D15: How the agent interacts with the notebooks is written up as an explicit
  convention, not left implicit. The clean path is the vscode-notebook MCP
  server (structured cell ops on the open notebook, real kernel, output/image
  read-back); `NotebookEdit` is the no-kernel fallback; raw `.ipynb` JSON edits
  and shell `nbconvert`/`nbstripout` runs are the avoided anti-patterns.
  Why: user note. It prevents the "mesh of nb runs and badly formatted" notebook JSON.
  Capability check is in the analysis section above. Placement is D20 (Q13).
- D16: The notebook import-freshness check (Q9) is a single committed command
  that emits a report, run in the periodic manual pass - not logic re-derived
  each time. It mechanizes the notebook case if feasible (extract and execute
  each notebook's import cells, as the audit prototyped), otherwise it checks
  scripts only and notebooks fall to the manual reading pass.
  Why: Q9. "Execute one command and get a report back", so the check is itself
  a small owned tool, consistent with D3 (logic is owned, not scattered).
- D17: The backlog is `pipelines/backlog.md`: a candidate list with a
  promote/reject status per item. The reject list is a durable artifact, so a
  future proposal to add the same capability is evaluated against the prior
  rejection and can reopen it deliberately.
  Why: Q10. Keeps the product-side list with the product, while the plan folder
  tracks overall progress. The retained rejections stop the folder churning on
  re-proposals.
- D18: The green pair is the one exception to D4. Once the `generate_board` and
  `ingest_sheet` pipelines exist and are validated, the
  `23_green_background/generate_green_board.py` and `ingest_green_sheet.py`
  scripts are removed and the docs that reference them (the
  `green_background` guide) are updated to point at the pipelines.
  Why: Q11. Leaving two runnable copies invites drift; the promoted-from
  scripts have no further role once the maintained pipelines exist. This is a
  narrow, deliberate carve-out from D4, which otherwise still holds for the R&D
  notebooks.
- D19: Output cleanup is a `make` target, not a hook change. The pre-commit
  `nbstripout --verify` hook blocks a commit when a notebook carries outputs but
  does not strip them, so a one-command cleaner is needed. Add e.g. `make
  nbstrip` running `uv run nbstripout` over the tracked notebooks
  (`git ls-files '*.ipynb'`, so it targets exactly what the hook verifies). The
  agent working in the editor has an equivalent that needs no shell:
  the MCP `notebook_clear_all_outputs`.
  Why: user note, and it fits the repo. Options weighed:
  - make target (chosen): matches the existing Makefile idiom, one discoverable
    command via `make help`, tool-agnostic (human or CI), and leaves the hook's
    gate intact. Con: must be remembered; does not auto-fire.
  - flip the hook to auto-strip (drop `--verify`): con - silently mutates the
    working tree on commit and forces a re-add/re-commit dance, and it reverses
    a deliberate existing policy. Rejected (R4).
  - git filter via `nbstripout --install`: transparent but per-clone local
    state, more magic, and awkward alongside the MCP-run workflow. Not chosen.
  The make target and the MCP clear are complementary: the target is the
  canonical CLI cleaner, the MCP call is the in-editor shortcut.
- D20: The agent-notebook convention (D15) lives at repo level, not only in
  `pipelines/`, so it governs any notebook work including future `scratch_space`
  experiments. Home is the existing shared instruction files (`AGENTS.md` and
  `.github/copilot-instructions.md`); `pipelines/` links to it rather than
  duplicating.
  Why: Q13. The user's point is that clean tooling should apply to every
  notebook, not just pipelines. See Q14 for how this reaches Claude Code, which
  has no `CLAUDE.md` in this repo today.

Rejected alternatives:

- R1: Migrate the 13 notebooks named by the prior audit. Rejected per D2.
- R2: Fix the stale notebooks in place in `scratch_space`. Rejected per D4:
  they are development artifacts, and there is no end to that work.
- R3: Make `pipelines/` a mirror of every capability the codebase has.
  Rejected per D1: coverage for its own sake reintroduces unmaintained files.
- R4: Flip the `nbstripout` hook from `--verify` to auto-strip. Rejected per
  D19: it silently mutates the working tree on commit and reverses a deliberate
  gate; the clean is added as a command, the check stays a check.

## open questions

- Q1: What is the first pipeline to write, and is the green-background pair
  (board generation, then photo ingest) the right seed given it is the most
  recently validated workflow?
  ANS: yes, but uplift to notebook: user might want to change the board generation parameters and see the result, so a notebook is more appropriate than a script for that first entry. same for ingestion, which is a one-shot operation but benefits from a notebook for exploration and validation of the ingest results.
- Q2: Notebooks, scripts, or both in `pipelines/`? Generation and ingest are
  currently scripts and work well as scripts (runnable, diffable, no output
  noise), while exploration-flavored steps benefit from a notebook. A mixed
  folder needs a convention for which is which.
  ANS: mixed, to be evaluated for each new entry.
- Q3: What is the flat structure? Options: flat numbered files
  (`01_generate_board.ipynb`), or numbered subfolders by domain as the prior
  audit proposed (`01_board_generation/`). Flat is easier to scan while the
  count is small.
  ANS: not numbered, flat for now. we keep a clean `pipelines/README.md` index to show the order and dependencies, and we can add subfolders later if the count grows with minimal moves.
- Q4: What keeps them up to date, mechanically? Nothing executes notebooks
  today, so "up to date" decays silently. Options: a smoke-run in CI, a
  periodic manual pass, a test that imports each pipeline module, or accepting
  drift and dating each entry.
  ANS: periodic manual pass, no smoke in CI for now. mechanical test of import is ok to catch blatant API drift for now.
- Q5: Does each pipeline need a matching docs page, or is a header inside the
  file plus a `pipelines/README.md` index enough? The docs wiki already has a
  guide-writing procedure and a `green_background` guide that overlaps with the
  first candidate pipelines.
  ANS: header inside the file plus a `pipelines/README.md` index is enough for now. individual docs pages can be added later if a pipeline becomes complex or widely used. in general, pipelines should not be complex, but do a small thing. there is no need to explain the logic behind the green background in the pipeline itself, it can link to the guide for that.
- Q6: Which capabilities from the audit are actually wanted as pipelines?
  The candidate list is board generation, photo ingest, bulk ingest to
  SQLite, segment matching, grid and scoring, solving, synthetic puzzle
  generation, and sheet identity. Some of those may be better as docs only.
  ANS: we can promote the audit to a `backlog` we place in `pipelines`. we start with the board generation + simple ingestion, we add one pipeline at a time, no megadump. we assess each backlog and reject or promote it until we conclude.
- Q7: `20_piece_markers/16_support.py` (268 LOC of coordinate transform
  verification) is the clearest "useful code outside src" case found. Promote
  it into `src` (as a coordinate-transform helper), turn it into a test, or
  leave it as a one-off verification script?
  ANS: we can mark it to promotion in `src` or in a `scripts` folder. will have it's own phase in the backlog, we need to pinpoint precisely why it's useful and what to uplift.
- Q8: Do pipelines need to run without the private `data/` folder present?
  They all depend on datasets that are gitignored, so a fresh clone cannot run
  them. That affects whether CI can check them at all.
  ANS: we can assess for each pipeline whether we can ship the minimal sample set, which would be useful for CI and in general for new users. deferred to each pipeline. for now we do not commit any data, just mark the steps needed to recreate the data in the header.

Batch Q9-Q11 surfaced 2026-07-21 while folding in the Q1-Q8 answers.

- Q9: The D9 import check needs a wrinkle for notebooks. D6 makes the first two
  entries notebooks, but an import test naturally targets `.py` modules, not
  `.ipynb`. The audit already prototyped the workaround (extract the import
  cells from each notebook and execute just those; 26/28 resolved). Is that
  extract-and-exec-imports harness the mechanism, or do we restrict the check
  to script entries and cover notebooks only in the manual pass?
  ANS: if we can mechanize the import check for notebooks, we do that. if not, we restrict the check to scripts and cover notebooks only in the manual pass. we do not regenerate the logic to do the check every time, we just execute one command and get a report back.
- Q10: Where does the backlog file live and what is its shape? D11 says "in
  `pipelines/`", so `pipelines/backlog.md`. That places a process/tracking file
  inside the product folder, slightly at odds with the plan folder owning
  tracking. Confirm `pipelines/backlog.md` (a candidate list with a
  promote/reject status per item), versus keeping the backlog here in the plan
  folder and only surfacing accepted entries in `pipelines/README.md`.
  ANS: `pipelines/backlog.md` is the right place. It is a candidate list with a promote/reject status per item. The plan folder tracks the overall progress, but the backlog itself lives with the pipelines. the reject list is an artifact itself, so that future proposals to add the same capability can be evaluated against the prior rejection and reassess it.
- Q11: Once the green pipeline notebooks exist, the two
  `23_green_background/` scripts become redundant runnable copies of the same
  thin logic. D4 says leave `scratch_space` alone, which keeps them as feature
  history. Is that the intent (two callers, both valid, one frozen), or is the
  promoted-from script the one case where deleting the scratch original is
  warranted to avoid drift?
  ANS: we can clean up the scratch space for this pair, update docs so that they point to the new pipelines.

Batch Q12-Q13 surfaced 2026-07-22 while folding in the two user notes
(preset exposure, agent-notebook interaction).

- Q12: What preset does the `generate_board` notebook default to? White keeps
  parity with the current global default and the "white boards still valid"
  intent; green is the workflow actually being driven right now. Either way the
  preset is a parameter cell; this only sets the default value.
  ANS: green, but leave the white one commented out for quick swap. also leave commented out some other presets, eg changing the size of the aruco rings, the number of pieces inside in the grid and so on. features will be assessed in the actual phase for the pipeline migration.
- Q13: Where does the D15 agent-interaction convention live: a section inside
  `pipelines/README.md`, or a separate support file (for example
  `pipelines/AGENTS.md` or `pipelines/agent_notes.md`)? A separate file is
  easier for an agent to load in isolation; a README section keeps everything
  in one place while the folder is small.
  ANS: `pipelines/AGENTS.md`. or really repo level in `.github` or the equivalent for claude, if we do a notebook in scratch in future experiments we want to use a clean tooling.

Batch Q14 surfaced 2026-07-22 while folding in the nbstripout mechanism and the
repo-level placement of D20.

- Q14: The repo has `AGENTS.md` and `.github/copilot-instructions.md` but no
  `CLAUDE.md`, so Claude Code does not auto-load the repo instructions today.
  The user's own global convention is that each repo carries a `CLAUDE.md` that
  imports `@.github/copilot-instructions.md`. For D20's repo-level notebook
  convention to actually reach Claude Code, do we add that `CLAUDE.md` import
  shim (small, matches the convention, also surfaces every existing repo
  instruction to Claude), or leave it and rely on AGENTS.md only? This is
  arguably its own tiny task, possibly a spin-off rather than part of this
  effort.
  ANS: add the claude import shim. it is small, matches the user's convention, and surfaces every existing repo instruction to claude. it can be a separate task, but it is a small one.

## proposed phase sequence

Refined 2026-07-22 after folding Q1-Q13 and the two user notes. Still a sketch;
sub-plan files are not written yet.

1. Conventions and scaffolding. Write `pipelines/README.md` (index plus the
   header/format conventions from D7-D10); put the D15 agent-interaction
   convention at repo level (D20, `AGENTS.md` + `.github/copilot-instructions.md`,
   pending Q14 for the Claude Code shim); seed `pipelines/backlog.md` from the
   audit capability list with promote/reject status (D11, D17); add the
   `make nbstrip` output cleaner (D19); and add the import-freshness check as a
   single committed command (D9, D16, mechanism per Q9).
2. First pipeline: `generate_board` as a notebook (D6). A parameter cell defaults
   to the green preset with white and other knobs (ring size, grid count)
   commented out for a quick swap (Q12, D14); thin cells call
   `BoardImageComposer` + `derive_background_mask`, show the composed board, and
   save. Reference: `23_green_background/generate_green_board.py`.
   Expected to need no `src` change (logic already there).
3. Second pipeline: `ingest_sheet` as a notebook (D6). Decode QR, resolve config
   by id, `load_sheet`, then display piece count/labels/overlays for validation.
   White and green ingest alike (D14). Reference: `23_green_background/ingest_green_sheet.py`.
4. Retire the green scratch scripts (D18): remove
   `23_green_background/generate_green_board.py` and `ingest_green_sheet.py`,
   and repoint the `green_background` guide at the new pipelines.
5. Promote any `src` gaps the seed pair exposed. Likely near-empty for the green
   pair; kept as a distinct step so the pattern is set for later capabilities.
6. Work the backlog one item at a time (D11), each with its own assess-then
   promote-or-reject pass. `16_support.py` (D12) is one such item.
7. Keep `pipelines/README.md` current as entries land; add a docs page for an
   entry only if D10's complexity trigger is hit.
