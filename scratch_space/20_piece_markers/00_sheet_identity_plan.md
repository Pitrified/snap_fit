# Sheet Identity & Piece Labelling - Design Plan

> **Branch target:** `feat/sheet-identity`  
> **Depends on:** existing `ArucoBoardGenerator`, `SheetAruco`, `ArucoDetectorConfig`  
> **Status:** Pre-implementation design  

---

## 1. The Real Flow (clarified)

The main pipeline is **not** the synthetic puzzle generator. That machinery
(`PuzzleGenerator`, `PuzzleSheetComposer`, `PuzzleRasterizer`) exists only for
testing with synthetic data. The real flow is:

```
[PRINT TIME]
  Generate board image  →  operator prints it  →  cuts puzzle pieces by hand

[PHOTO TIME]
  Operator places physical pieces on the board
  Operator reads the slot label for each piece (written on board background)
  Takes a photo

[INGEST TIME]
  Photo uploaded → SheetAruco.load_sheet() → Sheet → SheetManager → cache
```

The board image produced by `ArucoBoardGenerator.generate_image()` is today a
blank field with an ArUco ring. We need to embed two things into that generated
image:

1. **Sheet metadata** - machine-readable identity of the print run  
2. **Slot grid with labels** - human-readable + machine-computable piece positions

---

## 2. Preliminary Analysis: Existing Class Inventory

### 2.1 Generation side

| Class | File | Role | Output |
|-------|------|------|--------|
| `ArucoBoardConfig` | `config/aruco/aruco_board_config.py` | Pydantic config: markers_x/y, marker_length, separation, margin, dictionary_id | - |
| `ArucoBoardGenerator` | `aruco/aruco_board.py` | Builds `cv2.aruco.Board` ring; `generate_image() -> np.ndarray` | 920×1320 px numpy array (default config) |
| `ArucoDetectorConfig` | `config/aruco/aruco_detector_config.py` | Pydantic: detector params + **owns** `ArucoBoardConfig` as `board` field | - |
| `SheetArucoConfig` | `config/aruco/sheet_aruco_config.py` | Pydantic: `min_area`, `crop_margin`, `detector: ArucoDetectorConfig` | - |
| `SheetAruco` | `puzzle/sheet_aruco.py` | Wraps detector; `load_sheet(img_fp) -> Sheet` | `Sheet` object |
| `PuzzleGenerator` | `puzzle/puzzle_generator.py` | Generates Bézier puzzle geometry; produces `PuzzlePiece` list with `.label` (`A1`, `B3`…) | SVG / `PuzzlePiece` list |
| `PuzzleRasterizer` | `puzzle/puzzle_rasterizer.py` | SVG → `np.ndarray` via `cairosvg` at given DPI | BGR numpy array |
| `PuzzleSheetComposer` | `puzzle/puzzle_sheet.py` | Composites piece SVGs onto a board image | `np.ndarray` sheet image |

**Key observation:** `generate_label()` in `puzzle_generator.py` produces `LLNN`
labels (e.g. `A1`, `BC3`). This same function - and the grid logic in
`PuzzleGenerator` - can be reused directly for slot labelling on the board, with
no dependency on synthetic piece generation.

### 2.2 Parse/ingest side

| Class | File | Role |
|-------|------|------|
| `ArucoDetector` | `aruco/aruco_detector.py` | `detect_markers()` → corners/ids; `rectify()` → `np.ndarray` |
| `SheetAruco` | `puzzle/sheet_aruco.py` | Calls `rectify()`, then crops margin, constructs `Sheet` |
| `Sheet` | `puzzle/sheet.py` | Receives rectified image; runs contour detection; builds `Piece` list with `PieceId(sheet_id, piece_id_int)` |
| `SheetManager` | `puzzle/sheet_manager.py` | Aggregates sheets; serialises to `metadata.json` + `.npz` cache |
| `PieceService` | `webapp/services/piece_service.py` | Calls `SheetAruco.load_sheet` via `add_sheets()`; persists to `cache/{tag}/` |

**Key observation:** `Sheet.build_pieces()` assigns `piece_id_int` from contour
sort order (area-descending). This is **not** the same as slot label. The slot
label must be resolved by mapping contour centroid → nearest slot centre, using
the grid geometry embedded in the board config.

### 2.3 QR code: no existing code

No QR code generation or decoding exists in the project. `qrcode` (pure-Python)
is the natural addition for generation; `opencv-contrib-python` (already a
dependency) includes `cv2.QRCodeDetector` and `cv2.QRCodeDetectorAruco` for
decoding - **zero new runtime dependencies required**.

