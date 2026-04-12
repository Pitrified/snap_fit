# Move slot labels

## Overview

Slot labels are currently rendered in the top left corner of the slot.
We want to move them to the center of the slot.
The computer knows the position of the slot recomputed from config, and we leverage the centroid of the detected piece to assign the slot label to the piece.
The user will place the piece in the slot, covering the slot label, which helps to reduce noise in the image and improve the accuracy of piece detection.

### Plan

Now I have a clear picture. The change is in `render_labels` in slot_grid.py - move label placement from top-left to slot center using `cv2.getTextSize` for proper centering.

- **Before:** labels drawn at `(interior_x0 + col*slot_w + inset, interior_y0 + row*slot_h + inset + 12)` (top-left corner)
- **After:** labels drawn using `cv2.getTextSize` to compute text dimensions, then centered on each slot's pixel centroid `(interior_x0 + (col+0.5)*slot_w, interior_y0 + (row+0.5)*slot_h)`

The `label_inset_px` config field is no longer used by rendering (it's vestigial but harmless to keep).
