# Segment ID Model

## Overview

We need to create a proper data model for identifying segments across sheets/pieces/edges, replacing ad-hoc tuple usage with a structured `SegmentId` model. This will also enhance `SheetManager` with methods to query segments by ID.

**Option A: Simple Pydantic Model**
- Create a `SegmentId(BaseModel)` with `sheet_id`, `piece_id`, `edge_pos` fields
- Pros: Simple, immutable, hashable (with frozen=True), serializable out of the box
- Cons: Requires Pydantic dependency (already in use)

**Option B: NamedTuple**
- Create a `SegmentId(NamedTuple)` with typed fields
- Pros: Lightweight, hashable by default, unpacking support
- Cons: Less validation, no built-in serialization

**Option C: Dataclass (frozen)**
- Create a `@dataclass(frozen=True)` SegmentId
- Pros: Standard library, hashable when frozen, type hints
- Cons: Manual serialization if needed

---

**Selected: Option A - Pydantic Model**

## Plan

1. [ ] Create prototype notebook `01_segment_id.ipynb` to explore `SegmentId` model design
   - Follow structure from `scratch_space/feature_sample/01_sample.ipynb`:
     1. `# Title` - markdown cell with feature name
     2. `## Import` - markdown header
     3. Autoreload cell: `%load_ext autoreload` / `%autoreload 2`
     4. Logger/Rich setup cell (loguru, rich console fix)
     5. Project imports cell (snap_fit imports)
     6. `## Params and config` - markdown header
     7. Load params cell
     8. `## Develop and prototype` - markdown header
     9. Prototype cells...
2. [ ] Define `SegmentId` Pydantic model in `src/snap_fit/data_models/segment_id.py`
   - Fields: `sheet_id: str`, `piece_id: int`, `edge_pos: EdgePos`
   - Use `frozen=True` for hashability
   - Add helper properties (e.g., `as_tuple`, `__str__`)
3. [ ] Add `SheetManager.get_segment_ids_all()` → list of all `SegmentId` in manager
4. [ ] Add `SheetManager.get_segment_ids_other_pieces(seg_id: SegmentId)` → list of `SegmentId` from other pieces (excluding current piece, across all sheets)
5. [ ] Add `SheetManager.get_segment(seg_id: SegmentId)` → `Segment`
6. [ ] Add `SheetManager.get_piece(seg_id: SegmentId)` → `Piece`
7. [ ] Add `SheetManager.get_sheet(seg_id: SegmentId)` → `Sheet` (overload existing)
8. [ ] Write unit tests for `SegmentId` and new `SheetManager` methods
9. [ ] Update usage notebook demonstrating the new API
