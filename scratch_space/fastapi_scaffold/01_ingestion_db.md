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

| #   | Task                                  | Notes                                                                                     |
| --- | ------------------------------------- | ----------------------------------------------------------------------------------------- |
| 1.1 | Create `SheetRecord` Pydantic model   | Minimal: `sheet_id`, `img_path`, `piece_count`, `created_at`                              |
| 1.2 | Create `PieceRecord` Pydantic model   | `piece_id: PieceId`, `sheet_id`, `corners`, `segment_shapes`, `oriented_type`             |
| 1.3 | Create `SegmentRecord` Pydantic model | `segment_id: SegmentId`, `shape: SegmentShape`, `point_count`, `start_coord`, `end_coord` |
| 1.4 | Extend `MatchResult` for persistence  | Already Pydantic; ensure `model_dump()` works                                             |

### Phase 2: Serialization/Deserialization Layer

| #   | Task                                                 | Notes                                                                  |
| --- | ---------------------------------------------------- | ---------------------------------------------------------------------- |
| 2.1 | Add `SheetManager.to_records() -> list[SheetRecord]` | Flatten to DB-friendly format                                          |
| 2.2 | Add `SheetManager.save_json(path)`                   | Write records to JSON                                                  |
| 2.3 | Add `SheetManager.load_json(path)`                   | **Challenge:** Cannot fully reconstruct `Sheet`/`Piece` without images |
| 2.4 | Design lazy-load pattern for images                  | Only load images when needed for matching                              |

### Phase 3: PieceMatcher Persistence

| #   | Task                                           | Notes                                  |
| --- | ---------------------------------------------- | -------------------------------------- |
| 3.1 | Add `PieceMatcher.save_matches(path)`          | Serialize `_results` list to JSON      |
| 3.2 | Add `PieceMatcher.load_matches(path, manager)` | Reload matches; rebuild `_lookup` dict |
| 3.3 | Support incremental matching                   | Load existing, match only new pairs    |

### Phase 4: Integration & Validation

| #   | Task                                                    | Notes                                  |
| --- | ------------------------------------------------------- | -------------------------------------- |
| 4.1 | Create prototype notebook                               | `01_db_ingestion.ipynb` in this folder |
| 4.2 | Test round-trip: load → serialize → deserialize → query |
| 4.3 | Benchmark query performance                             |

---

## Serialization Strategy

### SheetRecord (Lightweight Metadata)

```python
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path

class SheetRecord(BaseModel):
    """DB-friendly representation of a Sheet."""
    sheet_id: str
    img_path: Path
    piece_count: int
    created_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_sheet(cls, sheet: Sheet) -> "SheetRecord":
        return cls(
            sheet_id=sheet.sheet_id,
            img_path=sheet.img_fp,
            piece_count=len(sheet.pieces),
        )
```

### PieceRecord (Geometry Metadata)

```python
class PieceRecord(BaseModel):
    """DB-friendly representation of a Piece."""
    piece_id: PieceId
    sheet_id: str
    corners: dict[str, tuple[int, int]]  # CornerPos -> (x, y)
    segment_shapes: dict[str, str]  # EdgePos -> SegmentShape
    oriented_type: str | None

    @classmethod
    def from_piece(cls, piece: Piece) -> "PieceRecord":
        return cls(
            piece_id=piece.piece_id,
            sheet_id=piece.piece_id.sheet_id,
            corners={pos.value: tuple(piece.corners[pos]) for pos in piece.corners},
            segment_shapes={pos.value: piece.segments[pos].shape.value for pos in piece.segments},
            oriented_type=piece.oriented_piece_type.value if piece.oriented_piece_type else None,
        )
```

### MatchResult (Already Pydantic)

Existing `MatchResult` serializes cleanly:

```python
# Serialize
match.model_dump_json()
# {"seg_id1": {...}, "seg_id2": {...}, "similarity": 0.123}

# Deserialize
MatchResult.model_validate_json(json_str)
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
   - Store image paths in DB
   - Store computed geometry (corners, segment shapes) as compact JSON/binary
   - Full contour points in separate cache file (lazy-loaded)
   - **At 1,500 pieces:** metadata ~1 MB, contour cache ~12 MB binary

**Recommendation:** Approach C—store metadata + geometry summary; contour points in binary cache; lazy-load when matching.

---

## Querying Patterns

### Common Queries for FastAPI

| Query                  | Data Needed                                    | Approach                       |
| ---------------------- | ---------------------------------------------- | ------------------------------ |
| List all pieces        | `PieceRecord[]`                                | Load from JSON/DB              |
| Get piece by ID        | `PieceRecord`                                  | Index by `piece_id`            |
| Get matches for piece  | `MatchResult[]` where `piece_id` in either seg | Filter `_results` or SQL WHERE |
| Get top N matches      | `MatchResult[]` sorted by similarity           | Pre-sorted list or ORDER BY    |
| Get match between pair | `MatchResult`                                  | Lookup by `frozenset` key      |

### SheetManager Serialization Methods (Proposed)

```python
class SheetManager:
    # ... existing methods ...

    def to_records(self) -> dict:
        """Export all data to serializable records."""
        return {
            "sheets": [SheetRecord.from_sheet(s).model_dump() for s in self.sheets.values()],
            "pieces": [
                PieceRecord.from_piece(p).model_dump()
                for s in self.sheets.values()
                for p in s.pieces
            ],
        }

    def save_json(self, path: Path) -> None:
        """Save sheet/piece metadata to JSON."""
        path.write_text(json.dumps(self.to_records(), indent=2, default=str))

    @classmethod
    def load_metadata(cls, path: Path) -> dict:
        """Load metadata (not full objects) from JSON."""
        return json.loads(path.read_text())
```

### PieceMatcher Persistence Methods (Proposed)

```python
class PieceMatcher:
    # ... existing methods ...

    def save_matches(self, path: Path) -> None:
        """Save all match results to JSON."""
        data = [r.model_dump() for r in self._results]
        path.write_text(json.dumps(data, indent=2))

    def load_matches(self, path: Path) -> None:
        """Load match results from JSON and rebuild lookup."""
        data = json.loads(path.read_text())
        self._results = [MatchResult.model_validate(d) for d in data]
        self._lookup = {r.pair: r for r in self._results}
        lg.info(f"Loaded {len(self._results)} matches from {path}")
```

---

## Open Questions

1. **Contour Point Storage:** Should we store full contour points for segments?
   - Needed for re-running `SegmentMatcher` on existing data
   - At scale: ~12 MB binary, ~30–50 MB JSON for 1,500 pieces
   - Options: numpy `.tobytes()` + base64, or separate `.npy`/`.npz` files
   - **Leaning:** Binary cache file, loaded on-demand

2. **Image Management:** Store images in DB (blob) or keep as file refs?
   - At scale: ~125 sheets × 4–8 MB = 500 MB–1 GB
   - **Recommendation:** File refs with configurable base path (keep images on disk)

3. **Incremental Updates:** How to handle adding new sheets without re-matching all?
   - Track which pairs have been matched
   - Store `matched_pairs: set[frozenset[SegmentId]]` in matcher state
   - At scale: adding 1 sheet (~12 pieces) requires ~12 × 6,000 = 72K new comparisons

4. **Manual Similarity Overrides:** `MatchResult.similarity_manual` exists—how to persist/restore?
   - Already part of Pydantic model; will serialize

5. **Match Storage Strategy:** Store all 4.5M matches or filter?
   - **Option:** Store only top N matches per segment (e.g., top 10 = 60K records)
   - **Option:** Store all but load lazily / paginate
   - **Leaning:** Store all in SQLite; index for fast queries

6. **Memory Budget:** How much RAM can we assume?
   - Loading all matches (~4.5M) needs 2–4 GB
   - **Mitigation:** Stream/paginate; keep only working set in memory

---

## Next Steps

- [ ] User selects approach (A: JSON-first, B: SQLite, C: PostgreSQL, D: Hybrid)
- [ ] Decide on match storage strategy (all vs top-N per segment)
- [ ] Implement `SheetRecord`, `PieceRecord` data models
- [ ] Add serialization methods to `SheetManager`
- [ ] Add persistence methods to `PieceMatcher`
- [ ] Create prototype notebook to validate round-trip
- [ ] Benchmark with realistic data (~100+ pieces) to validate estimates

Prima linea di meteo
Príncipessa sofia
Prato
Guernica dopo le 5 grayis
Templo de bom , resti egizi. Per. Il tramonto
Debod
Palazzo reale
Panino con frittura di calamari e maio all'aglio
Bar la campana
Plaza del sol
Retiro
Palazzo di cristallo anche dentro
Cabify
