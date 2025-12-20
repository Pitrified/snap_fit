## Overview

We need to implement a `PieceId` data model to uniquely identify pieces across different sheets. Currently, pieces are identified by a `(sheet_id: str, piece_id: int)` pair, which is duplicated in `SegmentId` and passed as separate arguments in several methods.

### Chosen Approach: Option A (Nested PieceId in SegmentId)

- Create a `PieceId` model with `sheet_id` and `piece_id`.
- Update `SegmentId` to contain a `piece_id: PieceId` field instead of separate `sheet_id` and `piece_id` fields.
- **Pros:** Cleanest separation; `PieceId` becomes a first-class citizen that can be used in `Piece` objects and `SheetManager` lookups.
- **Cons:** Requires updating `seg_id.sheet_id` to `seg_id.piece_id.sheet_id`.

## Plan

1. [ ] **Data Model Creation:**

   - Create `src/snap_fit/data_models/piece_id.py` with `PieceId(BaseModel, frozen=True)`.
   - Fields: `sheet_id: str`, `piece_id: int`.
   - Add `__str__` (format: `sheet_id:piece_id`) and `__repr__`.

2. [ ] **SegmentId Refactor:**

   - Update `src/snap_fit/data_models/segment_id.py` to use `PieceId`.
   - Change fields to: `piece_id: PieceId`, `edge_pos: EdgePos`.
   - Add `@property` for `sheet_id` and `piece_id_int` (or similar) to `SegmentId` to ease the transition if necessary, though a full refactor is preferred.
   - Update `__str__`, `__repr__`, and `as_tuple`.

3. [ ] **Piece Class Update:**

   - Update `src/snap_fit/puzzle/piece.py`:
     - Add `piece_id: PieceId` attribute to `Piece`.
     - Update `__init__` to accept `PieceId` instead of `int`.
   - Update `src/snap_fit/puzzle/sheet.py`:
     - When creating `Piece` objects in `find_pieces`, construct `PieceId` using the sheet's identifier (which needs to be passed to or stored in `Sheet`).

4. [ ] **SheetManager Update:**

   - Update `src/snap_fit/puzzle/sheet_manager.py`:
     - Update `get_piece_by_segment_id(self, seg_id: SegmentId)` to use `seg_id.piece_id`.
     - Add `get_piece(self, piece_id: PieceId) -> Piece | None`.
     - Update `get_segment_ids_other_pieces` to use `PieceId` for comparison.

5. [ ] **PieceMatcher Update:**

   - Update `src/snap_fit/puzzle/piece_matcher.py`:
     - Update `get_matches_for_piece(self, piece_id: PieceId)`.

6. [ ] **Validation & Tests:**

   - Update `tests/data_models/test_segment_id.py`.
   - Update `tests/puzzle/test_sheet_manager.py`.
   - Update `tests/puzzle/test_piece_matcher.py`.
   - Run `uv run pytest` to ensure everything still works.

7. [ ] **Notebooks (Optional/Usage):**
   - Update usage in `scratch_space/segment_id_model/02_usage.ipynb`.

## Affected Areas

Based on a codebase search, the following areas use the `(sheet_id, piece_id)` pair:

- **Data Models:**
  - `SegmentId`: Currently has `sheet_id: str` and `piece_id: int`.
  - `MatchResult`: Contains two `SegmentId`s.
- **Puzzle Logic:**
  - `SheetManager`:
    - `get_piece_by_segment_id(self, seg_id: SegmentId)`
    - `get_sheet_by_segment_id(self, seg_id: SegmentId)`
    - `get_segment(self, seg_id: SegmentId)`
    - `get_segment_ids_other_pieces(self, seg_id: SegmentId)`
  - `PieceMatcher`:
    - `get_matches_for_piece(self, sheet_id: str, piece_id: int)`
- **Notebooks:**
  - `scratch_space/segment_id_model/01_segment_id.ipynb`
  - `scratch_space/segment_id_model/02_usage.ipynb`
  - `scratch_space/piece_matcher/01_piece_matcher.ipynb`
