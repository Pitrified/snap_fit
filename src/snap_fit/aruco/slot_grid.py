"""Slot grid geometry and label rendering for board images."""

import cv2
import numpy as np

from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.metadata_zone_config import SlotGridConfig
from snap_fit.puzzle.puzzle_generator import generate_label


class SlotGrid:
    """Computes slot geometry and renders labels onto a board image.

    The piece area occupies the board interior minus a bottom strip reserved
    for QR codes and human-readable text. Slot labels are generated via
    generate_label() using column-letter / row-number format (e.g. "A1", "H6").
    """

    def __init__(
        self,
        grid_config: SlotGridConfig,
        board_config: ArucoBoardConfig,
    ) -> None:
        """Initialise SlotGrid from config objects.

        Args:
            grid_config: Slot grid parameters (cols, rows, label_inset_px).
            board_config: ArUco board config used to derive interior dimensions.
        """
        self.grid_config = grid_config
        self.board_config = board_config

        board_w, board_h = board_config.board_dimensions()

        # Marker at col 0 occupies x = margin..margin+marker_length.
        # Last marker col occupies x = (board_w-ring_start)..board_w-margin.
        # Interior = gap between first and last marker columns/rows.
        ring_start = board_config.margin + board_config.marker_length
        self._interior_x0 = ring_start
        self._interior_y0 = ring_start
        self._interior_x1 = board_w - ring_start
        self._interior_y1 = board_h - ring_start

        # Reserve a strip at the bottom of the interior for QR codes / text.
        # Height matches the ring band at the top for visual symmetry.
        qr_strip_h = ring_start
        self._piece_area_y1 = self._interior_y1 - qr_strip_h

        # Slot pixel dimensions (float for accuracy; convert on use).
        piece_w = self._interior_x1 - self._interior_x0
        piece_h = self._piece_area_y1 - self._interior_y0
        self._slot_w = piece_w / grid_config.cols
        self._slot_h = piece_h / grid_config.rows

    # ------------------------------------------------------------------
    # Slot geometry
    # ------------------------------------------------------------------

    def slot_centers(self) -> list[tuple[int, int]]:
        """Return pixel (x, y) of each slot centre, in row-major order."""
        centers: list[tuple[int, int]] = []
        for row in range(self.grid_config.rows):
            for col in range(self.grid_config.cols):
                cx = int(self._interior_x0 + (col + 0.5) * self._slot_w)
                cy = int(self._interior_y0 + (row + 0.5) * self._slot_h)
                centers.append((cx, cy))
        return centers

    def label_for_slot(self, col: int, row: int) -> str:
        """Return the label for slot (col, row), e.g. "A1" or "BC12".

        Uses generate_label() with letter/number digit counts derived from
        the grid dimensions.
        """
        letter_digits = 1 if self.grid_config.cols <= 26 else 2  # noqa: PLR2004
        number_digits = len(str(self.grid_config.rows))
        return generate_label(col, row, letter_digits, number_digits)

    def slot_for_centroid(self, cx: int, cy: int) -> tuple[int, int] | None:
        """Map a contour centroid pixel coordinate to (col, row).

        Returns None when the centroid is outside the piece area.
        """
        if not (self._interior_x0 <= cx < self._interior_x1):
            return None
        if not (self._interior_y0 <= cy < self._piece_area_y1):
            return None
        col = int((cx - self._interior_x0) / self._slot_w)
        row = int((cy - self._interior_y0) / self._slot_h)
        col = min(col, self.grid_config.cols - 1)
        row = min(row, self.grid_config.rows - 1)
        return (col, row)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_labels(self, board_img: np.ndarray) -> np.ndarray:
        """Draw slot label text centred in each slot.

        Args:
            board_img: BGR (or grayscale) board image to annotate.

        Returns:
            A copy of board_img with labels drawn.
        """
        img = board_img.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1

        for row in range(self.grid_config.rows):
            for col in range(self.grid_config.cols):
                label = self.label_for_slot(col, row)
                cx = int(self._interior_x0 + (col + 0.5) * self._slot_w)
                cy = int(self._interior_y0 + (row + 0.5) * self._slot_h)
                (text_w, text_h), _ = cv2.getTextSize(
                    label, font, font_scale, thickness
                )
                x = cx - text_w // 2
                y = cy + text_h // 2
                cv2.putText(
                    img,
                    label,
                    (x, y),
                    font,
                    font_scale,
                    (128, 128, 128),
                    thickness,
                    cv2.LINE_AA,
                )

        return img
