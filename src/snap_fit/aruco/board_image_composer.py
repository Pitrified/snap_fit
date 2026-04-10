"""Assembles a complete printable board image from its components."""

import cv2
import numpy as np

from snap_fit.aruco.aruco_board import ArucoBoardGenerator
from snap_fit.aruco.sheet_metadata import SheetMetadata
from snap_fit.aruco.sheet_metadata import SheetMetadataEncoder
from snap_fit.aruco.slot_grid import SlotGrid
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.metadata_zone_config import MetadataZoneConfig


class BoardImageComposer:
    """Assembles a complete board image from its components.

    Components (all optional except the ArUco ring):
      1. ArUco ring  (ArucoBoardGenerator)
      2. Slot grid labels  (SlotGrid)
      3. QR metadata strip  (SheetMetadataEncoder)
      4. Human-readable text line  (SheetMetadataEncoder)

    Existing code that calls ArucoBoardGenerator.generate_image() directly
    is unaffected - this class is an additive layer.
    """

    def __init__(
        self,
        board_config: ArucoBoardConfig,
        metadata_zone: MetadataZoneConfig | None = None,
    ) -> None:
        """Initialise composer.

        Args:
            board_config: ArUco board geometry configuration.
            metadata_zone: Optional QR strip / slot-grid config. When None (or
                when metadata_zone.enabled is False) only the plain ArUco board
                is returned.
        """
        self.board_config = board_config
        self.metadata_zone = metadata_zone

    def compose(self, metadata: SheetMetadata | None = None) -> np.ndarray:
        """Return the complete board image as a BGR numpy array.

        Args:
            metadata: Sheet identity to encode as QR codes. When None the QR
                strip is skipped even if metadata_zone is configured.

        Returns:
            BGR uint8 numpy array with all requested elements composited.
        """
        gray = ArucoBoardGenerator(self.board_config).generate_image()
        # Convert to BGR so all subsequent rendering uses a consistent format.
        img: np.ndarray = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        if self.metadata_zone is None or not self.metadata_zone.enabled:
            return img

        slot_grid = SlotGrid(self.metadata_zone.slot_grid, self.board_config)
        img = slot_grid.render_labels(img)

        if metadata is not None:
            encoder = SheetMetadataEncoder(self.board_config)
            img = encoder.render(img, metadata, self.metadata_zone)

        return img
