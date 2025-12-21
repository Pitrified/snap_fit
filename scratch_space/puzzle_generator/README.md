# Puzzle Generator

## Overview

Port the JavaScript jigsaw puzzle generator from `libs/jigsaw/` to Python with additional features for piece labeling and ArUco board integration.

**Goal:** Generate synthetic jigsaw puzzles with identifiable pieces that can be photographed on ArUco boards for testing the puzzle solver pipeline.

### Option A: Pure SVG Output (Minimal Dependencies)

Generate puzzles as SVG files using Python's `svgwrite` or raw XML string building.

**Pros:**
- Lightweight, no heavy dependencies
- Direct port of the JS logic
- Easy to integrate with laser cutters / printing
- Clean vector output

**Cons:**
- Text rendering may vary across SVG viewers
- Need separate rasterization step for image-based workflows

### Option B: OpenCV/PIL Rasterized Output

Generate puzzles directly as raster images using OpenCV or PIL.

**Pros:**
- Consistent output across platforms
- Direct integration with existing `snap_fit` image pipeline
- Easy to add text labels with `cv2.putText`

**Cons:**
- Heavier dependencies
- Need to implement Bézier curve rendering
- Fixed resolution (vs scalable SVG)

### Option C: Hybrid Approach (SVG + Rasterization)

Generate puzzle geometry as SVG, then rasterize using `cairosvg` or `svglib` for image output.

**Pros:**
- Best of both worlds: vector source, raster output
- Can export both formats
- Cleaner separation of concerns

**Cons:**
- Additional dependency (`cairosvg`)
- Two-step process

---

**Recommendation:** Start with **Option A** (Pure SVG) for the core geometry generation, then add rasterization as needed.

---

## Plan

### Phase 1: Core Puzzle Geometry

1. [ ] Create `PuzzleConfig` dataclass with parameters:
   - `width`, `height` (mm)
   - `tiles_x`, `tiles_y`
   - `tab_size` (0.1-0.3)
   - `jitter` (0.0-0.13)
   - `corner_radius`
   - `seed`

2. [ ] Port random number generator with seed support (deterministic puzzles)

3. [ ] Implement edge generation:
   - Bézier curve control points for tabs (in/out)
   - Horizontal edges generator
   - Vertical edges generator
   - Border (rounded rectangle) generator

4. [ ] Create `PuzzlePiece` dataclass:
   - `piece_id` (row, col)
   - `edges` (top, right, bottom, left) with Bézier paths
   - `bounds` (x, y, width, height)

5. [ ] Implement `PuzzleGenerator` class:
   - `generate()` → returns list of `PuzzlePiece`
   - `to_svg()` → full puzzle SVG
   - `piece_to_svg(piece_id)` → individual piece SVG

### Phase 2: Text Labels

6. [ ] Add text label config:
   - Font size (auto-scale based on piece size)
   - Label format (e.g., `"{row}-{col}"`, `"A1"`, `"001"`)
   - Position (center, corner)

7. [ ] Implement `add_label_to_piece()`:
   - Render text at piece center
   - Ensure text fits within piece bounds

8. [ ] Add label rendering to SVG export

### Phase 3: ArUco Board Integration

9. [ ] Create `SheetLayout` config:
   - Sheet size (A4, A3, custom)
   - Margins for ArUco markers
   - Pieces per sheet
   - Piece spacing

10. [ ] Implement `PuzzleSheetGenerator`:
    - Takes list of `PuzzlePiece` and `SheetLayout`
    - Arranges pieces on sheets with spacing
    - Integrates with existing `ArucoBoardGenerator`

11. [ ] Generate combined output:
    - SVG with pieces + ArUco markers
    - PDF export for printing (optional)

### Phase 4: Validation & Testing

12. [ ] Create prototype notebook `01_puzzle_generator.ipynb`:
    - Test geometry generation
    - Visualize pieces
    - Verify tab shapes

13. [ ] Create usage notebook `02_usage.ipynb`:
    - End-to-end workflow
    - Generate puzzle → add labels → create sheets

14. [ ] Add unit tests for:
    - Deterministic seed output
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
  - `p2-p6`: Tab shape (3 Bézier segments)
  - `p7-p9`: Exit from tab

## Dependencies

- `svgwrite` or built-in XML (Phase 1-2)
- `cairosvg` for rasterization (optional)
- Existing `snap_fit.aruco` for board generation (Phase 3)

## File Structure

```
src/snap_fit/puzzle/
├── puzzle_generator.py    # Core geometry generation
├── puzzle_config.py       # Config dataclasses
└── puzzle_sheet.py        # Sheet layout with ArUco

scratch_space/puzzle_generator/
├── README.md              # This file
├── 01_puzzle_generator.ipynb
└── 02_usage.ipynb
```
