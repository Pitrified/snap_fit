# Sheet Identity & Piece Labelling - Problem Definition and Options

> **Context:** `snap_fit` - `feat/fastapi-scaffold` branch  
> **Related code:** `ArucoBoardGenerator`, `PuzzleSheetComposer`, `SheetArucoConfig`, `SheetRecord`  
> **Status:** Brainstorm / pre-planning --> superseded by `scratch_space/20_piece_markers/00_sheet_identity_plan.md`

---

## 1. Problem Statement

### 1.1 Current situation

`ArucoBoardGenerator` produces a *ring* of ArUco markers that is embedded in the
printed sheet image by `PuzzleSheetComposer`. After photographing, `SheetAruco`
detects these markers, performs perspective correction (rectification), and passes
the rectified image to `Sheet` for piece contour detection.

The ArUco ring serves **one purpose only: geometric reprojection**. The markers
carry no data other than their ID within the ring, which is used purely for
homography estimation.

### 1.2 Two missing links

Once a photo has been taken and processed, the pipeline needs to answer two
questions it currently cannot answer:

#### Problem A - Sheet identity

> *Which photo belongs to which dataset / batch / physical print-run?*

A photo file arriving at the ingest endpoint is a bag of pixels. Nothing in the
image encodes:

- which puzzle it belongs to (`tag_name` / `sheets_tag`)
- which physical sheet within that puzzle it is (sheet index)
- what configuration was used (board parameters, piece grid, threshold)
- when it was printed

Without this, the operator must name files manually or track a separate spreadsheet
side-channel. Any mismatch silently produces wrong results downstream.

#### Problem B - Piece identity

> *Which physical piece in the photo is piece `A1`, `B3`, etc.?*

`PuzzleSheetComposer` places pieces in a grid and assigns each a label (e.g. `A1`
via `generate_label()`). But once printed and cut, **the machine only knows a
piece by its pixel position on the sheet** - it derives a `PieceId(sheet_id,
piece_idx)` from contour detection order, which is fragile. The human operator who
will physically handle pieces cannot cross-reference the machine index to the
printed label without an explicit visual mapping.

This matters for:

- Re-ingestion or correction (operator marks a piece as "re-scanned")
- Manual overrides in the webapp (`similarity_manual_` field on `MatchResult`)
- Any future physical manipulation step (placing solved pieces)

---

## 2. Design Constraints

These come from the existing codebase conventions:

- **No new heavy dependencies.** The project uses `opencv-python`, `numpy`,
  `pydantic`, `qrcode` is acceptable (pure-Python, stdlib-compatible); `zxing` or
  heavy barcode libs are not.
- **Generated at print time.** Metadata must be baked into the image that
  `PuzzleSheetComposer` produces - not added later.
- **Read at ingest time.** `SheetAruco.load_sheet()` is the natural decode point,
  after rectification but before `Sheet` construction.
- **Config-driven.** New layout parameters belong in `SheetLayout` or a new
  `SheetIdentityConfig`, consistent with `ArucoBoardConfig` / `SheetArucoConfig`
  patterns.
- **Graceful degradation.** If a QR / label zone is not found, the pipeline should
  warn (loguru) and continue - not crash.

---

## 3. Problem A - Sheet Identity (metadata encoding)

### What needs to be encoded

Minimum viable metadata payload (JSON-serialisable, mirrors existing
`SheetRecord` / `config_puzzle_v2.json` fields):

```
tag_name        str       e.g. "oca"
sheet_index     int       0-based index within the tag's sheet set
board_config_id str       reference to the ArucoBoardConfig used (e.g. "oca")
printed_at      ISO 8601  timestamp of image generation
```

Optional (can be reconstructed from `tag_name` + `sheet_index`):
```
piece_count     int
tiles_x / tiles_y int
```

### Option A1 - QR code zone outside the ArUco ring

Place one or more `qrcode`-generated QR codes in the outer margin of the sheet,
**outside** the ArUco ring perimeter. The QR code encodes the metadata as compact
JSON or a URL-like string.

