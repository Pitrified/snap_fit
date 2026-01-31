# Database Ingestion Plan for Sheets, Pieces, and Matches

> **Status:** Planning  
> **Related:** [FastAPI Scaffold README](./README.md), [Getting Started](../../docs/getting_started.md)

---

## Overview

A preliminary step before the FastAPI app is to set up the ingestion of pieces and matches into a database, which will then be queried by the FastAPI app. The current implementation is **not database-centric**—data flows through in-memory objects (`SheetManager`, `PieceMatcher`) without persistence.

### Current Architecture Challenges

| Component      | Current State                                            | Challenge for DB                                             |
| -------------- | -------------------------------------------------------- | ------------------------------------------------------------ |
| `Sheet`        | In-memory, holds numpy arrays (`img_orig`, `img_bw`)     | Images are large binary blobs; need to store paths or encode |
| `Piece`        | In-memory, references `Contour`, `Segment`, numpy arrays | Contains computed geometry; need custom serialization        |
| `Segment`      | In-memory, holds `Contour` reference and point arrays    | Circular refs; points need serialization                     |
| `SheetManager` | Dict of sheets, no persistence                           | Need save/load methods                                       |
| `PieceMatcher` | Volatile cache (`_results`, `_lookup`)                   | Need to persist matches and reload efficiently               |

### Evaluated Approaches

**Option A: JSON/File-Based Persistence (Lightweight)**

- Serialize data models to JSON files using Pydantic's `.model_dump_json()`
- Store images as file paths, not binary blobs
- Simple, no external DB dependency
- Cons: Queries require loading all data; no indexing

**Option B: SQLite with SQLAlchemy (Structured, Local)**

- Define ORM models mirroring data classes
- Store metadata in tables; images as file refs
- Indexed queries for matches by segment/piece
- Cons: Requires ORM mapping layer

**Option C: PostgreSQL + JSONB (Production-Ready)**

- Use JSONB columns for flexible nested data
- Binary storage for contour points (optional)
- Full indexing, concurrent access
- Cons: External dependency; overkill for local dev

**Recommendation: Keep options open—evaluate after prototyping with real data.**

**DECISION:** Proceed with **Option B (SQLite)** for match storage (indexed queries at scale), combined with **JSON for metadata** (sheets, pieces). This is effectively a hybrid approach optimized for the expected query patterns.

---

## Scale Estimates

Based on expected puzzle size:

| Metric                   | Value  | Notes                                                        |
| ------------------------ | ------ | ------------------------------------------------------------ |
| Total pieces             | ~1,500 | Full puzzle                                                  |
| Sheets (images)          | ~125   | 12MP images, ~12 pieces each                                 |
| Contour points per piece | ~500   | Variable; depends on piece complexity                        |
| Segments per piece       | 4      | One per edge (LEFT, BOTTOM, RIGHT, TOP)                      |
| Total segments           | ~6,000 | 1,500 × 4                                                    |
| Match pairs (worst case) | ~18M   | C(6000,2) if matching all segments                           |
| Match pairs (realistic)  | ~4.5M  | Each segment vs ~1,500 other pieces × 4 edges, with symmetry |

### Storage Projections

| Data Type                       | Size Estimate | Calculation                                         |
| ------------------------------- | ------------- | --------------------------------------------------- |
| **Contour points (all pieces)** | ~12 MB        | 1,500 pieces × 500 pts × 2 coords × 4 bytes (int32) |
| **Contour points (JSON)**       | ~30–50 MB     | JSON overhead (~3× binary)                          |
| **Contour points (compressed)** | ~5–8 MB       | gzip/zstd on binary or JSON                         |
| **PieceRecord metadata**        | ~1 MB         | 1,500 × ~700 bytes (corners, shapes, IDs)           |
| **MatchResult (all pairs)**     | ~500 MB–1 GB  | 4.5M × ~100–200 bytes JSON each                     |
| **MatchResult (top 10%)**       | ~50–100 MB    | Filter to best matches only                         |
| **Sheet images (refs only)**    | ~10 KB        | 125 × 80 bytes (paths)                              |
| **Sheet images (12MP JPEG)**    | ~500 MB–1 GB  | 125 × 4–8 MB each (on disk, not in DB)              |

