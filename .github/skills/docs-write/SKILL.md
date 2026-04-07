---
name: docs-write
description: "Write or update a module doc page for snap_fit. Use when: documenting a module, filling a missing library entry, updating a stale page after code changes, writing from a validated scratch_space notebook or folder. Covers the full procedure: read index, find gaps, read source, fill template, update index and log."
argument-hint: "[module name or path, e.g. puzzle/sheet_manager]"
---

# docs-write Skill

Write or update a `docs/library/` page for a snap_fit module.

## When to Use

- Filling in a module marked `missing` or `stub` in `docs/index.md`
- Updating a page after the underlying source file changed
- Translating validated scratch_space findings into library docs

## Procedure

1. **Read the index.** Load [docs/index.md](../../../docs/index.md). Identify the target module
   (user-specified or highest-priority `missing` row).

2. **Check for a gap.** Optionally run the gap-finder script to confirm:
   ```bash
   uv run python .github/skills/docs-write/scripts/find_undocumented.py
   ```

3. **Read the source.** Load the relevant files from `src/snap_fit/<submodule>/`. Also load the
   corresponding test files from `tests/<submodule>/` for usage patterns and edge cases.

4. **Fill the template.** Use [library_module.md](./templates/library_module.md) as the base.
   Populate every section. Replace all `<placeholder>` values.

5. **Write the page.** Save to `docs/library/<submodule>/<module>.md`. Create the subfolder if
   needed.

6. **Update the index.** In `docs/index.md`, set the row for this module:
   - `Status` → `complete` (or `draft` if partial)
   - `Last updated` → today's date (`YYYY-MM-DD`)
   - `Path` → relative path from `docs/`

7. **Append to the log.** In `docs/log.md`, prepend a new entry:
   ```
   ## [YYYY-MM-DD] write | <submodule/module>
   <One-sentence description of what was added or changed.>
   ```

## Quality Checklist

- [ ] H1 title matches module name
- [ ] Purpose section is one to three sentences, no jargon
- [ ] At least one minimal runnable example (copy-pasteable)
- [ ] Parameters / Returns table if there are more than two items
- [ ] Pitfalls section covers at least one real gotcha from the code or tests
- [ ] Related modules cross-linked with relative paths
- [ ] No secrets, `.env` contents, or absolute machine paths

## Resources

- [Library module template](./templates/library_module.md)
- [Guide template](./templates/guide.md)
- [Gap-finder script](./scripts/find_undocumented.py)
- [docs/index.md catalog](../../../docs/index.md)
- [docs/log.md](../../../docs/log.md)
- [docs/standards.md](../../../docs/standards.md) - style rules
