# docs/log.md - Documentation Change Log

> **LLM-maintained file.** Append a new entry for every doc write, ingest, or lint pass.
> Never edit or delete past entries. Format: `## [YYYY-MM-DD] <operation> | <scope>`
> Operations: `write` · `ingest` · `lint` · `update` · `index`

Grep tip: `grep "^## \[" docs/log.md | tail -10` shows the last 10 entries.

---

## [2026-04-07] write | all modules (full package)

Complete library documentation for all 35 tracked modules across 10 subpackages:
config, data_models, params, puzzle (9 modules), image (6 modules), grid (6 modules),
solver (2 modules), aruco (3 modules), persistence, webapp. Each page includes
purpose, usage examples, API reference, pitfalls, and cross-links. Index updated
to 35/35 complete.

## [2026-04-07] index | all

Initial catalog created in `docs/index.md`. All 35 modules marked `missing`. Wiki spine established:
`docs/index.md` (catalog) and `docs/log.md` (this file). No library pages exist yet.