### Performance Considerations

| Operation                      | Concern                    | Mitigation                                |
| ------------------------------ | -------------------------- | ----------------------------------------- |
| Load all matches into memory   | 4.5M objects = ~2–4 GB RAM | Lazy load; store only top N per segment   |
| Query matches for one piece    | Scan 4.5M records          | Index by `piece_id`; pre-group in dict    |
| Serialize/deserialize contours | 12–50 MB I/O               | Binary format; compress; cache            |
| Full re-matching               | O(n²) comparisons          | Incremental; persist intermediate results |

### Implications for Approach Selection

| Approach                  | Viability at Scale                                               |
| ------------------------- | ---------------------------------------------------------------- |
| **Option A (JSON)**       | ⚠️ Marginal—loading 500MB+ JSON is slow; no indexing             |
| **Option B (SQLite)**     | ✅ Good—indexed queries; handles millions of rows; single file   |
| **Option C (PostgreSQL)** | ✅ Good—better for concurrent access; overkill for single-user   |
| **Option D (Hybrid)**     | ✅ Recommended—SQLite for matches, JSON/binary for contour cache |

---

## Plan

### Phase 1: Define DB-Compatible Data Models

| #   | Task                                      | Notes                                                                                                                 |
| --- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 1.1 | Create `SheetRecord` Pydantic model       | Minimal: `sheet_id`, `img_path`, `piece_count`, `threshold`, `min_area`, `created_at`                                 |
| 1.2 | Create `PieceRecord` Pydantic model       | `piece_id`, `corners`, `segment_shapes`, `oriented_piece_type`, `flat_edges`, `contour_point_count`, `contour_region` |
| 1.3 | ~~Create `SegmentRecord` Pydantic model~~ | **REMOVED:** Segments are derived from piece contour + corner indices. Store `segment_shapes` in `PieceRecord`.       |
| 1.4 | Verify `MatchResult` serialization        | Already Pydantic; ensure `model_dump(by_alias=True)` works for `similarity_manual_` field                             |

### Phase 2: Serialization/Deserialization Layer

| #   | Task                                             | Notes                                                           |
| --- | ------------------------------------------------ | --------------------------------------------------------------- |
| 2.1 | Add `SheetManager.to_records() -> dict`          | Flatten to JSON-serializable format                             |
| 2.2 | Add `SheetManager.save_metadata(path)`           | Write records to JSON                                           |
| 2.3 | Add `SheetManager.save_contour_cache(dir)`       | Write `.npz` per sheet (contour points) + JSON (corner indices) |
| 2.4 | Add `SheetManager.load_metadata(path) -> dict`   | Load records only (no object reconstruction)                    |
| 2.5 | Design lazy-load pattern for full reconstruction | `reconstruct_from_cache()` for re-matching scenarios            |

### Phase 3: PieceMatcher Persistence

| #   | Task                                              | Notes                                                       |
| --- | ------------------------------------------------- | ----------------------------------------------------------- |
| 3.1 | Add `PieceMatcher.save_matches_json(path)`        | Serialize `_results` to JSON (small scale)                  |
| 3.2 | Add `PieceMatcher.load_matches_json(path)`        | Reload matches; rebuild `_lookup` dict                      |
| 3.3 | Add `PieceMatcher.save_matches_db(path)`          | SQLite persistence with indexes                             |
| 3.4 | Add `PieceMatcher.load_matches_db(path, filters)` | Load with optional filters (piece_id, similarity threshold) |
| 3.5 | Add `PieceMatcher.get_matched_pair_keys()`        | For incremental matching support                            |

### Phase 4: Integration & Validation

| #   | Task                                                              | Notes                                  |
| --- | ----------------------------------------------------------------- | -------------------------------------- |
| 4.1 | Create prototype notebook                                         | `01_db_ingestion.ipynb` in this folder |
| 4.2 | Test round-trip: load → serialize → deserialize → query           |
| 4.3 | Benchmark query performance with ~100+ pieces                     |
| 4.4 | Validate incremental matching (add 1 sheet, match only new pairs) |

---

## Serialization Strategy

### SheetRecord (Lightweight Metadata)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path

