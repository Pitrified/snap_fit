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
- D5: The audit informs the pipeline list but does not define it by mechanical
  translation. Each candidate is a deliberate choice.
  Why: follows from D1 and D2.

Rejected alternatives:

- R1: Migrate the 13 notebooks named by the prior audit. Rejected per D2.
- R2: Fix the stale notebooks in place in `scratch_space`. Rejected per D4:
  they are development artifacts, and there is no end to that work.
- R3: Make `pipelines/` a mirror of every capability the codebase has.
  Rejected per D1: coverage for its own sake reintroduces unmaintained files.

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

## proposed phase sequence

Sketch only, not agreed. Phases are not written as sub-plan files yet, pending
the answers above.

1. Settle the conventions: structure, notebook-versus-script rule, header
   format, and the freshness mechanism.
2. Seed `pipelines/` with the first entry end to end (likely board generation),
   proving the shape and the conventions on a real case.
3. Add the ingest counterpart, so the pair covers the current live workflow.
4. Promote the identified `src` gaps found while writing those two.
5. Extend to the remaining agreed capabilities, one at a time.
6. Index and document: `pipelines/README.md`, plus whatever docs wiki tie-in
   Q5 settles on.
