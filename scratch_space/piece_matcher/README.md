# PieceMatcher Implementation Plan

## Overview

The `PieceMatcher` class will centralize the logic for matching puzzle pieces across multiple sheets. It will leverage `SegmentMatcher` for segment-level similarity and `SheetManager` for data retrieval using `SegmentId`.

### Key Responsibilities
- Match all edges between two pieces.
- Match all pieces within a `SheetManager`.
- Store and query match results.
- Use `SegmentId` for identifying segments.

## Selected Approach: Hybrid Storage
- **Flat List**: `self._results: list[MatchResult]` sorted by similarity for "Top N" queries.
- **Dictionary**: `self._lookup: dict[frozenset[SegmentId], MatchResult]` for O(1) pair lookups.

## Plan

1. [ ] **Define `MatchResult` Data Model**
   - Create `src/snap_fit/data_models/match_result.py`.
   - Fields: `seg_id1: SegmentId`, `seg_id2: SegmentId`, `similarity: float`.
   - Add helper to get the "other" segment ID given one.

2. [ ] **Implement `PieceMatcher` Class**
   - Create `src/snap_fit/puzzle/piece_matcher.py`.
   - `__init__(self, manager: SheetManager)`: Store reference to the manager.
   - Methods:
     - `match_all(self)`: Double loop over all pieces/segments from `manager.get_segment_ids_all()`.
     - `match_pair(self, id1: SegmentId, id2: SegmentId) -> MatchResult`: Compute and store a single match.
     - `get_top_matches(self, n: int = 10) -> list[MatchResult]`.
     - `get_matches_for_piece(self, piece_id: int, sheet_id: str) -> list[MatchResult]`.

3. [ ] **Integration & Validation**
   - Update `src/snap_fit/data_models/__init__.py` to export `MatchResult`.
   - Update `src/snap_fit/puzzle/__init__.py` to export `PieceMatcher`.
   - Create `scratch_space/piece_matcher/01_piece_matcher.ipynb` for interactive testing.
   - Add unit tests in `tests/puzzle/test_piece_matcher.py`.