class SheetRecord(BaseModel):
    """DB-friendly representation of a Sheet."""
    sheet_id: str
    img_path: Path                    # Relative to data root
    piece_count: int
    threshold: int = 130              # For reproducible preprocessing
    min_area: int = 80_000
    created_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_sheet(cls, sheet: Sheet, data_root: Path) -> "SheetRecord":
        return cls(
            sheet_id=sheet.sheet_id,
            img_path=sheet.img_fp.relative_to(data_root),
            piece_count=len(sheet.pieces),
            threshold=sheet.threshold,
            min_area=sheet.min_area,
        )
```

### PieceRecord (Geometry Metadata)

```python
from snap_fit.data_models.piece_id import PieceId
from snap_fit.grid.orientation import OrientedPieceType
from snap_fit.config.types import CornerPos, EdgePos

class PieceRecord(BaseModel):
    """DB-friendly representation of a Piece."""
    piece_id: PieceId
    corners: dict[str, tuple[int, int]]       # CornerPos.value -> (x, y)
    segment_shapes: dict[str, str]            # EdgePos.value -> SegmentShape.value
    oriented_piece_type: OrientedPieceType | None
    flat_edges: list[str]                     # EdgePos.value list
    contour_point_count: int
    contour_region: tuple[int, int, int, int] # (x, y, w, h)

    @classmethod
    def from_piece(cls, piece: Piece) -> "PieceRecord":
        return cls(
            piece_id=piece.piece_id,
            corners={pos.value: tuple(piece.corners[pos]) for pos in CornerPos},
            segment_shapes={pos.value: seg.shape.value for pos, seg in piece.segments.items()},
            oriented_piece_type=piece.oriented_piece_type,
            flat_edges=[e.value for e in piece.flat_edges],
            contour_point_count=len(piece.contour.cv_contour),
            contour_region=piece.contour.region,
        )
```

### MatchResult (Already Pydantic)

Existing `MatchResult` serializes cleanly:

```python
# Serialize (note by_alias=True for similarity_manual_ field)
match.model_dump_json(by_alias=True)
# {"seg_id1": {...}, "seg_id2": {...}, "similarity": 0.123, "similarity_manual": null}

# Deserialize
MatchResult.model_validate_json(json_str)
```

### Contour Binary Cache

Store contour points separately from metadata for efficiency:

```python
import numpy as np
import json
from pathlib import Path

def save_contour_cache(sheet: Sheet, cache_dir: Path) -> None:
    """Save contour points and corner indices for a sheet."""
    contours = {}
    corner_indices = {}

    for piece in sheet.pieces:
        key = str(piece.piece_id)
        contours[f"contour_{key}"] = piece.contour.cv_contour
        corner_indices[key] = {
            pos.value: int(piece.contour.corner_idxs[pos])
            for pos in CornerPos
        }

    # Binary: ~500 pts × 12 pieces × 8 bytes ≈ 48 KB per sheet
    np.savez_compressed(cache_dir / f"{sheet.sheet_id}_contours.npz", **contours)

    # JSON: corner indices (small, ~1 KB per sheet)
    (cache_dir / f"{sheet.sheet_id}_corners.json").write_text(
        json.dumps(corner_indices, indent=2)
    )


def load_contour_for_piece(piece_id: PieceId, cache_dir: Path) -> tuple[np.ndarray, dict]:
    """Load contour points and corner indices for a specific piece."""
    npz_path = cache_dir / f"{piece_id.sheet_id}_contours.npz"
    json_path = cache_dir / f"{piece_id.sheet_id}_corners.json"

    with np.load(npz_path) as data:
        contour = data[f"contour_{piece_id}"]

    with json_path.open() as f:
        all_corners = json.load(f)
        corners = all_corners[str(piece_id)]

    return contour, corners
