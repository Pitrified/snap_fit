# Repository Agents Overview

This repository uses specialized agents defined in `.github/agents/` to improve maintainability and velocity. Each agent follows best practices: specificity, executable commands, real code examples, clear boundaries (Always / Ask / Never), explicit stack & file structure.

## Active Agents

- `@meta_agent` – Maintains agent definitions and ensures adherence to six core areas.
- `@docs_agent` – Generates and updates developer documentation in `docs/`.
- `@dev_agent` – Scaffolds features, plans implementation, and prototypes in `scratch_space/`.
- `@test_agent` – Generates and maintains test coverage (writes to `tests/`).

## Six Core Areas (Applied to Every Agent)

1. Commands (copyable & with purpose)
2. Testing & validation steps (where applicable)
3. Project structure awareness (folders it reads/writes)
4. Code style example(s)
5. Git workflow guidance (commit scope, diff style)
6. Boundaries (Always / Ask / Never)

## Tech Stack Reference

Python 3.13+ · Haystack 2.x · OpenAI · Loguru · Rich · Pytest · Ruff · Pyright · Pre-commit

## Scripts

(Always activate venv: `source .venv/bin/activate`)

- Test: `pytest`
- Lint: `ruff check .`
- Format: `ruff format .`
- Type Check: `pyright`
  (Extend with test/docs scripts as they are added.)

## Adding a New Agent

1. Create file: `.github/agents/<name>-agent.md`
2. Include YAML frontmatter with `name` & `description`.
3. Cover six core areas; add one concrete code example.
4. Define boundaries with Always / Ask / Never tiers.
5. Update this index (Active Agents section).

## Boundary Conventions

- ✅ **Always:** Safe, recurring actions within scope.
- ⚠️ **Ask first:** Potentially impactful or structural changes.
- 🚫 **Never:** Out-of-scope directories, secrets, irreversible or high-risk edits.

## Code Style Example (Shared Reference)

```python
# Shared style baseline
from loguru import logger as lg

def fetch_entity(table: str, entity_id: str | None) -> dict:
    if entity_id is None:
        msg = "entity_id required"
        raise ValueError(msg)

    # Example placeholder logic
    lg.info(f"Fetching {entity_id} from {table}")
    return {"id": entity_id, "table": table}
```

## Meta Agent Maintenance Cycle

- Weekly or on dependency change: audit all agent files.
- Validate version accuracy vs `pyproject.toml`.
- Ensure new folders are reflected in project knowledge sections.

## Docs Agent Output Pattern

Each doc file should include: Title, Purpose, Usage Example, Parameters, Returns/Side Effects, Pitfalls, Related Links.

## Roadmap (Potential Future Agents)

- `@test_agent` – Generate and maintain test coverage (writes to `tests/`).
- `@lint_agent` – Enforce formatting & style without logic changes.
- `@api_agent` – Assist with API endpoints & data models (ask before schema changes).

## Review Checklist Before Merging Agent Changes

- Frontmatter present & accurate
- Commands actionable
- Boundaries include all three tiers
- Example code compiles conceptually
- No source logic modifications in agent diffs

Iterate; keep agents lean and specific. Add detail reactively when mistakes appear.