### 2.4 SVG text labels

`PuzzleGenerator.piece_to_svg()` and `to_svg()` render piece labels using SVG
`<text>` elements, then `PuzzleRasterizer.rasterize()` converts to a numpy array
via `cairosvg`. For slot labels on the board background we do not need SVG -
`cv2.putText()` on the numpy array directly is simpler and avoids the
SVG→raster round-trip. `opencv-python` is already present.

---

## 3. Board Geometry (Numbers)

All numbers are for the **default `ArucoBoardConfig`** (5×7 ring,
`marker_length=100`, `marker_separation=100`, `margin=20`). The same geometry
applies to the `oca` board (identical config).

```
Board image:  920 × 1320 px  (width × height)
Print target: A4 portrait, 210 × 297 mm
Scale:        920/210 = 4.38 px/mm  (horizontal)
              1320/297 = 4.44 px/mm  (vertical)

ArUco ring band (each side):  120 px ≈ 27 mm
  - outer margin:   20 px
  - marker length: 100 px

Interior region (inside ring):
  x = 120 … 820  →  700 px ≈ 160 mm
  y = 120 … 1220  →  1100 px ≈ 248 mm

Separation strips between ring markers:
  100 px ≈ 22.5 mm  (available between any two adjacent ring-row or ring-column markers)
```

### 3.1 QR strip zone

The **bottom interior strip** (between the last row of pieces and the bottom
ring row) is the ideal location for QR codes + human text:

```
QR + text strip:
  x = 120 … 820  (700 px = 160 mm wide - full interior width)
  y = 1100 … 1220  (120 px = 27 mm tall)

This is the gap between the bottom ring row and the interior piece area.
No markers overlap this strip. The strip is preserved through rectification
because it is inside the ring boundary.
```

Reducing the effective piece area by 120 px at the bottom:

```
Adjusted piece area:
  x = 120 … 820  →  700 px ≈ 160 mm
  y = 120 … 1100  →  980 px ≈ 220 mm
```

### 3.2 QR payload and sizing

**Metadata payload** (CSV, minimal):

```
tag_name, sheet_index, total_sheets, board_config_id, printed_at_date
e.g.  "oca,2,6,oca,20250115"   →  20 bytes
```

**QR version selection:**

| Version | Modules | Cap (ECC-M) | Size at 2 mm/module |
|---------|---------|-------------|---------------------|
| V1      | 21      | 14 bytes    | 58 mm               |
| V2      | 25      | 26 bytes    | 66 mm               |
| V3      | 29      | 42 bytes    | 74 mm               |

A single **V2 QR** at ECC-M holds 26 bytes - enough for the entire 20-byte
payload with 6 bytes to spare. Using **3× V1 QR codes** in a horizontal line
provides redundancy: any one code is sufficient to decode the full payload (each
encodes the complete payload, not a chunk). Three V1 codes at 58 mm each = 174 mm,
which fits comfortably in the 160 mm wide strip at slightly reduced module size,
or along the 297 mm tall side.

**Chosen approach:** 3 identical V1 QR codes, ECC-M (15% error correction),
placed horizontally in the QR strip. Each encodes the full payload. Decoding
succeeds if any one code is readable.

In board pixels: V1 at `module_size_px` such that total QR width ≤ 220 px
(¼ of the 700 px strip width per code). `(21 + 8) × module_size_px ≤ 220` →
`module_size_px ≤ 7.6` → use 7 px/module. At 4.38 px/mm this is 1.6 mm/module -
within reliable decoding range for clean prints.

### 3.3 Human text zone

Right of the 3 QR codes in the same strip (~346 px remaining) or immediately
above the QR strip (a single text line). Plain English:

```
PUZZLE: oca   SHEET: 02/06   2025-01-15
```

Rendered with `cv2.putText()`. Font height ~18 px (≈ 4 mm) is legible when
printed on A4.

### 3.4 Slot grid sizing

Inside the adjusted piece area (160 mm × 220 mm). The grid is driven by a new
`SlotGridConfig` (see §5.3). Example for 8 cols × 6 rows:

```
Slot width:  160 / 8 = 20 mm   →  88 px
Slot height: 220 / 6 = 37 mm   →  163 px
```

Label text `A1` … `H6` rendered at the **top-left corner** of each slot,
inset by 4 px, using `cv2.putText()` at `fontScale=0.5`, `thickness=1`,
`FONT_HERSHEY_SIMPLEX`. At 4.38 px/mm, character height ≈ 10 px ≈ 2.3 mm -
clearly legible at A4 print size.