```

---

## Reload Considerations

### Problem: Full Object Reconstruction

`Sheet` and `Piece` are **computed** objects—they derive geometry from images at load time. To reconstruct them:

1. **Approach A:** Store derived data (corners, contours as point lists)
   - Pro: No image re-processing needed
   - Con: ~30–50 MB for 1,500 pieces (acceptable); ~500 pts × 1,500 pieces

2. **Approach B:** Store only image paths + minimal config
   - Pro: Compact (~10 KB total); single source of truth
   - Con: Must re-run image processing on load (~125 sheets to process)

3. **Approach C (Hybrid):** Store metadata + cache processed results
   - Store image paths in metadata JSON
   - Store computed geometry (corners, segment shapes) in `PieceRecord`
   - Full contour points in separate binary cache (`.npz` per sheet, lazy-loaded)
   - **At 1,500 pieces:** metadata ~1 MB, contour cache ~12 MB binary

**DECISION: Approach C**—store metadata + geometry summary; contour points in binary cache; lazy-load when matching.

### Reconstruction Strategy

For most FastAPI queries, **full reconstruction is not needed**:

| Use Case            | Data Needed                        | Reconstruction?              |
| ------------------- | ---------------------------------- | ---------------------------- |
| List pieces         | `PieceRecord` from JSON/SQLite     | ❌ No                        |
| Get piece info      | `PieceRecord`                      | ❌ No                        |
| Query matches       | `MatchResult` from SQLite          | ❌ No                        |
| Display piece image | `img_fp` from `SheetRecord` + crop | ⚠️ Partial (load image only) |
| Re-run matching     | Full `Segment` objects             | ✅ Yes                       |

For re-matching scenarios, provide a reconstruction helper:

```python
def reconstruct_segment(piece_id: PieceId, edge_pos: EdgePos, cache_dir: Path) -> Segment:
    """Reconstruct a Segment from cached contour data.

    This is only needed for re-running SegmentMatcher on existing data.
    """
    from snap_fit.image.contour import Contour
    from snap_fit.image.segment import Segment
    from snap_fit.config.types import EDGE_ENDS_TO_CORNER, CornerPos

    # Load cached contour and corner indices
    contour_points, corner_indices = load_contour_for_piece(piece_id, cache_dir)

    # Rebuild minimal Contour
    contour = Contour(contour_points)
    contour.corner_idxs = {
        CornerPos(k): v for k, v in corner_indices.items()
    }

    # Get segment indices
    start_corner, end_corner = EDGE_ENDS_TO_CORNER[edge_pos]
    start_idx = corner_indices[start_corner.value]
    end_idx = corner_indices[end_corner.value]

    return Segment(contour, start_idx, end_idx)
```

---

## Querying Patterns

### Common Queries for FastAPI

| Query                  | Data Needed                                                 | Approach                          |
| ---------------------- | ----------------------------------------------------------- | --------------------------------- |
| List all pieces        | `PieceRecord[]`                                             | Load from JSON/SQLite             |
| Get piece by ID        | `PieceRecord`                                               | Index by `piece_id`               |
| Get matches for piece  | `MatchResult[]` where `piece_id` in either seg              | SQLite WHERE or filter `_results` |
| Get top N matches      | `MatchResult[]` sorted by similarity                        | Pre-sorted list or ORDER BY       |
| Get match between pair | `MatchResult`                                               | Lookup by `frozenset` key         |
| Get pieces by type     | `PieceRecord[]` where `oriented_piece_type.piece_type == X` | Filter or indexed query           |

### SheetManager Serialization Methods (Proposed)

```python
class SheetManager:
    # ... existing methods ...

    def to_records(self, data_root: Path) -> dict:
        """Export all data to JSON-serializable records."""
        from snap_fit.data_models.sheet_record import SheetRecord
        from snap_fit.data_models.piece_record import PieceRecord

        return {
            "sheets": [
                SheetRecord.from_sheet(s, data_root).model_dump(mode="json")
                for s in self.sheets.values()
            ],
            "pieces": [
                PieceRecord.from_piece(p).model_dump(mode="json")
                for s in self.sheets.values()
                for p in s.pieces
            ],
        }

    def save_metadata(self, path: Path, data_root: Path) -> None:
        """Save sheet/piece metadata to JSON."""
        import json
        path.write_text(json.dumps(self.to_records(data_root), indent=2))

    def save_contour_cache(self, cache_dir: Path) -> None:
        """Save contour points to binary .npz files (one per sheet)."""
        import json
        import numpy as np
        from snap_fit.config.types import CornerPos

        cache_dir.mkdir(parents=True, exist_ok=True)

        for sheet_id, sheet in self.sheets.items():
            contours = {}
            corner_indices = {}
            for piece in sheet.pieces:
                key = str(piece.piece_id)
                contours[f"contour_{key}"] = piece.contour.cv_contour
                corner_indices[key] = {
                    pos.value: int(piece.contour.corner_idxs[pos])
                    for pos in CornerPos
                }
            np.savez_compressed(cache_dir / f"{sheet_id}_contours.npz", **contours)
            (cache_dir / f"{sheet_id}_corners.json").write_text(
                json.dumps(corner_indices, indent=2)
            )
        lg.info(f"Saved contour cache for {len(self.sheets)} sheets to {cache_dir}")

    @classmethod
    def load_metadata(cls, path: Path) -> dict:
        """Load metadata only (not full objects) from JSON.

        Returns dict with 'sheets' and 'pieces' lists of dicts.
        Use for FastAPI queries without reconstructing full objects.
        """
        import json
        return json.loads(path.read_text())
