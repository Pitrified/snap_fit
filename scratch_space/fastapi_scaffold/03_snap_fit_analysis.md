# snap_fit - Ingestion Pipeline & Interactive Interface Analysis

> Branch: `feat/fastapi-scaffold` · Status: Phase 0-4 complete (scaffold + data layer)

analysis done at commit

```
1260dd7c270e5f25e9e35744e76cdb0b3c283953 (HEAD -> feat/fastapi-scaffold, origin/feat/fastapi-scaffold)
Date:   Sun Apr 5 10:18:52 2026 +0200
```

---

## 1. Data Model

### Core Identifiers

| Model | Key Fields | Notes |
|---|---|---|
| `PieceId` | `sheet_id: str`, `piece_id: int` | Frozen Pydantic model; hashable; string form `sheet_id:piece_id` |
| `SegmentId` | `piece_id: PieceId`, `edge_pos: EdgePos` | Frozen; identifies one edge of one piece; string form `sheet_id:piece_id:edge` |

`EdgePos` ∈ `{LEFT, BOTTOM, RIGHT, TOP}`, `CornerPos` ∈ `{TOP_LEFT, BOTTOM_LEFT, BOTTOM_RIGHT, TOP_RIGHT}`, `SegmentShape` ∈ `{IN, OUT, EDGE, WEIRD}`.

### Persistence Records (Pydantic)

**`SheetRecord`** - metadata-only snapshot of a physical photo sheet:

```
sheet_id        str
img_path        Path        # relative to data root; image stays on disk
piece_count     int
threshold       int         # binarisation threshold used (default 130)
min_area        int         # minimum contour area (default 80_000)
created_at      datetime
```

**`PieceRecord`** - geometry metadata for one piece; no numpy arrays:

```
piece_id            PieceId
corners             dict[str, tuple[int,int]]   # CornerPos.value → (x, y)
segment_shapes      dict[str, str]              # EdgePos.value → SegmentShape.value
oriented_piece_type OrientedPieceType | None    # INNER / EDGE / CORNER
flat_edges          list[str]                   # EdgePos values of straight edges
contour_point_count int
contour_region      tuple[int,int,int,int]       # bounding rect (x, y, w, h)
```

**`MatchResult`** - similarity between two segments:

```
seg_id1             SegmentId
seg_id2             SegmentId
similarity          float       # computed score; lower = better match
similarity_manual_  float|None  # optional human override (alias: similarity_manual)
```

The `pair` property returns `frozenset({seg_id1, seg_id2})` for symmetric lookup.

### In-Memory Domain Objects

The full domain layer (used during processing only) consists of `Sheet → [Piece → {Contour, Segment×4}]`. These hold numpy arrays and are never persisted directly - they are serialised to the record types above.

---

## 2. Ingestion Pipeline

### 2a. Batch Ingestion (API endpoint)

Entry point: `POST /api/v1/pieces/ingest` → `PieceService.ingest_sheets(sheets_tag, data_dir)`.

**Expected directory layout:**

```
data/
└── {sheets_tag}/
    ├── {sheets_tag}_SheetArucoConfig.json   ← ArUco board config
    └── sheets/
        ├── back_01.jpg
        ├── back_02.jpg
        └── ...
```

**Pipeline steps:**

1. `SheetArucoConfig` is loaded from the JSON config file.
2. A `SheetAruco` instance wraps the config and exposes a `load_sheet(path) → Sheet` loader.
3. `SheetManager.add_sheets(folder, pattern="*.jpg", loader_func=aruco_loader)` globs all images and calls the loader per file. The sheet ID is derived from the image filename relative to the sheets folder.
4. Inside each `load_sheet` call, ArUco markers are detected to establish orientation/scale, contours are found against the binarised image, and each contour becomes a `Piece` with four `Segment` objects.
5. After all sheets are loaded, the manager serialises to the cache:
   - `SheetManager.save_metadata(tag_dir/metadata.json)` → sheets + pieces as JSON.
   - `SheetManager.save_contour_cache(tag_dir/contours/)` → one `.npz` (compressed numpy) per sheet for contour point arrays, plus one `_corners.json` per sheet for corner indices.

The response is `IngestResponse {sheets_tag, sheets_ingested, pieces_detected, cache_path}`.

### 2b. Interactive / Incremental Ingestion

Not yet exposed via a dedicated API route (the `/api/v1/interactive/session` endpoint is a stub returning `{session_id: "placeholder", active: false}`).

The domain layer supports incremental ingestion through `PieceMatcher.match_incremental(new_piece_ids)`, which matches only newly added pieces against existing ones, skipping already-computed pairs. The design intent is to add sheets one at a time without full re-matching.

