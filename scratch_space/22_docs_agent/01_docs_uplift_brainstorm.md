# Docs Agent Uplift - Brainstorm

_Date: 2026-04-07_

---

## 1. Current State and Core Problem

The existing `docs-agent.md` is a well-structured custom agent, but it has a fundamental limitation:
**it is reactive and stateless**. Every conversation starts from scratch - the agent reads source code,
rediscovers module structure, and writes docs with no memory of what was done before or what still needs
doing. As a result, `docs/library/` is completely empty, and the getting-started guide leans on raw
notebook links rather than compiled prose.

The pattern described in `00_ref_gist.md` names this problem precisely: most LLM-doc systems are RAG
over raw sources, not a compounding knowledge base. The fix is to make `docs/` a **persistent,
maintained wiki** - not a dump of one-off outputs.

A second, practical observation: snap_fit already has a natural pipeline that the docs agent does not
exploit:

```
scratch_space/  (plan, prototype, validate)
    → src/      (validated implementation)
        → docs/ (compiled knowledge) ← this step is missing
```

The docs agent should be the machinery for that last arrow.

---

## 2. Diagnosis: What Is Missing

| Gap | Impact |
|-----|--------|
| `docs/library/` is empty | No module-level reference docs for the core layers |
| No inventory of documented vs undocumented modules | Agent cannot prioritise or track coverage |
| No log of doc changes | No way to know what was written, when, or why |
| Agent cannot detect stale docs after code changes | Docs will drift from code silently |
| No structured workflow for "ingest a finished notebook" | scratch_space knowledge is not compiled into docs |
| All project knowledge is hardcoded in the agent file | Hard to keep in sync as the codebase evolves |

---

## 3. Available VS Code Primitives (as of April 2026)

The customization stack offers five composable primitives, each with a distinct role:

| Primitive | File | Best for |
|-----------|------|----------|
| Custom Agent | `.github/agents/*.agent.md` | Persistent persona, tool restrictions, handoffs |
| Skill | `.github/skills/<name>/SKILL.md` | Reusable workflow + bundled scripts + templates |
| Prompt | `.github/prompts/*.prompt.md` | Single focused task, slash-command invocable |
| Hook | `.github/hooks/*.json` | Deterministic enforcement at lifecycle events |
| Instructions | `.github/instructions/*.instructions.md` | Always-on coding/style conventions |

Two features added recently are worth highlighting:

- **Handoffs**: an agent can declare a `handoffs:` block in its frontmatter, rendering a button after
  each response that transitions the user to the next agent with pre-filled context. This enables a
  "write → index → lint" pipeline that keeps the human in control at each gate.

- **Scoped hooks (Preview)**: hooks can now live *inside* an agent's frontmatter (requires
  `chat.useCustomAgentHooks: true`), so a docs agent can carry its own staleness-injection hook
  without polluting the global hook config.

Agent Skills is also now an **open standard** (`agentskills.io`) - skills created in VS Code are
portable to GitHub Copilot CLI and the Copilot coding agent, which is relevant if the project ever
uses background agents for automated doc runs.

---

## 4. Proposed Uplift

### 4.1 Introduce a Wiki Spine: `docs/index.md` + `docs/log.md`

This is the single highest-value change and costs nothing in infrastructure.

**`docs/index.md`** - a living catalog of every documented and undocumented module:

```markdown
## Library

| Module | Path | Status | Last updated | Notes |
|--------|------|--------|--------------|-------|
| puzzle/sheet_manager | library/puzzle/sheet_manager.md | complete | 2026-04-07 | |
| puzzle/piece_matcher | library/puzzle/piece_matcher.md | stub | 2026-03-15 | needs examples |
| image/segment_matcher | - | missing | - | high priority |
```

**`docs/log.md`** - append-only chronological log, parseable with simple grep:

```markdown
## [2026-04-07] write | puzzle/sheet_manager
Added full module doc with examples and pitfalls. Source: src/snap_fit/puzzle/sheet_manager.py.

## [2026-04-07] lint | all
Found 3 orphan pages. Found 1 stale reference (PieceMatcher.clear() renamed).
```