```

### PieceMatcher Persistence Methods (Proposed)

```python
class PieceMatcher:
    # ... existing methods ...

    def save_matches_json(self, path: Path) -> None:
        """Save all match results to JSON."""
        import json
        data = [r.model_dump(by_alias=True) for r in self._results]
        path.write_text(json.dumps(data, indent=2))

    def load_matches_json(self, path: Path) -> None:
        """Load match results from JSON and rebuild lookup."""
        import json
        data = json.loads(path.read_text())
        self._results = [MatchResult.model_validate(d) for d in data]
        self._lookup = {r.pair: r for r in self._results}
        lg.info(f"Loaded {len(self._results)} matches from {path}")

    def get_matched_pair_keys(self) -> set[frozenset[SegmentId]]:
        """Get all matched pairs for incremental matching support."""
        return set(self._lookup.keys())

    def match_incremental(self, new_piece_ids: list[PieceId]) -> int:
        """Match only new pieces against existing ones.

        Args:
            new_piece_ids: Piece IDs from newly added sheets.

        Returns:
            Number of new matches computed.
        """
        existing_keys = self.get_matched_pair_keys()
        new_count = 0

        for piece_id in new_piece_ids:
            for edge_pos in EdgePos:
                new_seg_id = SegmentId(piece_id=piece_id, edge_pos=edge_pos)
                other_ids = self.manager.get_segment_ids_other_pieces(new_seg_id)

                for other_id in other_ids:
                    pair = frozenset({new_seg_id, other_id})
                    if pair not in existing_keys:
                        self.match_pair(new_seg_id, other_id)
                        new_count += 1

        self._results.sort(key=lambda x: x.similarity)
        lg.info(f"Incremental matching added {new_count} new matches")
        return new_count
