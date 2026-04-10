# Step 05 - `SlotGrid` Geometry + Label Rendering

> **Status:** done
> **Target file:** `src/snap_fit/aruco/slot_grid.py`
> **Depends on:** Step 04 (SlotGridConfig, MetadataZoneConfig)

---

## Objective

Implement `SlotGrid`, which computes slot geometry within the board interior and
renders human-readable labels (e.g. "A1", "B3") onto a board image. Also provides
`slot_for_centroid()` for mapping detected piece centroids to slot positions at
ingest time.

## Board geometry recap

From the plan (Section 3), for the default `ArucoBoardConfig` (5x7 ring):

```
Board image:        920 x 1320 px
ArUco ring band:    120 px each side (margin 20 + marker 100)
Interior region:    x=120..820, y=120..1220  (700 x 1100 px)
QR strip reserve:   y=1100..1220 (120 px at bottom interior)
Adjusted piece area: x=120..820, y=120..1100  (700 x 980 px)
```

These values must be computed dynamically from `ArucoBoardConfig`, not hardcoded.

## Code stub

```python
import cv2
import numpy as np

from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.metadata_zone_config import SlotGridConfig
from snap_fit.puzzle.puzzle_generator import generate_label


class SlotGrid:
    """Computes slot geometry and renders labels onto a board image."""

    def __init__(self, grid_config: SlotGridConfig, board_config: ArucoBoardConfig) -> None:
        self.grid_config = grid_config
        self.board_config = board_config

        # Compute interior region from board config
        ring_band = board_config.margin + board_config.marker_length
        board_w = ...   # from ArucoBoardGenerator's dimension calculation
        board_h = ...   # same
        self._interior_x0 = ring_band
        self._interior_y0 = ring_band
        self._interior_x1 = board_w - ring_band
        self._interior_y1 = board_h - ring_band

        # Reserve bottom strip for QR codes (120 px = ring_band height)
        self._qr_strip_height = ring_band
        self._piece_area_y1 = self._interior_y1 - self._qr_strip_height

        # Compute slot dimensions
        piece_area_w = self._interior_x1 - self._interior_x0
        piece_area_h = self._piece_area_y1 - self._interior_y0
        self._slot_w = piece_area_w / grid_config.cols
        self._slot_h = piece_area_h / grid_config.rows

    def slot_centers(self) -> list[tuple[int, int]]:
        """Pixel (x, y) of each slot's centre, in row-major label order."""
        centers = []
        for row in range(self.grid_config.rows):
            for col in range(self.grid_config.cols):
                cx = int(self._interior_x0 + (col + 0.5) * self._slot_w)
                cy = int(self._interior_y0 + (row + 0.5) * self._slot_h)
                centers.append((cx, cy))
        return centers

    def label_for_slot(self, col: int, row: int) -> str:
        """Returns label like 'A1', 'B3' via generate_label()."""
        letter_digits = 1 if self.grid_config.cols <= 26 else 2
        number_digits = len(str(self.grid_config.rows))
        return generate_label(col, row, letter_digits, number_digits)

    def render_labels(self, board_img: np.ndarray) -> np.ndarray:
        """Draw slot label text at each slot's top-left corner. Returns modified image."""
        img = board_img.copy()
        inset = self.grid_config.label_inset_px
        for row in range(self.grid_config.rows):
            for col in range(self.grid_config.cols):
                label = self.label_for_slot(col, row)
                x = int(self._interior_x0 + col * self._slot_w) + inset
                y = int(self._interior_y0 + row * self._slot_h) + inset + 12  # baseline offset
                cv2.putText(
                    img, label, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1, cv2.LINE_AA,
                )
        return img

    def slot_for_centroid(self, cx: int, cy: int) -> tuple[int, int] | None:
        """Map a contour centroid to nearest (col, row). None if outside piece area."""
        if not (self._interior_x0 <= cx <= self._interior_x1):
            return None
        if not (self._interior_y0 <= cy <= self._piece_area_y1):
            return None
        col = int((cx - self._interior_x0) / self._slot_w)
        row = int((cy - self._interior_y0) / self._slot_h)
        col = min(col, self.grid_config.cols - 1)
        row = min(row, self.grid_config.rows - 1)
        return (col, row)
```

### Board dimension computation

`ArucoBoardGenerator.generate_image()` computes board dimensions internally. The
`SlotGrid` must replicate that calculation. Options:

1. **Extract to a method on `ArucoBoardConfig`** (clean, no duplication)
2. **Duplicate the formula** (simple but fragile)

Recommended: add `board_dimensions() -> tuple[int, int]` to `ArucoBoardConfig`.

```python
# In ArucoBoardConfig
def board_dimensions(self) -> tuple[int, int]:
    """Compute (width, height) in pixels for the generated board image."""
    w = self.markers_x * (self.marker_length + self.marker_separation) - self.marker_separation + 2 * self.margin
    h = self.markers_y * (self.marker_length + self.marker_separation) - self.marker_separation + 2 * self.margin
    return (w, h)
```

This must match exactly what `generate_image()` computes. Verify by comparing
with the known 920x1320 output for the default config.

## File touchmap

| File | Change |
|------|--------|
| `src/snap_fit/aruco/slot_grid.py` | **NEW** - `SlotGrid` class |
| `src/snap_fit/config/aruco/aruco_board_config.py` | Add `board_dimensions()` method |

## Test strategy

- **Label grid:** Assert `label_for_slot(0,0)=="A1"`, `label_for_slot(7,5)=="H6"`
- **Slot centers:** Assert centers are within the interior region
- **Slot centroid mapping:** Known centroid maps to correct (col, row)
- **Out-of-bounds centroid:** Returns `None`
- **render_labels visual:** Generate image, save, inspect in notebook (Step 4 in plan)
- **Board dimensions:** `ArucoBoardConfig().board_dimensions() == (920, 1320)`
- **Test file:** `tests/aruco/test_slot_grid.py`

## Interactive verification

Update the notebook in `scratch_space/20_piece_markers/00_sample.ipynb` to interactively create a `SlotGrid` instance with the default config, visualize the computed slot centers and rendered labels on a generated board image, and verify the `slot_for_centroid()` mapping with sample points.

## Acceptance criteria

- [x] `SlotGrid` computes correct slot positions for default 8x6 grid
- [x] `label_for_slot()` reuses `generate_label()` from puzzle_generator
- [x] `slot_for_centroid()` correctly maps interior centroids and rejects out-of-bounds
- [x] `render_labels()` produces readable text on a board image
- [x] `board_dimensions()` on `ArucoBoardConfig` matches `generate_image()` output