The agent reads the index at the start of every session to know what exists and what is missing,
and appends to the log at the end of every write. This is the "accumulation" pattern from the gist -
the maintenance overhead is near zero for the LLM.

### 4.2 Add a `docs-write` Skill

Convert the core doc-writing workflow into a **Skill** at `.github/skills/docs-write/`.

```
.github/skills/docs-write/
├── SKILL.md              # Procedure + template references
├── scripts/
│   └── find_undocumented.py   # Scans src/ + docs/index.md, prints gaps
└── templates/
    ├── library_module.md      # Standard module doc template
    └── guide.md               # Guide template
```

`SKILL.md` body covers:
1. Read `docs/index.md` to identify the highest-priority gap.
2. Run `find_undocumented.py` to get a current gap report (optional, confirms index).
3. Read the relevant source files and tests.
4. Fill `templates/library_module.md`.
5. Write to `docs/library/<submodule>/`.
6. Update `docs/index.md` (status → complete, last-updated date).
7. Append to `docs/log.md`.

The script `find_undocumented.py` is a simple file-walker: it lists all `src/snap_fit/**/__init__.py`
modules, checks for a corresponding entry in `docs/library/`, and prints what is missing. Roughly
15-20 lines of Python, no new dependencies.

**Why a Skill and not just instructions in the agent?** The script and templates are bundled assets
that travel with the workflow. A Skill loads them progressively (only when relevant), keeps the agent
context lean, and is portable to Claude Code / CLI automatically.

### 4.3 Add a `docs-lint` Prompt

A slash-command prompt `/docs-lint` for periodic wiki health checks.

```markdown
---
description: "Health-check the docs wiki: find orphans, stale links, undocumented modules, contradictions"
agent: "docs_agent"
tools: [read, search]
---
Perform a full health check of docs/ using docs/index.md as the manifest.

Check for:
1. Pages in docs/library/ that have no entry in docs/index.md (orphans).
2. Entries in docs/index.md marked as complete but whose source file has changed since last-updated date.
3. Modules in src/snap_fit/ with no docs/library/ entry and no index row.
4. Broken relative links in any docs/ file. Check them explicitly using `uv mkdocs build` to catch missing files or typos.
5. Pages with no inbound links from other docs pages.

Output a Markdown report. Append a summary entry to docs/log.md.
```

This maps to the "Lint" operation in the gist. The user types `/docs-lint` once in a while, or after
a significant refactor.

### 4.4 Add a `docs-ingest` Prompt

A slash-command prompt `/docs-ingest <notebook_path>` for the scratch_space → docs pipeline:

```markdown
---
description: "Ingest a completed scratch_space notebook into the docs wiki"
argument-hint: "<notebook path>"
agent: "docs_agent"
tools: [read, edit, search]
---
Process the provided scratch_space notebook into docs/:
1. Read the notebook cells and extract validated patterns, findings, and examples.
2. Identify which src/ modules are demonstrated.
3. Update or create the relevant docs/library/ page(s).
4. Update docs/index.md and append to docs/log.md.
5. If the notebook describes a user-facing workflow, propose a guide addition.
```

This is the cleanest expression of the gist idea for this project: every scratch_space notebook is a
"raw source" that, once validated, should be compiled into the wiki by the LLM.

The ingest unit is an entire `scratch_space/<name>/` folder rather than a single notebook - this
captures associated scripts, plan files, and secondary resources alongside the notebook cells.

### 4.5 Upgrade the Agent with Handoffs

Add a `handoffs:` block to `docs-agent.md` so the write → index → lint pipeline is surfaced as
one-click transitions:

```yaml
handoffs:
  - label: Update index
    agent: docs_agent
    prompt: "Update docs/index.md to reflect all changes just made. Then append to docs/log.md."
    send: true
  - label: Run lint
    agent: docs_agent
    prompt: "Health-check the docs wiki. Run /docs-lint."
    send: false
```

