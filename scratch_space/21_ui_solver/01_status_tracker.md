# Status Tracker

Track sub-plans location and high-level status for the UI solver feature.

## Sub-plans

| # | File | Title | Status | Dependencies |
|---|------|-------|--------|--------------|
| 02 | [02_dataset_selector.md](02_dataset_selector.md) | Dataset selector & settings page | **done** | - |
| 03 | [03_piece_image_endpoint.md](03_piece_image_endpoint.md) | Piece image endpoint | **done** | - |
| 04 | [04_session_crud.md](04_session_crud.md) | Session CRUD & PlacementState persistence | **done** | 02 |
| 05 | [05_suggestion_engine.md](05_suggestion_engine.md) | Suggestion engine | **not started** | 04, 06 |
| 06 | [06_run_matching.md](06_run_matching.md) | Run matching endpoint | **done** | - |
| 07 | [07_viz_primitives.md](07_viz_primitives.md) | Visualization primitives (Jinja2 macros) | **not started** | 03 |
| 08 | [08_solver_ui_templates.md](08_solver_ui_templates.md) | Solver UI templates | **not started** | 03, 04, 05, 07 |
| 09 | [09_orientation_debug.md](09_orientation_debug.md) | Orientation debug page | **not started** | 03 |

## Dependency graph

```
02 Dataset Selector ──────────────────────────┐
                                              ├──> 04 Session CRUD ──┐
03 Piece Image ──┬──> 07 Viz Primitives ──┐   │                     ├──> 05 Suggestion ──┐
                 ├──> 09 Orientation Debug │   │                     │                    │
                 │                         ├───┼─────────────────────┼──> 08 Solver UI    │
                 │                         │   │                     │                    │
06 Run Matching ─┼─────────────────────────┼───┼─────────────────────┘                    │
                 │                         │   │                                          │
                 └─────────────────────────┘   └──────────────────────────────────────────┘
```

## Recommended implementation order

1. **02** Dataset selector + **03** Piece image endpoint + **06** Run matching (parallel, no deps)
2. **04** Session CRUD (needs 02)
3. **07** Viz primitives + **09** Orientation debug (need 03)
4. **05** Suggestion engine (needs 04 + 06)
5. **08** Solver UI templates (needs 03 + 04 + 05 + 07)

## Notes

- Sub-plans 02, 03, 06 have NO dependencies and can be built in parallel
- Sub-plan 08 (solver UI) is the final integration step that pulls everything together
- Sub-plan 09 (orientation debug) is standalone once piece images work - use it early to validate rotation conventions before building the solver grid