---

## 4. Decisions (your answers integrated)

| # | Question | Decision |
|---|----------|----------|
| 1 | `SheetMetadata` shape | Structured Pydantic model: `SheetMetadata` |
| 2 | Relation to `SheetRecord` | Embed as `metadata: SheetMetadata \| None` field on `SheetRecord` |
| 3 | QR decode: pre or post rectification | **Pre-rectification** (images already nearly straight; avoids crop risk) |
| 4 | QR code count/size | 3× V1 identical QR codes; each encodes full payload; `QRChunkHandler` manages encode/decode uniformly |
| 5 | QR strip location | **Inside** the ArUco ring - in the bottom interior gap - positioned around the ring as needed |
| 6 | Board image assembly | Composited in-place: `ArucoBoardGenerator.generate_image()` remains as-is; new `BoardImageComposer` assembles all elements |

---

## 5. Architecture

### 5.1 New module: `src/snap_fit/aruco/sheet_metadata.py`

```python
class SheetMetadata(BaseModelKwargs):
    tag_name: str
    sheet_index: int                    # 0-based
    total_sheets: int
    board_config_id: str                # e.g. "oca" (matches data/aruco_boards/{id}/)
    printed_at: date = Field(default_factory=date.today)

    def to_qr_payload(self) -> str:
        """Compact CSV: 'oca,2,6,oca,20250115'"""
        ...

    @classmethod
    def from_qr_payload(cls, s: str) -> "SheetMetadata":
        ...
```

```python
class QRChunkHandler:
    """Encodes/decodes a string across N identical QR images.

    All N codes carry the full payload. Decode succeeds on any one.
    Chunked split-and-reconstruct is deferred to a future extension.
    """
    def __init__(self, n_codes: int = 3, ecc: str = "M") -> None: ...

    def encode(self, payload: str) -> list[np.ndarray]:
        """Return list of N identical QR code images (numpy arrays)."""
        ...

    def decode_first(self, image: np.ndarray) -> str | None:
        """Detect and decode any QR code in image. Returns payload or None."""
        # Uses cv2.QRCodeDetector - no new dependency
        ...
```

```python
class SheetMetadataEncoder:
    """Renders QR codes + human text onto a board image."""

    def render(
        self,
        board_img: np.ndarray,
        metadata: SheetMetadata,
        config: "MetadataZoneConfig",
    ) -> np.ndarray:
        """Return modified board image with QR strip and text."""
        ...

class SheetMetadataDecoder:
    """Extracts SheetMetadata from a raw (pre-rectified) photo."""

    def decode(self, image: np.ndarray) -> SheetMetadata | None:
        """Try to decode metadata. Returns None with a loguru warning if not found."""
        ...
```

### 5.2 New module: `src/snap_fit/aruco/slot_grid.py`

```python
class SlotGridConfig(BaseModelKwargs):
    """Defines a grid of piece slots within the board interior."""
    cols: int = Field(default=8)
    rows: int = Field(default=6)
    label_inset_px: int = Field(default=4)
    # Derived from board config at render time - not stored here

class SlotGrid:
    """Computes slot geometry and renders labels onto a board image."""

    def __init__(self, grid_config: SlotGridConfig, board_config: ArucoBoardConfig) -> None:
        ...

    def slot_centers(self) -> list[tuple[int, int]]:
        """Pixel coordinates (x, y) of each slot's centre, in label order."""
        ...

    def label_for_slot(self, col: int, row: int) -> str:
        """Returns 'A1', 'B3', etc. via generate_label()."""
        # Reuses puzzle_generator.generate_label() directly
        ...

    def render_labels(self, board_img: np.ndarray) -> np.ndarray:
        """Draws slot label text at each slot's top-left corner."""
        # cv2.putText()
        ...

    def slot_for_centroid(self, cx: int, cy: int) -> tuple[int, int] | None:
        """Map a detected contour centroid to the nearest (col, row) slot."""
        # Used at ingest time to assign labels to detected pieces
        ...
```

### 5.3 New config: `MetadataZoneConfig`

Embedded in `SheetArucoConfig` (generation side) and referenced by
`SheetMetadataEncoder` and `SlotGrid`:

```python
class MetadataZoneConfig(BaseModelKwargs):
    """Controls the QR strip and slot grid on generated board images."""
    enabled: bool = True
    qr_n_codes: int = 3                       # number of QR codes (all carry full payload)
    qr_ecc: Literal["L","M","Q","H"] = "M"
    text_enabled: bool = True                 # human-readable text alongside QR
    slot_grid: SlotGridConfig = Field(default_factory=SlotGridConfig)
```

`SheetArucoConfig` gains an optional field:
```python
metadata_zone: MetadataZoneConfig | None = None
```
When `None`, existing behaviour is unchanged.

### 5.4 New class: `BoardImageComposer`

In `src/snap_fit/aruco/board_image_composer.py`. This is the single entry point
for generating a complete board image. It replaces ad-hoc use of
`ArucoBoardGenerator.generate_image()` in notebooks/scripts:

```python
class BoardImageComposer:
    """Assembles a complete board image from its components.

    Components (all optional except ArUco board):
      1. ArUco ring  (ArucoBoardGenerator)
      2. Slot grid labels  (SlotGrid)
      3. QR metadata strip  (SheetMetadataEncoder)
      4. Human-readable text  (SheetMetadataEncoder)
    """

    def __init__(
        self,
        board_config: ArucoBoardConfig,
        metadata_zone: MetadataZoneConfig | None = None,
    ) -> None: ...

    def compose(self, metadata: SheetMetadata | None = None) -> np.ndarray:
        """Return the complete board image."""
        img = ArucoBoardGenerator(self.board_config).generate_image()
        if metadata and self.metadata_zone:
            img = SlotGrid(self.metadata_zone.slot_grid, self.board_config).render_labels(img)
            img = SheetMetadataEncoder().render(img, metadata, self.metadata_zone)
        return img
```

### 5.5 Changes to `SheetAruco.load_sheet()`

```python
# Before
def load_sheet(self, img_fp: Path) -> Sheet:

# After
def load_sheet(self, img_fp: Path) -> Sheet:
    img_orig = load_image(img_fp)

    # Decode metadata BEFORE rectification (avoids crop risk)
    metadata = SheetMetadataDecoder().decode(img_orig)   # → SheetMetadata | None
    if metadata is None:
        lg.warning(f"No sheet metadata QR found in {img_fp.name}")

    rectified = self.aruco_detector.rectify(img_orig)
    ...
    sheet = Sheet(img_fp=img_fp, min_area=self.config.min_area, image=img_final)
    sheet.metadata = metadata   # attach; see §5.6
    return sheet
```

`load_sheet()` signature is **unchanged** - return type stays `Sheet`. Metadata
is attached as an attribute. Callers that do not care about metadata are
unaffected.

### 5.6 Changes to `Sheet` and `SheetRecord`

`Sheet` gains:
```python
self.metadata: SheetMetadata | None = None   # set by SheetAruco.load_sheet()
```

`SheetRecord` gains:
```python
metadata: SheetMetadata | None = None
```

`SheetRecord.from_sheet()` propagates it:
```python
metadata=sheet.metadata
```

No schema migration needed immediately - the field is nullable and the
`DatasetStore` can store it as a JSON text column when plan 11/12 migration is
complete.

### 5.7 Slot-to-label resolution in `Sheet.build_pieces()`

After contour detection, each `Piece` currently only has a numeric index. With
the slot grid, we can assign labels:

```python
def build_pieces(self) -> None:
    ...
    slot_grid = self.metadata.slot_grid_state if self.metadata else None
    for piece_id_int, contour in enumerate(self.contours):
        label = None
        if slot_grid:
            cx, cy = contour.centroid   # (x, y) in px
            slot = slot_grid.slot_for_centroid(cx, cy)
            if slot:
                label = slot_grid.label_for_slot(*slot)
        piece_id = PieceId(sheet_id=self.sheet_id, piece_id=piece_id_int)
        piece = Piece.from_contour(..., label=label)
        ...
```

`PieceRecord` gains:
```python
label: str | None = None   # e.g. "A1", None if no slot grid available
```

---

## 6. Data Flow

### Print time

```
SheetMetadata(tag_name="oca", sheet_index=1, total_sheets=6, ...)
    │
    ▼
BoardImageComposer(board_config, metadata_zone)
    .compose(metadata)
    │
    ├── ArucoBoardGenerator.generate_image()        → base 920×1320 array
    ├── SlotGrid.render_labels(img)                 → slot labels on interior
    └── SheetMetadataEncoder.render(img, metadata)  → QR strip + text at bottom interior
    │
    ▼
numpy array  →  cv2.imwrite / PuzzleRasterizer.save()  →  PNG file  →  print
```