```

---

## Open Questions

1. **Contour Point Storage:** Should we store full contour points for segments?
   - Needed for re-running `SegmentMatcher` on existing data
   - At scale: ~12 MB binary, ~30–50 MB JSON for 1,500 pieces
   - Options: numpy `.tobytes()` + base64, or separate `.npy`/`.npz` files
   - **DECISION:** Binary cache file, loaded on-demand

2. **Image Management:** Store images in DB (blob) or keep as file refs?
   - At scale: ~125 sheets × 4–8 MB = 500 MB–1 GB
   - **DECISION:** File refs with configurable base path (keep images on disk)

3. **Incremental Updates:** How to handle adding new sheets without re-matching all?
   - Track which pairs have been matched
   - Store `matched_pairs: set[frozenset[SegmentId]]` in matcher state
   - At scale: adding 1 sheet (~12 pieces) requires ~12 × 6,000 = 72K new comparisons

4. **Manual Similarity Overrides:** `MatchResult.similarity_manual` exists—how to persist/restore?
   - Already part of Pydantic model; will serialize

5. **Match Storage Strategy:** Store all 4.5M matches or filter?
   - **Option:** Store only top N matches per segment (e.g., top 10 = 60K records)
   - **Option:** Store all but load lazily / paginate
   - **DECISION:** Store all in SQLite; index for fast queries

6. **Memory Budget:** How much RAM can we assume?
   - Loading all matches (~4.5M) needs 2–4 GB
   - **Mitigation:** Stream/paginate; keep only working set in memory

---

## Class Adaptation Deep Dive

Based on codebase analysis, here is how each existing class relates to the DB layer and what adaptations are needed.

### Current Class Hierarchy (Immutable Objects)

```
SheetManager
├── sheets: dict[str, Sheet]
    └── Sheet
        ├── sheet_id: str
        ├── img_fp: Path
        ├── img_orig: np.ndarray          # Large binary, not persisted
        ├── img_bw: np.ndarray             # Derived, can be recomputed
        ├── contours: list[Contour]
        └── pieces: list[Piece]
            └── Piece
                ├── piece_id: PieceId      # Already Pydantic (frozen, hashable)
                ├── img_fp: Path
                ├── img_orig: np.ndarray   # Cropped from sheet, not persisted
                ├── img_bw: np.ndarray     # Derived
                ├── contour: Contour
                │   ├── cv_contour: np.ndarray   # Points, must cache
                │   └── segments: dict[EdgePos, Segment]
                ├── corners: dict[CornerPos, tuple[int, int]]
                ├── segments: dict[EdgePos, Segment]
                │   └── Segment
                │       ├── points: np.ndarray   # Subset of contour, must cache
                │       ├── shape: SegmentShape  # IN/OUT/EDGE/WEIRD
                │       ├── start_coord, end_coord
                │       └── contour: Contour     # ⚠️ Back-reference (circular)
                ├── flat_edges: list[EdgePos]
                └── oriented_piece_type: OrientedPieceType
                    ├── piece_type: PieceType (INNER/EDGE/CORNER)
                    └── orientation: Orientation (DEG_0/90/180/270)

PieceMatcher
├── manager: SheetManager            # Reference to live objects
├── _results: list[MatchResult]      # Already Pydantic
└── _lookup: dict[frozenset[SegmentId], MatchResult]  # Derived from _results
```

### Existing Pydantic Models (DB-Ready)

| Model               | Fields                                                   | Notes                                      |
| ------------------- | -------------------------------------------------------- | ------------------------------------------ |
| `PieceId`           | `sheet_id: str`, `piece_id: int`                         | ✅ Frozen, hashable, serializes cleanly    |
| `SegmentId`         | `piece_id: PieceId`, `edge_pos: EdgePos`                 | ✅ Frozen, hashable                        |
| `MatchResult`       | `seg_id1`, `seg_id2`, `similarity`, `similarity_manual_` | ✅ Has `model_dump()` / `model_validate()` |
| `OrientedPieceType` | `piece_type: PieceType`, `orientation: Orientation`      | ✅ Frozen Pydantic model                   |

### Classes Requiring Adaptation

#### 1. `Sheet` → `SheetRecord`

**Current:** Non-Pydantic class with heavy numpy data

**Adaptation:** Create lightweight `SheetRecord` for metadata only

```python
# src/snap_fit/data_models/sheet_record.py (new file)
class SheetRecord(BaseModel):
    sheet_id: str
    img_path: Path                    # Relative to data root
    piece_count: int
    threshold: int = 130              # Preprocessing param for reload
    min_area: int = 80_000
    created_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_sheet(cls, sheet: Sheet, data_root: Path) -> "SheetRecord":
        return cls(
            sheet_id=sheet.sheet_id,
            img_path=sheet.img_fp.relative_to(data_root),
            piece_count=len(sheet.pieces),
            threshold=sheet.threshold,
            min_area=sheet.min_area,
        )
