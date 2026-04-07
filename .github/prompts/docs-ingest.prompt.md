---
description: "Ingest a completed scratch_space folder or notebook into the docs wiki. Extracts validated patterns and examples from scratch_space sources and compiles them into docs/library/ pages. Use when a prototype is considered done and its knowledge should be persisted."
argument-hint: "<scratch_space folder path, e.g. scratch_space/piece_matcher/>"
agent: "docs_agent"
tools: [read, edit, search]
---

Process the provided `scratch_space/` folder (or single notebook) into `docs/`.

The `scratch_space/` directory is the source of raw, exploratory knowledge in this project. This
prompt compiles that knowledge into the persistent wiki under `docs/`. The human has already
validated the content - your job is extraction, structuring, and filing.

## Procedure

1. **Identify the source.**
   If a folder was provided, read all files in it: notebooks (`.ipynb`), markdown plans
   (`*.md`), and any Python scripts. If a single notebook was provided, read only that file.

2. **Extract validated knowledge.**
   From the notebooks: read all completed cells (skip cells marked as abandoned or experimental).
   From plan files: read the "validated" or "conclusion" sections if present.
   Identify:
   - Which `src/snap_fit/` modules are demonstrated or described.
   - Key usage patterns (instantiation, method calls, parameter choices).
   - Surprising behaviours, errors encountered, and their resolutions (pitfalls).
   - Any data shapes or type constraints that are not obvious from the source code alone.
   Cross check with final `src/` files to check actual implementation.

3. **Map to docs/library/ pages.**
   For each module identified in step 2, look up its row in `docs/index.md`.
   - If `missing`: create a new page using the
     [library_module.md template](./../skills/docs-write/templates/library_module.md).
   - If `stub` or `draft`: enrich the existing page with findings from the notebook.
   - If `complete`: only add content if the notebook reveals something not already documented.

4. **Write or update pages.**
   Save pages to `docs/library/<submodule>/<module>.md`. Do not invent content that is not
   supported by the source files or notebooks.

5. **Check for guide additions.**
   If the folder describes an end-to-end user workflow (e.g. loading sheets, running the solver),
   and no corresponding guide exists, propose a new guide file path and a brief outline. Ask the
   user before writing it.

6. **Update docs/index.md.**
   For every page created or updated, set `Status` and `Last updated`. Add any new rows for
   modules that were not previously tracked.

7. **Append to docs/log.md.**
   ```
   ## [YYYY-MM-DD] ingest | <scratch_space folder name>
   <What was ingested. Which modules were created/updated. Number of pages affected.>
   ```

## Constraints

- Do not copy raw notebook output (cell results, tracebacks) verbatim into docs. Summarise and
  clean up.
- Do not document internal implementation details that are not part of the public interface,
  unless they are necessary to explain a pitfall.
- Do not modify `scratch_space/` files.
