"""Assembles a complete printable board image from its components."""

import cv2
import numpy as np

from snap_fit.aruco.aruco_board import ArucoBoardGenerator
from snap_fit.aruco.sheet_metadata import SheetMetadata
from snap_fit.aruco.sheet_metadata import SheetMetadataEncoder
from snap_fit.aruco.slot_grid import SlotGrid
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.metadata_zone_config import MetadataZoneConfig

# BGR color for each named background preset. "white" is handled as an
# identity conversion (see _colorize_background) rather than looked up here.
_PRESET_BGR: dict[str, tuple[int, int, int]] = {
    "white": (255, 255, 255),
    "green": (0, 255, 0),
    "blue": (255, 0, 0),
}


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
        # Colorize to BGR using the configured background preset. All
        # subsequent rendering uses this consistent BGR format.
        img = self._colorize_background(gray)

        if self.metadata_zone is None or not self.metadata_zone.enabled:
            return img

        slot_grid = SlotGrid(self.metadata_zone.slot_grid, self.board_config)
        img = slot_grid.render_labels(img)

        if metadata is not None:
            encoder = SheetMetadataEncoder(self.board_config)
            img = encoder.render(img, metadata, self.metadata_zone)

        return img

    def _colorize_background(self, gray: np.ndarray) -> np.ndarray:
        """Convert the grayscale board render to BGR using the background preset.

        "white" is an identity conversion, reproducing the previous unconditional
        cv2.cvtColor behavior exactly. Other presets scale each BGR channel by
        the grayscale value, so marker ink (0) stays black and background
        pixels (255) reach the exact preset color.

        Args:
            gray: Grayscale board image from ArucoBoardGenerator.

        Returns:
            BGR uint8 numpy array.
        """
        preset = self.board_config.background_preset
        if preset == "white":
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        color = _PRESET_BGR[preset]
        gray_f = gray.astype(np.float32) / 255.0
        colored = np.empty((*gray.shape, 3), dtype=np.float32)
        for channel, value in enumerate(color):
            colored[..., channel] = gray_f * value
        return np.round(colored).astype(np.uint8)