```

#### 2. `Piece` → `PieceRecord`

**Current:** Heavy class with images, contours, computed geometry

**Adaptation:** Store only computed metadata; contour points in binary cache

```python
# src/snap_fit/data_models/piece_record.py (new file)
class PieceRecord(BaseModel):
    piece_id: PieceId
    corners: dict[str, tuple[int, int]]            # CornerPos.value -> (x, y)
    segment_shapes: dict[str, str]                 # EdgePos.value -> SegmentShape.value
    oriented_piece_type: OrientedPieceType | None
    flat_edges: list[str]                          # EdgePos.value list

    # Contour metadata (not full points)
    contour_point_count: int
    contour_region: tuple[int, int, int, int]      # (x, y, w, h) bounding rect

    @classmethod
    def from_piece(cls, piece: Piece) -> "PieceRecord":
        return cls(
            piece_id=piece.piece_id,
            corners={pos.value: tuple(piece.corners[pos]) for pos in piece.corners},
            segment_shapes={pos.value: seg.shape.value for pos, seg in piece.segments.items()},
            oriented_piece_type=piece.oriented_piece_type,
            flat_edges=[e.value for e in piece.flat_edges],
            contour_point_count=len(piece.contour.cv_contour),
            contour_region=piece.contour.region,
        )
```

#### 3. `Segment` → Points Binary Cache

**Current:** Holds `points: np.ndarray` and back-reference to `Contour`

**Challenge:** Circular reference (`Segment.contour -> Contour.segments -> Segment`)

**Adaptation:** Don't persist `Segment` as a record; persist contour points at piece level

```python
# Binary cache structure (per piece)
{
    "piece_id": "sheet_a:0",
    "contour_points": np.ndarray,     # Full contour, shape (N, 1, 2)
    "corner_indices": {               # To reconstruct segments
        "top_left": 123,
        "bottom_left": 456,
        ...
    }
}
```

**Why this works:** Segments are derived from contour + corner indices. We store:

1. Full contour points (binary `.npz` file per sheet)
2. Corner indices in `PieceRecord` or separate lookup

#### 4. `SheetManager` Adaptations

**Current:** In-memory dict, no persistence

**New Methods Needed:**

```python
class SheetManager:
    # Existing...

    # NEW: Export to records
    def to_records(self, data_root: Path) -> dict:
        """Export sheets/pieces to JSON-serializable records."""
        return {
            "sheets": [SheetRecord.from_sheet(s, data_root).model_dump() for s in self.sheets.values()],
            "pieces": [
                PieceRecord.from_piece(p).model_dump()
                for s in self.sheets.values()
                for p in s.pieces
            ],
        }

    def save_metadata(self, path: Path, data_root: Path) -> None:
        """Save sheet/piece metadata to JSON."""
        import json
        data = self.to_records(data_root)
        path.write_text(json.dumps(data, indent=2, default=str))

    def save_contour_cache(self, cache_dir: Path) -> None:
        """Save contour points to binary .npz files (one per sheet)."""
        for sheet_id, sheet in self.sheets.items():
            contours = {}
            corner_indices = {}
            for piece in sheet.pieces:
                key = str(piece.piece_id)
                contours[key] = piece.contour.cv_contour
                corner_indices[key] = {
                    pos.value: piece.contour.corner_idxs[pos]
                    for pos in CornerPos
                }
            np.savez_compressed(
                cache_dir / f"{sheet_id}_contours.npz",
                **{f"contour_{k}": v for k, v in contours.items()},
            )
            # Save corner indices separately (small JSON)
            (cache_dir / f"{sheet_id}_corners.json").write_text(
                json.dumps(corner_indices)
            )

    @classmethod
    def load_metadata(cls, path: Path) -> dict:
        """Load metadata only (for FastAPI queries)."""
        import json
        return json.loads(path.read_text())
```

#### 5. `PieceMatcher` Adaptations

**Current:** Volatile; `_results` and `_lookup` lost on exit

**Adaptation:** Add save/load with SQLite integration

```python
class PieceMatcher:
    # Existing...

    def save_matches_json(self, path: Path) -> None:
        """Save matches to JSON (simple, for small datasets)."""
        import json
        data = [r.model_dump(by_alias=True) for r in self._results]
        path.write_text(json.dumps(data, indent=2))

    def load_matches_json(self, path: Path) -> None:
        """Load matches from JSON and rebuild lookup."""
        import json
        data = json.loads(path.read_text())
        self._results = [MatchResult.model_validate(d) for d in data]
        self._lookup = {r.pair: r for r in self._results}
        lg.info(f"Loaded {len(self._results)} matches from {path}")

    # For SQLite (Phase 2)
    def save_matches_db(self, db_path: Path) -> None:
        """Save matches to SQLite for indexed queries."""
        # Implementation with sqlalchemy/sqlite3
        pass

    def load_matches_db(self, db_path: Path, filters: dict | None = None) -> None:
        """Load matches from SQLite with optional filters."""
        pass

    def get_matched_pair_keys(self) -> set[frozenset[SegmentId]]:
        """Get all matched pairs (for incremental matching)."""
        return set(self._lookup.keys())
