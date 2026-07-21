---
status: draft
---

# Phase 1 - Conventions and scaffolding

## Overview

Lay down the rules and tooling before any pipeline exists, so the first entries
are written into a shaped folder rather than shaping it retroactively.
Context: [00_start.md](00_start.md), depends on
[00.2_claude_shim.md](00.2_claude_shim.md). Decisions D7-D11, D15-D20.

## Goals

1. A `pipelines/README.md` that states what a pipeline is and indexes entries.
2. The agent-notebook interaction convention recorded at repo level.
3. A `pipelines/backlog.md` seeded from the audit, with promote/reject status.
4. The output-cleanup and import-freshness commands as `make` targets.

## Plan

1. `pipelines/README.md`:
   - what a pipeline is (D1, D3): thin, one job, cells are flat loops of 5-20
     lines, logic in `src`, runs against the current API, header per file.
   - the header format (D10): what it does, what it needs, what it produces,
     and a link to the relevant guide instead of re-explaining.
   - the format-per-entry rule (D7) and the flat, non-numbered naming with the
     README carrying order and dependencies (D8).
   - an index table (empty at first; entries added as they land).
   - a pointer to the agent-notebook convention (item 2).
2. Agent-notebook convention (D15, D20): add a section to
   `.github/copilot-instructions.md` covering: use the
   vscode-notebook MCP server for live cell work, `NotebookEdit` when no kernel
   is open, never hand-edit `.ipynb` JSON or shell out to `nbconvert`, and clean
   outputs with `make nbstrip` or the MCP `notebook_clear_all_outputs`. It is
   repo-level so it also governs future `scratch_space` notebooks. Reached by
   Claude via the phase 0 shim.
3. `pipelines/backlog.md` (D11, D17): seed from the audit capability table in
   [00.1_audit_notebooks.md](00.1_audit_notebooks.md). One row per candidate
   with a status (candidate / promoted / rejected) and a rationale column. The
   rejected rows stay as a durable record. `16_support.py` (D12) is a row.
4. `Makefile`:
   - `nbstrip` (D19): `uv run nbstripout $(git ls-files '*.ipynb')`, matching
     exactly what the `nbstripout --verify` hook checks.
   - `pipelines-check` (D9, D16): run the import-freshness check and print a
     report. Add both with the repo's `## help` comment style.
5. The import-check tool (D16): a small committed script (e.g.
   `scripts/check_pipeline_imports.py`) that, for each pipeline, imports scripts
   and executes only the import cells of notebooks (the audit already proved
   this works, 26/28), and reports failures. It imports, never executes bodies;
   this is why script pipelines must guard work under `if __name__ == "__main__"`
   (state that rule in the README).

## Out of scope

- Writing any pipeline (phases 2+).
- Executing the backlog items (phase 6).

## Done when

- `pipelines/README.md`, `pipelines/backlog.md`, and the repo-level agent
  convention exist.
- `make nbstrip` strips tracked notebooks and `make pipelines-check` runs and
  reports (green on the empty/near-empty folder).
- The README states the pipeline shape, header format, naming, and the
  `__main__`-guard rule for scripts.
