# `grid/scoring`

> Module: `src/snap_fit/grid/scoring.py`
> Related tests: `tests/grid/`

## Purpose

Scoring functions that evaluate how well pieces fit together on the grid. Computes pairwise match scores between adjacent placed pieces using cached similarity data from `PieceMatcher`.

## Usage

### Minimal example

```python
from snap_fit.grid.scoring import score_grid, score_grid_with_details, score_edge

# Score an individual edge between two positions
edge_score = score_edge(state, pos1, pos2, matcher)
# Returns float or None if either position is empty

# Total grid score
total = score_grid(state, matcher)

# Detailed breakdown
total, edge_scores = score_grid_with_details(state, matcher)
for (p1, p2), score in edge_scores.items():
    print(f"{p1} <-> {p2}: {score:.2f}")
```

## API Reference

| Function | Returns | Description |
|----------|---------|-------------|
| `score_edge(state, pos1, pos2, matcher)` | `float \| None` | Score between two adjacent placed pieces |
| `score_grid(state, matcher)` | `float` | Sum of all edge scores |
| `score_grid_with_details(state, matcher)` | `(float, dict)` | Total + per-edge breakdown |

Scoring accounts for piece rotation: it maps the rotated edge position back to the original segment using `get_original_edge_pos()`, then looks up the match score from `PieceMatcher`.

## Common Pitfalls

- **Empty positions are skipped**: Edges adjacent to empty slots return `None` and are not penalized. A partially filled grid may appear to have a better score than a fully filled one simply because fewer edges are scored.

## Related Modules

- [`grid/placement_state`](placement_state.md) - the placement being scored
- [`puzzle/piece_matcher`](../puzzle/piece_matcher.md) - provides cached similarity scores
- [`grid/orientation_utils`](orientation.md) - `get_original_edge_pos()` for rotation mapping