### Photo / ingest time

```
photo file
    │
    ▼
SheetAruco.load_sheet(img_fp)
    ├── load_image()
    ├── SheetMetadataDecoder.decode(img_orig)   ← pre-rectification, any QR code
    │       cv2.QRCodeDetector.detectAndDecode()
    │       → SheetMetadata | None
    ├── ArucoDetector.rectify(img_orig)
    ├── crop margin
    └── Sheet(image=img_final)
            sheet.metadata = metadata
            Sheet.build_pieces()
                → SlotGrid.slot_for_centroid() per contour
                → PieceRecord.label = "A1" etc.
```

---

## 7. File Touchmap

| File | Change |
|------|--------|
| `src/snap_fit/aruco/sheet_metadata.py` | **NEW** - `SheetMetadata`, `QRChunkHandler`, `SheetMetadataEncoder`, `SheetMetadataDecoder` |
| `src/snap_fit/aruco/slot_grid.py` | **NEW** - `SlotGridConfig`, `SlotGrid` |
| `src/snap_fit/aruco/board_image_composer.py` | **NEW** - `BoardImageComposer` |
| `src/snap_fit/config/aruco/sheet_aruco_config.py` | Add `metadata_zone: MetadataZoneConfig \| None = None` |
| `src/snap_fit/puzzle/sheet_aruco.py` | Call `SheetMetadataDecoder` pre-rectification; attach to `sheet.metadata` |
| `src/snap_fit/puzzle/sheet.py` | Add `metadata: SheetMetadata \| None = None`; call `SlotGrid.slot_for_centroid()` in `build_pieces()` |
| `src/snap_fit/data_models/sheet_record.py` | Add `metadata: SheetMetadata \| None = None` |
| `src/snap_fit/data_models/piece_record.py` | Add `label: str \| None = None` |
| `src/snap_fit/puzzle/puzzle_generator.py` | No changes - `generate_label()` reused as-is |
| `pyproject.toml` | Add `qrcode>=8.0` to dependencies |

`cv2.QRCodeDetector` is already available via `opencv-contrib-python`. No other
new dependencies.

---

## 8. Implementation Sequence

Each step is independently testable.

| Step | Task | Test |
|------|------|------|
| 1 | `SheetMetadata` Pydantic model + `to_qr_payload()` / `from_qr_payload()` | Round-trip unit test |
| 2 | `QRChunkHandler.encode()` + `decode_first()` | Encode payload, render to image, decode back |
| 3 | `SlotGridConfig` + `SlotGrid.slot_centers()` + `label_for_slot()` | Assert label grid matches expected `generate_label()` output |
| 4 | `SlotGrid.render_labels()` on a blank white array | Visual inspection in notebook |
| 5 | `SheetMetadataEncoder.render()` - QR strip + text | Visual + decode round-trip |
| 6 | `BoardImageComposer.compose()` - full assembly | Save image, visual check |
| 7 | `SheetMetadataDecoder.decode()` on a composed image (not rectified) | Assert metadata recovered |
| 8 | `SheetAruco.load_sheet()` integration | End-to-end: compose → save → load → assert `sheet.metadata` |
| 9 | `SlotGrid.slot_for_centroid()` + `Sheet.build_pieces()` label assignment | Synthetic contours at known slot positions |
| 10 | `SheetRecord.metadata` + `PieceRecord.label` persistence | `DatasetStore` round-trip (if SQLite migration is complete) or JSON |

---

## 9. Open Questions

| # | Question | Answer |
|---|----------| ------ |
| 1 | Should `SlotGrid` be part of `SheetMetadata` (so slot grid params travel with the QR payload) or driven purely by config at both ends? Recommendation: config-driven (grid params live in `MetadataZoneConfig`), not in QR payload - payload stays minimal. | config driven, not in QR payload |
| 2 | `QRChunkHandler` is currently "3 identical codes". The name suggests future chunking. Confirm whether the chunked (split-string) variant is in scope now or explicitly deferred. | deferred, dedicated class is there precisely to keep details of qr code handling isolated |
| 3 | `Contour.centroid` - does it exist? `Sheet.build_pieces()` will need it. Check `src/snap_fit/image/contour.py`. | check and add if needed |
| 4 | What is the source of truth for `total_sheets` at print time? It must be known before all sheets are generated (typically it's `ceil(total_pieces / slots_per_sheet)`). This drives whether `BoardImageComposer` needs to receive it externally or compute it. | might be unknown |
