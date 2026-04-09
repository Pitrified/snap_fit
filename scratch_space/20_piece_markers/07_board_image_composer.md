# Step 07 - `BoardImageComposer` Full Assembly

> **Status:** not started
> **Target file:** `src/snap_fit/aruco/board_image_composer.py`
> **Depends on:** Steps 05, 06

---

## Objective

Create a single entry point that assembles a complete printable board image from
its components: ArUco ring, slot grid labels, QR metadata strip, and human text.
Replaces ad-hoc use of `ArucoBoardGenerator.generate_image()` in notebooks.

## Code stub

```python
import numpy as np

from snap_fit.aruco.aruco_board import ArucoBoardGenerator
from snap_fit.aruco.sheet_metadata import SheetMetadata, SheetMetadataEncoder
from snap_fit.aruco.slot_grid import SlotGrid
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.metadata_zone_config import MetadataZoneConfig


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
    ) -> None:
        self.board_config = board_config
        self.metadata_zone = metadata_zone

    def compose(self, metadata: SheetMetadata | None = None) -> np.ndarray:
        """Return the complete board image as a numpy array."""
        img = ArucoBoardGenerator(self.board_config).generate_image()

        if self.metadata_zone and self.metadata_zone.enabled:
            # Render slot grid labels
            slot_grid = SlotGrid(self.metadata_zone.slot_grid, self.board_config)
            img = slot_grid.render_labels(img)

            # Render QR strip + text (only if metadata provided)
            if metadata:
                encoder = SheetMetadataEncoder()
                img = encoder.render(img, metadata, self.metadata_zone)

        return img
```

## Usage example

```python
from datetime import date

from snap_fit.aruco.board_image_composer import BoardImageComposer
from snap_fit.aruco.sheet_metadata import SheetMetadata
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.metadata_zone_config import MetadataZoneConfig

board_config = ArucoBoardConfig()
metadata_zone = MetadataZoneConfig()
metadata = SheetMetadata(
    tag_name="oca",
    sheet_index=1,
    total_sheets=6,
    board_config_id="oca",
    printed_at=date(2025, 1, 15),
)

composer = BoardImageComposer(board_config, metadata_zone)
board_img = composer.compose(metadata)

# Save to file
import cv2
cv2.imwrite("board_sheet_02.png", board_img)
```

## Backward compatibility

`BoardImageComposer` does not modify `ArucoBoardGenerator`. Existing code that
calls `ArucoBoardGenerator.generate_image()` directly continues to work. The
composer is an additive layer.

## File touchmap

| File | Change |
|------|--------|
| `src/snap_fit/aruco/board_image_composer.py` | **NEW** - `BoardImageComposer` class |

## Test strategy

- **Base image:** `compose(metadata=None)` with no `metadata_zone` returns the plain ArUco board
- **With slot grid only:** `compose(metadata=None)` with `metadata_zone` enabled renders labels
- **Full compose:** `compose(metadata)` produces image with QR + labels + text
- **Decode round-trip:** Compose a board, run `SheetMetadataDecoder.decode()`, assert recovered metadata
- **Image dimensions:** Output matches `ArucoBoardConfig.board_dimensions()`
- **Test file:** `tests/aruco/test_board_image_composer.py`

## Acceptance criteria

- [ ] `compose()` without metadata produces a valid ArUco board with labels
- [ ] `compose()` with metadata adds QR codes and text
- [ ] Full round-trip: compose -> decode -> recovered SheetMetadata matches input
- [ ] Output image dimensions match board config
- [ ] No modifications to existing `ArucoBoardGenerator`