**Where:** The ring board is a frame; the "outside" is the area beyond the
outermost marker row/column. Currently `ArucoBoardConfig.margin = 20 px` - this
margin could host a QR code strip at a corner.

**Pros:**
- `qrcode` is a pure-Python library, minimal footprint.
- Machine-scannable independently of the aruco pipeline (phone camera, webapp
  upload flow).
- Can be decoded *before* rectification (useful if rectification fails).
- QR codes survive moderate rotation and perspective distortion - redundancy with
  ArUco.

**Cons:**
- Needs space in the margin; current margin (20 px at board pixel resolution) is
  too small. Margin must be enlarged or QR placed inside a dedicated strip.
- After `crop_margin` in `SheetAruco.load_sheet()`, the QR zone may be cropped
  away - must decode *before* cropping, or adjust `crop_margin`.
- Adds a second decode step in `SheetAruco`.

**Fit with codebase:** A `SheetMetadataEncoder` class in
`src/snap_fit/aruco/sheet_metadata.py` would generate the QR image;
`ArucoBoardGenerator.generate_image()` (or `PuzzleSheetComposer`) composites it
in. Decoding lives in a `SheetMetadataDecoder` counterpart called from
`SheetAruco.load_sheet()` on the pre-crop image.

---

### Option A2 - Human-readable text block alongside a QR code

Pair the QR code (Option A1) with a printed text block in the same margin zone,
in plain English:

```
PUZZLE: oca
SHEET:  02 / 06
DATE:   2025-01-15
```

OpenCV's `cv2.putText()` or PIL/Pillow can render this directly onto the numpy
array.

**Pros:**
- Zero ambiguity for a human inspecting a printout - no scanner needed.
- Works as a fallback when QR decode fails.
- Trivially added on top of A1 (same margin zone, stacked).

**Cons:**
- Text is not machine-parseable (no OCR in the pipeline). The QR code remains
  the machine-readable path; text is purely for operators.
- Adds layout complexity (must not overlap markers or piece area).

**Fit with codebase:** Same `SheetMetadataEncoder` renders both the QR and the
text block. `cv2.putText()` is already a dependency via `opencv-python`.

---

### Option A3 - Steganography / invisible watermark

Embed metadata in the image's high-frequency pixel noise (imperceptible to
the eye) using a library such as `invisible-watermark`.

**Verdict: Not recommended.** Steganography is fragile to JPEG compression,
printing/scanning noise, and perspective distortion - all of which apply here.
Adds a heavy, uncommon dependency. Mentioned for completeness; discard.

---

### Option A4 - Filename convention only (current implicit approach)

Keep relying on the operator to name files correctly (e.g. `oca_sheet_02.jpg`)
and parse the tag from the filename at ingest time.

**Verdict: Insufficient.** Filename is not part of the image; it is lost when
files are copied, renamed, or uploaded through the webapp. The FastAPI ingest
endpoint already receives a `sheets_tag` parameter as a workaround, but this is
manual. Does not solve the problem.

---

### Recommendation for Problem A

**A1 + A2 combined.** One QR code in a corner of the outer margin, plus a
small human-readable text block beside it. The QR encodes compact JSON; the text
provides a visual label. Both are generated at print time by an extended
`PuzzleSheetComposer` and decoded by `SheetAruco` on the pre-crop image.

`crop_margin` must be set to preserve the outer margin zone, or the decode step
must run before the crop. The latter is cleaner - decode metadata from the
pre-rectified image, then proceed with crop as today.

---

## 4. Problem B - Piece Identity (grid labelling)

### What needs to be communicated

`PuzzleSheetComposer` already places pieces in a regular grid and knows each
piece's `(row, col)` and `label` (e.g. `A1`). The problem is that **none of this
is visible in the photo in a machine-parseable or human-legible way at the slot
level**.

The machine derives `piece_idx` from contour detection order, which is not
guaranteed to match printing order. The human has no way to know that the piece
in the upper-left slot is `A1` without looking at the original print template.

