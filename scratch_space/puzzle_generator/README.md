# Puzzle Generator

## Overview

Port the JavaScript jigsaw puzzle generator from `libs/jigsaw/` to Python with additional features for piece labeling and ArUco board integration.

**Goal:** Generate synthetic jigsaw puzzles with identifiable pieces that can be photographed on ArUco boards for testing the puzzle solver pipeline.

### Chosen Approach: Hybrid (SVG + Rasterization)

Generate puzzle geometry as SVG, then rasterize using `cairosvg` for image output.

**Why this approach:**

- Vector source allows clean geometry definition and optional laser cutter export
- Raster output integrates directly with existing `snap_fit` OpenCV loaders
- `cairosvg` provides reliable, consistent rasterization
- Both SVG and PNG/raster outputs available from same source

---

## Plan

### Phase 1: Core Puzzle Geometry

1. [ ] Create `PuzzleConfig` Pydantic model with parameters:

   - `width`, `height` (mm)
   - `tiles_x`, `tiles_y`
   - `tab_size` (0.1-0.3, default 0.2)
   - `jitter` (0.0-0.13, default 0.04)
   - `corner_radius` (mm)
   - `seed` (int)

2. [ ] Port random number generator with seed support:

   - Deterministic PRNG using `sin(seed) * 10000` approach
   - `random()`, `uniform(min, max)`, `rbool()` helpers

3. [ ] Create `BezierEdge` Pydantic model:

   - List of control points for cubic Bézier segments
   - `flip` direction (tab in/out)
   - Method to generate SVG path string

4. [ ] Implement edge generation:

   - 10-point Bézier curves with jitter offsets (p0-p9)
   - `generate_horizontal_edges()` → 2D list of `BezierEdge`
   - `generate_vertical_edges()` → 2D list of `BezierEdge`

5. [ ] Create `PuzzlePiece` Pydantic model:

   - `row`, `col` (grid position)
   - `label` (str, e.g., "A1", "BC12")
   - `edges`: top, right, bottom, left (`BezierEdge | None` for border)
   - `bounds` (x, y, width, height in mm)

6. [ ] Implement `PuzzleGenerator` class:
   - `__init__(config: PuzzleConfig)`
   - `generate() → list[PuzzlePiece]`
   - `to_svg() → str` (full puzzle SVG)
   - `piece_to_svg(row, col) → str` (individual piece SVG)

### Phase 2: Text Labels

7. [ ] Implement label generation with `LLNN` format:

   - Letters for columns: A-Z, then AA-AZ, BA-BZ, etc.
   - Numbers for rows: 1-9, then 01-99, 001-999, etc.
   - Auto-calculate required digits based on `tiles_x`, `tiles_y`
   - Examples:
     - 5x5 puzzle: A1, A2, ..., E5
     - 10x10 puzzle: A01, A02, ..., J10
     - 30x30 puzzle: AA01, AA02, ..., BD30

8. [ ] Add label config to `PuzzleConfig`:

   - `font_size` (auto-scale if None)
   - `font_family` (default: monospace)
   - `label_position` (center)

9. [ ] Implement `add_label_to_svg(piece_svg, label)`:
   - Render text at piece center
   - Auto-scale font to fit within piece bounds

### Phase 3: Rasterization

10. [ ] Implement `PuzzleRasterizer`:

    - `__init__(dpi: int = 300)`
    - `rasterize_puzzle(svg: str) → np.ndarray`
    - `rasterize_piece(piece_svg: str) → np.ndarray`
    - Uses `cairosvg` for SVG → PNG conversion
    - Returns OpenCV-compatible BGR numpy array

11. [ ] Add convenience methods to `PuzzleGenerator`:
    - `to_image() → np.ndarray` (full puzzle raster)
    - `piece_to_image(row, col) → np.ndarray`

### Phase 4: Sheet Composition with ArUco

12. [ ] Generate ArUco board images using existing `ArucoBoardGenerator`:

    - Create blank board with markers at edges
    - Output as raster image (PNG/numpy array)

13. [ ] Create `SheetLayout` Pydantic model:

- `sheet_width`, `sheet_height` (mm)
- `margin` (mm, space for ArUco markers)
- `piece_spacing` (mm, gap between pieces)
- `pieces_per_row`, `pieces_per_col` (auto-calculate from available space)

14. [ ] Implement `PuzzleSheetComposer`:

    - `__init__(layout: SheetLayout, aruco_board_image: np.ndarray)`
    - `place_pieces(pieces: list[PuzzlePiece], start_idx: int) → np.ndarray`
    - Paint rasterized pieces onto ArUco board image
    - Return composed sheet image

15. [ ] Implement `generate_all_sheets()`:
    - Distribute all pieces across multiple sheets
    - Return list of composed sheet images

### Phase 5: Validation & Testing

16. [ ] Create prototype notebook `01_puzzle_generator.ipynb`:

    - Test geometry generation
    - Visualize SVG output
    - Test rasterization pipeline
    - Verify tab shapes match reference

17. [ ] Create usage notebook `02_usage.ipynb`:

    - End-to-end workflow
    - Generate puzzle → add labels → rasterize → compose sheets
    - Save output images

18. [ ] Add unit tests for:
    - Deterministic seed output (same seed → same puzzle)
    - Label generation (correct format for various grid sizes)
    - Edge continuity between adjacent pieces
    - Piece bounds calculation

---

## Reference Implementation

The original JavaScript implementation in `libs/jigsaw/jigsaw.html` uses:

- **Seeded PRNG:** `Math.sin(seed) * 10000` for deterministic randomness
- **Tab geometry:** 10-point Bézier curves with jitter offsets
- **Edge directions:** `flip` boolean determines tab in/out
- **Key control points:**
  - `p0-p1`: Entry to tab
  - `p2-p6`: Tab shape (3 cubic Bézier segments)
  - `p7-p9`: Exit from tab

## Label Format

Labels follow the `LLNN` pattern (letters for columns, numbers for rows):

| Grid Size | Letter Digits | Number Digits | Example Labels |
| --------- | ------------- | ------------- | -------------- |
| 5×5       | 1 (A-E)       | 1 (1-5)       | A1, B3, E5     |
| 10×10     | 1 (A-J)       | 2 (01-10)     | A01, J10       |
| 26×26     | 1 (A-Z)       | 2 (01-26)     | A01, Z26       |
| 30×30     | 2 (AA-BD)     | 2 (01-30)     | AA01, BD30     |
| 100×100   | 2 (AA-CV)     | 3 (001-100)   | AA001, CV100   |

Letter sequence: A, B, ..., Z, AA, AB, ..., AZ, BA, BB, ...

## Dependencies

- `cairosvg` for SVG → raster conversion
- `pydantic` for data models (already in project)
- `numpy`, `opencv-python` for image handling (already in project)
- Existing `snap_fit.aruco` for board generation

## File Structure

```
src/snap_fit/puzzle/
├── puzzle_generator.py    # Core geometry generation + SVG
├── puzzle_config.py       # Pydantic config models
├── puzzle_rasterizer.py   # SVG → numpy array conversion
└── puzzle_sheet.py        # Sheet composition with ArUco

scratch_space/puzzle_generator/
├── README.md              # This file
├── 01_puzzle_generator.ipynb
└── 02_usage.ipynb
```
