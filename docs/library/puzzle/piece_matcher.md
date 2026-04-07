# `puzzle/piece_matcher`

> Module: `src/snap_fit/puzzle/piece_matcher.py`
> Related tests: `tests/puzzle/`

## Purpose

`PieceMatcher` computes and caches segment-pair similarity scores. It uses `SegmentMatcher` for the actual affine-transform-based comparison and maintains an internal lookup cache keyed by `frozenset[SegmentId]` for symmetric, efficient retrieval.

## Usage

### Minimal example

```python
from snap_fit.puzzle.piece_matcher import PieceMatcher
from snap_fit.puzzle.sheet_manager import SheetManager

matcher = PieceMatcher(manager=sheet_manager)

# Match all segments against each other
matcher.match_all()

# Get the top 10 best matches (lowest similarity score)
for m in matcher.get_top_matches(n=10):
    print(f"{m.seg_id1} <-> {m.seg_id2}: {m.similarity:.2f}")
```

### Incremental matching

```python
# After adding new sheets to manager
new_ids = [piece.piece_id for piece in new_sheet.pieces]
new_count = matcher.match_incremental(new_ids)
print(f"Computed {new_count} new matches")
```

### Persistence

```python
from pathlib import Path

# JSON
matcher.save_matches_json(Path("cache/matches.json"))
matcher.load_matches_json(Path("cache/matches.json"))

# SQLite
matcher.save_matches_db(Path("cache/dataset.db"))
matcher.load_matches_db(Path("cache/dataset.db"))
```

## API Reference

### `PieceMatcher`

Matches puzzle piece segments and caches results.

Constructor: `PieceMatcher(manager: SheetManager | None)` - pass `None` if only loading from persistence.

Key methods:

| Method | Description |
|--------|-------------|
| `match_pair(id1, id2)` | Match two segments (cached) |
| `match_all()` | Match every segment against every other piece's segments |
| `match_incremental(new_piece_ids)` | Match only new pieces against existing ones |
| `get_top_matches(n)` | Top N matches by similarity |
| `get_matches_for_piece(piece_id)` | All matches involving a piece |
| `get_cached_score(seg_a, seg_b)` | Lookup cached score, returns `None` if not cached |
| `get_matched_pair_keys()` | Set of all matched frozenset pairs |
| `clear()` | Wipe all results and lookup cache |

Similarity scoring: lower is better. A score of `1e6` indicates incompatible shapes (e.g., two IN segments or an EDGE segment).

## Common Pitfalls

- **O(n^2) matching**: `match_all()` matches every segment pair across all pieces. For N pieces, this is ~16N^2 comparisons (4 edges each). Can be slow for large datasets.
- **Manager required for matching**: Pass `None` as manager only if you intend to load results from disk. Calling `match_pair()` or `match_all()` without a manager raises `RuntimeError`.
- **Results are sorted after match_all()**: Results are sorted by similarity ascending. If you add matches manually via `match_pair()`, the list is not automatically re-sorted.

## Related Modules

- [`puzzle/sheet_manager`](sheet_manager.md) - provides segment lookups for matching
- [`image/segment_matcher`](../image/segment_matcher.md) - the affine-based matching algorithm
- [`data_models`](../data_models/index.md) - `MatchResult`, `SegmentId` data structures
- [`grid/scoring`](../grid/scoring.md) - uses cached match scores for grid placement scoring