### Option B1 - Grid slot labels printed on the sheet background

Print the label of each slot (e.g. `A1`, `B3`) directly onto the sheet
background, inside the slot area but positioned so it remains visible after the
puzzle piece is placed (e.g. at a corner of the slot, outside the piece bounding
box).

**Machine use:** After rectification, the machine computes slot positions
geometrically from the known grid layout (derived from `SheetLayout` +
`ArucoBoardConfig`), reads the label *from the config* (not from the image), and
assigns each detected contour to the nearest slot. No OCR needed.

**Human use:** The operator places a physical piece in a slot, glances at the
printed corner label, and can optionally hand-write or mark the label on the
piece itself.

**Pros:**
- Already partially supported: `PuzzleSheetComposer.place_pieces()` renders piece
  SVGs with `include_label=True`. The label just needs to also appear in the
  background slot.
- No new image-recognition step; slot assignment is geometric.
- Works with the existing `generate_label()` → `A1` / `B2` scheme.

**Cons:**
- Labels may be occluded by the placed piece if positioned carelessly - must be
  placed at a consistent corner offset.
- Requires `SheetLayout` to know piece spacing precisely at render time (already
  available via `pieces_per_sheet()`).

**Fit with codebase:** New method `PuzzleSheetComposer.render_slot_labels()` that
draws each label at a fixed inset from the slot's top-left corner, called before
`place_pieces()`. The slot geometry is already computed in `place_pieces()` -
extract it into a shared helper.

---

### Option B2 - Per-slot QR codes

Each grid slot gets its own small QR code encoding the slot's label + position.
The QR is printed in the background of the slot.

**Machine use:** Detect and decode each QR after rectification to read `{label,
row, col}` for every slot, replacing the geometric contour→slot assignment.

**Pros:**
- Fully self-describing: the image carries slot identity explicitly, no reliance
  on grid geometry.
- Robust to layout variation (different `sheet_width`, `piece_spacing` values).

**Cons:**
- At 300 DPI and ~25 mm slots, a QR code in a slot corner must be very small
  (~6-8 mm), approaching the reliable decoding limit.
- 48 QR codes on a single sheet (for an 8×6 grid) is visually noisy and
  computationally expensive to decode.
- Largely redundant if the sheet-level metadata QR (Problem A) already encodes
  `tag_name` + `sheet_index`, from which the grid layout is fully determined.

**Verdict:** Overkill given Option B1's geometric approach. Viable only if layout
is unknown at decode time. Recommend against for the current use case.

---

### Option B3 - Human label strip / index card

Print a reference strip outside the ArUco ring (in the margin, similar to the
metadata zone in A1/A2) listing all slots and their labels:

```
SHEET 02  |  A1 A2 A3 A4 A5 A6 A7 A8
           |  B1 B2 B3 B4 B5 B6 B7 B8
           |  ...
```

This is a pure human-readable aid. The machine still uses geometric slot
assignment (B1). The operator can use the strip to manually label cut pieces
before they are placed back (e.g. with a marker pen).

**Pros:** Trivial to generate with `cv2.putText()`; no additional decode logic.
**Cons:** Redundant with in-slot labels (B1) if those are already visible at the
corner. Most useful if pieces are cut and handled loose, away from the sheet.

**Fit with codebase:** Part of the same `SheetMetadataEncoder` text-rendering
pass as Option A2.

---

### Option B4 - Slot index encoded in the ArUco marker IDs

Assign ArUco marker IDs to carry slot-position information (e.g. marker 0 = slot
A1, marker 1 = slot A2, …). The ring already uses a subset of the dictionary;
interior markers (currently not used) could carry slot data.

**Verdict: Not recommended.** The ring layout is chosen for geometric
reprojection quality, not data density. Overloading marker IDs with slot
semantics couples two concerns that are currently cleanly separated. The
`DICT_6X6_250` dictionary has 250 IDs; a 48-piece sheet would need 48 interior
markers plus the ring - feasible but cluttered. Discard.

---

### Recommendation for Problem B

