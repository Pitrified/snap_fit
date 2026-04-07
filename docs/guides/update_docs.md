# Updating the docs - workflow guide

> Type: technical
> Audience: contributors maintaining or growing the documentation

## Overview

The snap_fit docs system is a **persistent wiki maintained by an LLM** - not a dump of one-off
generated files. Every session builds on the last. The docs agent reads a catalog (`docs/index.md`)
to know what exists and what is missing, then writes or updates pages and records what it did in
a log (`docs/log.md`).

The three raw sources feeding the wiki are:

```
scratch_space/  (exploratory notebooks and prototypes)
src/            (validated implementation)
tests/          (usage patterns and edge cases)
    ↓
docs/           (compiled, maintained wiki)
```

The LLM does the compilation. You do the sourcing, direction, and commit.

---

## Core concepts

### Wiki spine

Two files are the engine of the whole system.

**`docs/index.md`** is a living catalog. Every module in `src/snap_fit/` has a row with a status
(`missing` · `stub` · `draft` · `complete`) and a last-updated date. The agent reads this at the
start of every session to know what to do next.

**`docs/log.md`** is an append-only change log. Every write, ingest, or lint pass adds one entry.
It gives you and the agent a shared memory of what happened and when. Parse it quickly:

```bash
grep "^## \[" docs/log.md | tail -10
```

Neither file should be edited by hand. The docs agent maintains them.

### Three operations

| Operation | When to use | How to invoke |
|-----------|-------------|---------------|
| **Write** | Document a specific module | Switch to `docs_agent`, ask it to document `<module>` |
| **Ingest** | Compile a finished scratch_space folder into docs | `/docs-ingest scratch_space/<name>/` |
| **Lint** | Periodic health check; after a big refactor | `/docs-lint` |

---

## Prerequisites

- VS Code with GitHub Copilot (agent mode)
- The `docs_agent` custom agent is available in the agent picker (`.github/agents/docs-agent.md`)
- The `docs-write` skill is available (`.github/skills/docs-write/`)

---

## Workflow 1: Write a module doc from scratch

Use this when `docs/index.md` shows a module as `missing` or `stub`.

### 1. Switch to the docs agent

In VS Code Chat, select **docs_agent** from the agent picker.

The agent automatically reads `docs/index.md` and `docs/log.md` (last 20 lines) on startup.

### 2. Ask for the module

```
Document puzzle/sheet_manager
```

or let the agent pick the highest-priority gap:

```
Document the next missing high-priority module
```

The agent uses the `docs-write` skill procedure: reads `src/`, reads `tests/`, fills the template,
writes to `docs/library/`.

### 3. Review the output

Check the generated file in `docs/library/<submodule>/<module>.md`. Look for:
- Accurate type signatures (compare against source)
- At least one runnable example
- Pitfalls that match real behaviour

### 4. Update index + log

After reviewing, click the **Update index + log** handoff button that appears after the agent
response. The agent sets the status row and appends to the log automatically.

Or explicitly ask:
```
Update docs/index.md and docs/log.md for what we just wrote.
```

### 5. Commit

```bash
git add docs/library/puzzle/sheet_manager.md docs/index.md docs/log.md
git commit -m "docs(puzzle): add sheet_manager reference page"
```

---

## Workflow 2: Ingest a scratch_space folder

Use this when a prototype folder in `scratch_space/` is considered done and its validated knowledge
should be compiled into the wiki.

### 1. Switch to the docs agent

Select **docs_agent** in the agent picker.

### 2. Run the ingest prompt

Type `/docs-ingest` and then the folder path:

```
/docs-ingest scratch_space/piece_matcher/
```

The agent reads all files in the folder (notebooks, plan files, scripts), extracts validated
patterns, and creates or updates the matching `docs/library/` pages.

### 3. Review and confirm guides

If the folder describes a user-facing workflow, the agent will propose a new guide. Confirm or
decline before it writes.

### 4. Update index + log

Click **Update index + log** or ask explicitly. Then commit.

```bash
git add docs/
git commit -m "docs(puzzle): ingest piece_matcher scratch_space"
```

---

## Workflow 3: Lint the wiki

Run periodically (monthly) or after a significant refactor.

### 1. Run the lint prompt

In chat with **docs_agent**, type:

```
/docs-lint
```

### 2. Review the report

The agent checks for:
- Orphan pages (exist in `docs/library/` but not in `docs/index.md`)
- Stale docs (source file changed after `Last updated` date)
- Undocumented modules (in `src/` but no index row)
- Broken relative links
- Pages with no inbound links

### 3. Act on findings

For each stale module, ask the agent to update it:

```
Update the docs for image/segment_matcher - it was flagged as stale.
```

Then commit the fixes.

---

## Reference: file locations

| File | Purpose | Who edits |
|------|---------|-----------|
| `docs/index.md` | Module coverage catalog | docs_agent |
| `docs/log.md` | Append-only change log | docs_agent |
| `docs/library/**/*.md` | Module reference pages | docs_agent |
| `docs/guides/*.md` | How-to guides | docs_agent (ask first for existing guides) |
| `.github/agents/docs-agent.md` | Agent persona + handoffs | Human |
| `.github/skills/docs-write/` | Write procedure + templates | Human |
| `.github/prompts/docs-lint.prompt.md` | Lint slash command | Human |
| `.github/prompts/docs-ingest.prompt.md` | Ingest slash command | Human |

---

## Pitfalls

- **Do not edit `docs/index.md` or `docs/log.md` by hand** unless correcting an error. The agent uses
  them as its memory; manual edits that do not match the catalog format will confuse it.
- **Do not commit generated docs without reviewing them.** The agent can hallucinate type signatures
  or behaviour; always spot-check against the source.
- **Do not ingest a scratch_space folder that is still experimental.** The ingest prompt assumes the
  content is validated. Ingesting an in-progress notebook will produce docs that contradict the
  final implementation.
- **The `docs/references/` folder is auto-generated by mkdocs.** Never write to it manually and
  never ask the docs agent to touch it.

---

## Related

- [docs/index.md](../index.md) - Current coverage catalog
- [docs/log.md](../log.md) - Change log
- [docs/README.md](../README.md) - Docs overview
- [.github/agents/docs-agent.md](../../.github/agents/docs-agent.md) - Agent definition
- [.github/skills/docs-write/SKILL.md](../../.github/skills/docs-write/SKILL.md) - Write skill procedure
