"""Aruco board generation utility."""

import cv2
from loguru import logger as lg
import numpy as np

from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig


class ArucoBoardGenerator:
    """Generates a custom ArUco board (Ring Layout)."""

    def __init__(
        self,
        config: ArucoBoardConfig,
    ) -> None:
        """Initialize the ArucoBoardGenerator.

        Args:
            config: The configuration for the board.
        """
        self.config = config
        self.dictionary = cv2.aruco.getPredefinedDictionary(config.dictionary_id)
        self.board = self._create_ring_board()

    def _create_ring_board(self) -> cv2.aruco.Board:
        # 1. Create a temporary GridBoard to get standard coordinates
        temp_board = cv2.aruco.GridBoard(
            size=(self.config.markers_x, self.config.markers_y),
            markerLength=self.config.marker_length,
            markerSeparation=self.config.marker_separation,
            dictionary=self.dictionary,
        )

        # 2. Extract all object points and IDs
        all_obj_points = temp_board.getObjPoints()
        all_ids = temp_board.getIds()

        # 3. Filter for edge markers (Ring)
        ring_obj_points = []
        ring_ids = []

        # Calculate centers to determine grid position
        centers = []
        for pts in all_obj_points:
            center = np.mean(pts, axis=0)
            centers.append(center)

        centers = np.array(centers)
        # Round to avoid float precision issues
        centers_rounded = np.round(centers, decimals=3)

        unique_xs = np.unique(centers_rounded[:, 0])
        unique_ys = np.unique(centers_rounded[:, 1])

        min_x = np.min(unique_xs)
        max_x = np.max(unique_xs)
        min_y = np.min(unique_ys)
        max_y = np.max(unique_ys)

        for i, center in enumerate(centers_rounded):
            cx, cy, _ = center
            # Check if on edge
            if (
                np.isclose(cx, min_x)
                or np.isclose(cx, max_x)
                or np.isclose(cy, min_y)
                or np.isclose(cy, max_y)
            ):
                ring_obj_points.append(all_obj_points[i])
                ring_ids.append(all_ids[i])

        ring_ids = np.array(ring_ids)

        # 4. Create the custom Board
        board = cv2.aruco.Board(ring_obj_points, self.dictionary, ring_ids)

        lg.info(
            f"Created ring board with {len(ring_ids)} markers "
            f"(out of {self.config.markers_x * self.config.markers_y} possible)."
        )
        return board

    def generate_image(self) -> np.ndarray:
        """Generate an image of the board.

        Returns:
            The generated board image.
        """
        min_width = (
            self.config.markers_x * self.config.marker_length
            + (self.config.markers_x - 1) * self.config.marker_separation
            + self.config.margin
        )
        min_height = (
            self.config.markers_y * self.config.marker_length
            + (self.config.markers_y - 1) * self.config.marker_separation
            + self.config.margin
        )

        img_width = int(min_width)
        img_height = int(min_height)

        board_image = self.board.generateImage(
            (img_width, img_height),
            None,
            self.config.margin,
            self.config.border_bits,
        )
        return board_image