```

### Identified Inconsistencies & Fixes

| Issue                                                                      | Location in Plan       | Fix                                                                                                                                                                        |
| -------------------------------------------------------------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SegmentRecord` proposed but segments lack IDs                             | Phase 1.3              | **Remove SegmentRecord**—segments are derived from piece contour + corners. Store segment shapes in `PieceRecord.segment_shapes`.                                          |
| `SheetManager.load_json` can't reconstruct full objects                    | Phase 2.3              | **Clarify:** `load_metadata()` returns records only. Full reconstruction requires `Sheet(img_fp)` + cache. Add separate `reconstruct_from_cache()` method.                 |
| Plan says "Challenge: Cannot fully reconstruct Sheet/Piece without images" | Reload Considerations  | **Decision C handles this:** Store metadata + geometry. For matching queries, only `PieceRecord` + `MatchResult` needed. Full `Piece` objects only needed for re-matching. |
| `PieceRecord` example shows `corners: dict[str, tuple[int, int]]`          | Serialization Strategy | **OK but clarify:** Keys are `CornerPos.value` strings ("top_left", etc.) for JSON compatibility.                                                                          |
| `similarity_manual_` field uses alias                                      | MatchResult            | **Ensure `by_alias=True`** in `model_dump()` calls to preserve alias in JSON.                                                                                              |
| Binary cache structure undefined                                           | Approach C             | **Added above:** `.npz` per sheet for contours, JSON for corner indices.                                                                                                   |

### Data Flow for FastAPI (Read Path)

```
[Request: GET /pieces/{piece_id}]
         │
         ▼
┌─────────────────┐
│  SQLite / JSON  │◄── Metadata: SheetRecord, PieceRecord
└────────┬────────┘
         │ Query by piece_id
         ▼
┌─────────────────┐
│  PieceRecord    │──► Response JSON
└─────────────────┘

[Request: GET /matches?piece_id=X]
         │
         ▼
┌─────────────────┐
│     SQLite      │◄── MatchResult rows indexed by seg_id1.piece_id, seg_id2.piece_id
└────────┬────────┘
         │ Query + filter
         ▼
┌─────────────────┐
│ list[MatchResult]│──► Response JSON (paginated)
└─────────────────┘
```

### Data Flow for Matching (Write Path)

```
[Load sheets from images]
         │
         ▼
┌─────────────────┐
│  SheetManager   │──► Full in-memory Sheet/Piece/Segment objects
└────────┬────────┘
         │
         ├──► save_metadata(path)     ──► metadata.json
         ├──► save_contour_cache(dir) ──► {sheet_id}_contours.npz
         │
         ▼
┌─────────────────┐
│  PieceMatcher   │
│   .match_all()  │
└────────┬────────┘
         │
         ├──► save_matches_json(path) ──► matches.json (small scale)
         └──► save_matches_db(path)   ──► matches.sqlite (large scale)
```

---

## Next Steps

- [x] User selects approach → **DECISION: Option B (SQLite)** for matches, with JSON metadata for sheets/pieces
- [x] Decide on match storage strategy → **DECISION: Store all in SQLite; index for fast queries**
- [x] Define contour storage approach → **DECISION: Binary `.npz` cache per sheet, loaded on-demand**
- [ ] Implement `SheetRecord`, `PieceRecord` data models in `src/snap_fit/data_models/`
- [ ] Add serialization methods to `SheetManager` (`.to_records()`, `.save_metadata()`, `.save_contour_cache()`)
- [ ] Add persistence methods to `PieceMatcher` (`.save_matches_json()`, `.load_matches_json()`)
- [ ] Create prototype notebook `01_db_ingestion.ipynb` to validate round-trip
- [ ] Benchmark with realistic data (~100+ pieces) to validate estimates
- [ ] (Phase 2) Add SQLite persistence for matches with indexed queries