**B1 as the primary mechanism, B3 as a supplementary human aid.**

- The background of each slot gets a small `label` printed at its top-left
  corner (outside the piece area) by a new `render_slot_labels()` method in
  `PuzzleSheetComposer`.
- Geometric slot assignment (contour centroid → nearest slot center) handles the
  machine side, driven by the grid parameters already in `SheetLayout`.
- A compact label index strip in the margin (B3) provides a quick human
  cross-reference, especially useful after pieces are cut and loose.

---

## 5. Proposed Architecture

The changes touch three layers and introduce one new module:

```
src/snap_fit/
├── aruco/
│   ├── aruco_board.py              (existing - no changes)
│   ├── aruco_detector.py           (existing - no changes)
│   └── sheet_metadata.py           (NEW)
│       ├── SheetMetadata           Pydantic model (tag_name, sheet_index, ...)
│       ├── SheetMetadataEncoder    generate_image(metadata) -> np.ndarray
│       └── SheetMetadataDecoder    decode_from_image(img) -> SheetMetadata | None
│
├── config/aruco/
│   └── sheet_aruco_config.py       (existing - add metadata_zone: MetadataZoneConfig)
│
└── puzzle/
    ├── puzzle_sheet.py             (existing - add render_slot_labels(),
    │                                render_metadata_zone() to PuzzleSheetComposer)
    └── sheet_aruco.py              (existing - call decoder before crop in load_sheet())
```

### `SheetMetadata` Pydantic model

```python
class SheetMetadata(BaseModelKwargs):
    tag_name: str
    sheet_index: int
    total_sheets: int
    board_config_id: str   # references data/aruco_boards/{id}/
    printed_at: datetime = Field(default_factory=datetime.now)
```

This is written to the QR at print time and read back into a `SheetRecord`
extension (or a separate `SheetRecord.metadata` field) at ingest.

### `MetadataZoneConfig`

New config embedded in `SheetArucoConfig` (or `SheetLayout`):

```python
class MetadataZoneConfig(BaseModelKwargs):
    enabled: bool = True
    corner: Literal["top-left", "top-right", "bottom-left", "bottom-right"] = "bottom-right"
    qr_size_mm: float = 15.0       # physical QR size
    text_enabled: bool = True       # render human-readable text alongside QR
    slot_labels_enabled: bool = True
    label_strip_enabled: bool = True
```

### Decode point in `SheetAruco.load_sheet()`

```python
def load_sheet(self, img_fp: Path) -> tuple[Sheet, SheetMetadata | None]:
    img_orig = load_image(img_fp)
    metadata = SheetMetadataDecoder().decode_from_image(img_orig)  # before rectify
    if metadata is None:
        lg.warning(f"No sheet metadata found in {img_fp}")
    rectified = self.aruco_detector.rectify(img_orig)
    ...
    return Sheet(...), metadata
```

Return type changes to a tuple - callers that only need `Sheet` can unpack and
discard `metadata`. Alternatively wrap in a dataclass `LoadedSheet(sheet, metadata)`.

---

## 6. Open Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | Should `load_sheet()` return `(Sheet, SheetMetadata | None)` or a `LoadedSheet` dataclass? | API shape of `SheetAruco` |
| 2 | Where does `SheetMetadata` live relative to `SheetRecord`? Embed as a field, or keep separate? | `DatasetStore` schema migration |
| 3 | Should QR decoding happen pre- or post-rectification? Pre is safer (no crop risk) but the image may be more distorted. | `SheetMetadataDecoder` robustness |
| 4 | What is the minimum QR physical size at 300 DPI that reliably decodes after JPEG compression? Needs empirical testing. | `MetadataZoneConfig.qr_size_mm` default |
| 5 | Should the label strip (B3) be on the same side as the QR zone (A1/A2) to keep one margin "information-dense"? | `PuzzleSheetComposer` layout |
| 6 | Does `ArucoBoardConfig.margin` need to grow to accommodate the metadata zone, or should the zone use a separate outer border? | Print layout / `SheetLayout` |