---

## 3. Storage & Reload

### Storage Layout

```
cache/
└── {sheets_tag}/
    ├── metadata.json          ← SheetRecord[] + PieceRecord[] (JSON)
    └── contours/
        ├── {sheet_id}_contours.npz    ← contour point arrays (compressed)
        └── {sheet_id}_corners.json    ← corner indices per piece

cache/
└── {sheets_tag}/
    └── matches.json           ← MatchResult[] (JSON, sorted by similarity)
```

All image files remain on disk under `data/`; only paths are persisted.

### Storage Scale Targets

| Artefact | Estimated size (1,500 pieces) |
|---|---|
| `metadata.json` | ~1 MB |
| Contour `.npz` files | ~5-12 MB (compressed binary) |
| `matches.json` (top % only) | ~50-100 MB |
| Full match set (4.5M pairs) | ~500 MB-1 GB → SQLite planned |

### Reload

**Metadata reload** (`PieceService`): On every list/get request, `SheetManager.load_metadata(tag_dir/metadata.json)` is called per tag directory. This deserialises JSON → `SheetRecord`/`PieceRecord` via `model_validate`. There is no in-memory cache at the service layer; each request re-reads from disk.

**Contour reload**: `SheetManager.load_contour_for_piece(piece_id, cache_dir)` loads the `.npz` and `_corners.json` for the piece's sheet on demand (not called automatically during normal API queries - available for geometry reconstruction when needed).

**Match reload** (`PuzzleService`): `PieceMatcher.load_matches_json(path)` deserialises `MatchResult[]` and rebuilds the `frozenset → MatchResult` lookup dict. Again, no service-level cache; called per request.

### Path Resolution

Configured via `pydantic-settings` from `.env`:

```
data_dir  = "data"    → settings.data_path   (source images + configs)
cache_dir = "cache"   → settings.cache_path  (all derived artefacts)
```

---

## 4. Interactive Puzzle Interface

### Routing Structure

| Prefix | Router | Purpose |
|---|---|---|
| `/api/v1/pieces` | `piece_ingestion` | REST: ingest, list, get sheets/pieces |
| `/api/v1/puzzle` | `puzzle_solve` | REST: query matches, trigger solve |
| `/api/v1/interactive` | `interactive` | Stub: session state (not yet implemented) |
| `/` (HTML) | `ui` | Jinja2 admin UI: browse sheets, pieces, matches |

### How the Puzzle is Browsed Interactively

The UI router renders Jinja2 templates with data sourced live from the service layer:

- **`/sheets`** - lists all `SheetRecord`s across all cached datasets.
- **`/sheets/{sheet_id}`** - shows sheet metadata + all `PieceRecord`s for that sheet.
- **`/pieces`** - flat list of all pieces.
- **`/pieces/{piece_id}`** - piece detail with top 20 `MatchResult`s for that piece.
- **`/matches`** - paginated match list (default 100), showing total count.

### Match Data - How It's Stored and Queried

Match computation is a separate offline step (not triggered by the ingest endpoint). `PieceMatcher.match_all()` computes all segment-vs-segment similarities and `save_matches_json()` writes the result to `cache/{sheets_tag}/matches.json`.

At query time:

- `PuzzleService.list_matches(limit, min_similarity)` - loads all matches.json files, filters and sorts by similarity (ascending = best first), returns top N.
- `PuzzleService.get_matches_for_piece(piece_id)` - filters to matches where either `seg_id1` or `seg_id2` belongs to the piece.
- `PuzzleService.get_matches_for_segment(piece_id, edge_pos)` - further narrows to a specific edge.

The `similarity_manual` field allows a human override to be set on any `MatchResult` without discarding the computed score; `similarity_manual` falls back to `similarity` if not set.

### Puzzle Solve

`POST /api/v1/puzzle/solve` with `{piece_ids?, config_path?}` is wired but returns a stub response (`"Solver integration pending"`). The `naive_linear_solver` module exists in `src/snap_fit/solver/` but is not yet connected to the API service layer.

---

## 5. Summary

| Concern | Current approach | Planned evolution |
|---|---|---|
| Metadata persistence | JSON files per dataset tag | SQLite for match data at scale |
| Contour persistence | Binary `.npz` + corner JSON | Stable; no change planned |
| Match persistence | JSON (all results) | SQLite with indexing (Phase 2+) |
| Service-layer caching | None (disk read per request) | To be added when scale demands |
| Interactive session | Stub | To be implemented |
| Solver integration | Domain module exists; not wired | Pending Phase 5+ |
