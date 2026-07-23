# pipelines backlog

Candidate pipelines, worked one at a time. Each row is assessed and then
promoted (authored fresh as an entry) or rejected (with a reason). Rejected rows
stay: a future proposal for the same capability is weighed against the prior
rejection before it is reopened. No bulk migration.

Seeded from the capability audit in
[../scratch_space/24_pipelines_cleanup/00.1_audit_notebooks.md](../scratch_space/24_pipelines_cleanup/00.1_audit_notebooks.md).

Status: `candidate` (not yet decided) / `promoted` (an entry exists) /
`rejected` (with reason).

| Capability | Freshest reference | Status | Notes |
| ---------- | ------------------ | ------ | ----- |
| Board generation (green preset, QR, slot grid) | `scratch_space/23_green_background/generate_green_board.py` | promoted | `generate_board.ipynb`, preset-parameterized |
| Sheet ingest (QR to resolved config to pieces) | `scratch_space/23_green_background/ingest_green_sheet.py` | promoted | `ingest_sheet.ipynb`, depends on generate_board |
| Bulk ingest into SheetManager + SQLite | `scratch_space/fastapi_scaffold/01_db_ingestion.ipynb` | candidate | |
| Segment matching | `scratch_space/contour_/01_match_.ipynb`, `scratch_space/piece_matcher/02_usage.ipynb` | candidate | |
| Grid model and scoring | `scratch_space/grid_model/01_grid_model.ipynb`, `scratch_space/grid_model/02_scoring.ipynb` | candidate | tutorial-shaped; may be docs-only |
| Solving | `scratch_space/naive_linear_solver/02_usage.ipynb` | candidate | |
| Synthetic puzzle generation and rasterizing | `scratch_space/puzzle_generator/01,02,03` | candidate | useful for test data |
| Sheet identity (QR encode/decode, slot labels) | `scratch_space/20_piece_markers/00_sample.ipynb` | candidate | large feature sample; may be docs-only |
| Coordinate-transform helper from `16_support.py` | `scratch_space/20_piece_markers/16_support.py` | candidate | promote the reusable core to `src`/`scripts`, not the 268-line whole |
