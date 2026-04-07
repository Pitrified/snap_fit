---
description: "Health-check the docs wiki: find orphan pages, stale module docs, undocumented modules, and broken links. Run periodically or after a significant refactor."
agent: "docs_agent"
tools: [read, search, execute]
---

Perform a full health check of `docs/` using `docs/index.md` as the manifest.

## Checks to perform

1. **Orphan pages** - Markdown files in `docs/library/` that have no corresponding row in
   `docs/index.md`. List each orphan with its path.

2. **Stale docs** - Rows in `docs/index.md` with status `complete` where the `Last updated` date
   is older than the `git log --since` date for the corresponding `src/snap_fit/` source file.
   Use this command to find recently changed source files:
   ```bash
   git log --name-only --pretty=format: -- src/snap_fit/ | grep '\.py$' | sort -u
   ```
   Flag any module where the source was committed after the `Last updated` date in the index.

3. **Undocumented modules** - Run the gap-finder script:
   ```bash
   uv run python .github/skills/docs-write/scripts/find_undocumented.py
   ```
   List every submodule it reports as missing.

4. **Broken relative links** - For each `.md` file in `docs/`, check that every `[text](path)`
   reference resolves to an existing file. Flag any broken link with file + line number.

5. **Orphan pages (no inbound links)** - Pages in `docs/library/` that are not linked from any
   other doc page (including `docs/index.md` and `docs/guides/`). List them.

## Output format

Produce a Markdown report with one section per check. Use a table for stale docs and undocumented
modules. Use a list for broken links and orphans. Include a summary line: `X issues found`.

If there are zero issues for a check, write `No issues.` for that section.

## After reporting

Append a summary entry to `docs/log.md`:
```
## [YYYY-MM-DD] lint | all
<summary line from report, e.g. "5 issues found: 2 stale, 1 undocumented, 2 broken links">
```
