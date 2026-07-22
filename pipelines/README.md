# pipelines

Current, trusted, one-job workflows for snap_fit. Open any entry and rely on it
without checking its age against `src`. This is the opposite of `scratch_space/`,
which is the development and R&D record and is expected to be stale.

Backlog of candidate pipelines: [backlog.md](backlog.md).

## What a pipeline is

- It does one precise thing, named for the capability so it is easy to find.
- Its cells (or a script's body) are thin: mostly flat loops that call into
  `src`. It defines little or nothing itself.
- All real logic lives in `src`. If an entry needs to define a function, that
  logic belongs in `src` first (with a test); the entry then just calls it.
- It runs top to bottom against the current API.
- It carries a header (a top markdown cell, or a module docstring) saying what
  it does, what it needs, and what it produces, and linking to a guide for the
  why rather than re-explaining it.

## Conventions

- Format is per entry: a notebook when the value is interactive (tweak a
  parameter, see the result, validate a run), a script when it is a batch step.
- Filenames are flat and not numbered. This README carries the order and
  dependencies. Subfolders come only if the count grows.
- No dataset is committed. Each entry's header documents how to recreate the
  data it needs.
- Script entries must guard their work under `if __name__ == "__main__"`, so the
  import check can import them without running them.
- Agent-driven notebook work follows the repo convention in
  `.github/copilot-instructions.md`: use the VS Code notebook MCP server for
  live cell work, never hand-edit `.ipynb` JSON, and clean outputs with
  `make nbstrip`.

## Freshness

Nothing runs these in CI. Two commands keep them honest:

- `make pipelines-check` - imports every entry against the current API and
  reports drift (a renamed or removed symbol). Run it in a periodic manual pass.
- `make nbstrip` - strips notebook outputs before commit (the `nbstripout`
  pre-commit hook verifies and blocks, it does not strip). The in-editor
  equivalent is the MCP `notebook_clear_all_outputs`.

## Index

Order and dependencies of the current entries.

| Entry | Does | Needs | Guide |
| ----- | ---- | ----- | ----- |
| _(none yet)_ | | | |