This keeps the human in control (they click to proceed) while removing the cognitive overhead of
remembering the next step.

---

## 5. Architecture Summary

After the uplift, the docs system looks like this:

```
.github/
├── agents/
│   └── docs-agent.md          # Core persona - same as now, add handoffs
├── skills/
│   └── docs-write/
│       ├── SKILL.md           # Write procedure
│       ├── scripts/find_undocumented.py
│       └── templates/
│           ├── library_module.md
│           └── guide.md
└── prompts/
    ├── docs-lint.prompt.md    # /docs-lint slash command
    └── docs-ingest.prompt.md  # /docs-ingest slash command

docs/
├── index.md                   # Living catalog (LLM-maintained)
├── log.md                     # Append-only change log (LLM-maintained)
├── library/                   # Per-module docs (currently empty)
│   ├── puzzle/
│   ├── image/
│   ├── grid/
│   └── ...
└── guides/
    ├── getting_started.md     # Exists - do not edit; add new guides alongside it
    ├── update_docs.md         # NEW - meta guide for the docs workflow
    └── fastapi.md             # Exists, good shape
```

The wiki spine (`index.md` + `log.md`) is what turns the agent from a one-shot document generator
into a compounding knowledge base. Everything else follows from that.

---

## 6. Prioritised Action Plan

| Priority | Action | Effort | Value |
|----------|--------|--------|-------|
| 1 | Create `docs/index.md` with current module inventory | Low | High - enables all subsequent work |
| 2 | Create `docs/log.md` (empty, ready for LLM appends) | Trivial | High - audit trail |
| 3 | Create `.github/skills/docs-write/` with procedure + templates | Medium | High - standardises output |
| 4 | Write `find_undocumented.py` script | Low | Medium - automates gap detection |
| 5 | Add `/docs-lint` prompt | Low | Medium - periodic health checks |
| 6 | Add `/docs-ingest` prompt (folder-level) | Low | High - scratch_space pipeline |
| 7 | Add `handoffs:` to `docs-agent.md` | Low | Medium - guided workflow |
| 8 | Write `docs/guides/update_docs.md` user meta guide | Low | High - onboarding |

Items 1-2 can be done immediately and unlock everything downstream. Items 3-7 form the full skill
layer. Item 8 is optional - worth adding once the library has meaningful coverage to protect.

---

## 7. What Not To Do

- **Do not add a search infrastructure** (qmd or similar vector search). At current docs volume
  (tens of pages), the `docs/index.md` file is a fully sufficient navigation layer. Add a search tool
  only if the wiki grows past ~200 pages.
- **Do not automate commits**. The human reviews and commits. The LLM writes.
- **Do not create separate Claude Code agent files**. VS Code now detects `.md` files in
  `.github/agents/` and maps them; the same files work in Claude Code via `.claude/agents/`. Avoid
  duplication.
- **Do not replace the existing `getting_started.md` structure**. It is good; it just needs prose
  linking the steps together, not a rewrite.

---

## 8. Relation to the Gist

The gist describes a general pattern ("LLM wiki"). Here is the mapping for snap_fit specifically:

| Gist concept | snap_fit equivalent |
|---|---|
| Raw sources (immutable) | `src/`, `tests/`, `scratch_space/` |
| The wiki (LLM-maintained) | `docs/` |
| The schema (agent config) | `docs-agent.md` + `docs-write` skill |
| Index file | `docs/index.md` |
| Log file | `docs/log.md` |
| Ingest operation | `/docs-ingest <notebook>` |
| Query operation | Chat with `docs_agent`, reads index first |
| Lint operation | `/docs-lint` |
| Obsidian / IDE | VS Code with Copilot |

The gist is a good fit here because snap_fit already has exactly the three-layer pipeline (scratch
→ src → docs). The missing piece is the machinery to maintain the docs layer - which is entirely
covered by the VS Code primitives described above.
