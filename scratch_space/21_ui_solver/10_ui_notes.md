# UI Notes - Feature Index

This document tracks six UI improvement features for the snap_fit solver and piece detail pages. Each feature has a detailed sub-plan with implementation steps, files to touch, and acceptance criteria.

## Sub-plans

| # | Feature | Plan | Status | Complexity |
|---|---------|------|--------|------------|
| 11 | Placed piece labels | [11_placed_piece_labels.md](11_placed_piece_labels.md) | done | low |
| 12 | Orientation of suggested pieces | [12_orientation_display.md](12_orientation_display.md) | done | low |
| 13 | Side-by-side matching preview | [13_matching_preview.md](13_matching_preview.md) | not started | high |
| 14 | Rotated label on piece image | [14_rotated_piece_label.md](14_rotated_piece_label.md) | done | medium |
| 15 | Piece inspection overlay | [15_piece_inspection.md](15_piece_inspection.md) | done | medium |
| 16 | Piece segment edit | [16_piece_edit.md](16_piece_edit.md) | not started | medium |
| 17 | Overlay discoveries (prep for 13) | [17_overlay_discoveries.md](17_overlay_discoveries.md) | done | - |

## Recommended order

1. **11 - Placed piece labels** (low effort, standalone, improves readability immediately)
2. **12 - Orientation display** (low effort, standalone, improves suggestion UX)
3. **14 - Rotated label on piece** (depends on 11 for label data pipeline)
4. **15 - Piece inspection overlay** (independent, medium effort, useful for debugging detection)
5. **16 - Piece segment edit** (independent, medium effort, enables manual correction)
6. **13 - Matching preview** (highest complexity, depends on 12 for orientation context, benefits from 15 for overlay experience)

## Original notes

### label of placed pieces

when a piece is placed on the grid, we show a small label with the piece ID to help track placements

### orientation of suggested pieces

when showing a suggested piece, we need to show it in the correct orientation. Leverage existing rotation functionality. Show that orientation also as text for clarity (e.g. "Place piece #5 rotated 90 degrees clockwise")

### side by side matching preview

when proposing a match, we want to also preview the rotated/translated/reshaped piece image
existing piece on grid is static, new piece image is rotated/translated/reshaped according to the proposed placement.
the ends of the two matching segments in the contour can be matched (some code in some random notebook does this)
overlap the two piece images with some transparency to show how they fit together
also show the label/description of the piece we are matching against, not just of the piece we are placing

### rotated label on the piece

to help keep track of the labels, we can also show the piece ID label directly on the piece image, rotated according to the piece orientation

### piece inspection

in the piece detail page, overlay the detected contour segments and corner points on top of the piece image

### piece edit

in the piece detail page, add options to change the detected in/out/edge segment labels
