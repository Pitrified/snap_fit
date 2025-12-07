"""Aruco board generation utility."""

import cv2
from loguru import logger as lg
import numpy as np


class ArucoBoardGenerator:
    """Generates a custom ArUco board (Ring Layout)."""

    def __init__(
        self,
        markers_x: int = 5,
        markers_y: int = 7,
        marker_length: int = 100,
        marker_separation: int = 100,
        dictionary_id: int = cv2.aruco.DICT_6X6_250,
    ) -> None:
        """Initialize the ArucoBoardGenerator.

        Args:
            markers_x: Number of markers in X direction.
            markers_y: Number of markers in Y direction.
            marker_length: Length of the marker side in pixels (or arbitrary units).
            marker_separation: Separation between markers in pixels.
            dictionary_id: ArUco dictionary ID.
        """
        self.markers_x = markers_x
        self.markers_y = markers_y
        self.marker_length = marker_length
        self.marker_separation = marker_separation
        self.dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)
        self.board = self._create_ring_board()

    def _create_ring_board(self) -> cv2.aruco.Board:
        # 1. Create a temporary GridBoard to get standard coordinates
        temp_board = cv2.aruco.GridBoard(
            size=(self.markers_x, self.markers_y),
            markerLength=self.marker_length,
            markerSeparation=self.marker_separation,
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
            f"(out of {self.markers_x * self.markers_y} possible)."
        )
        return board

    def generate_image(self, margin: int = 20, border_bits: int = 1) -> np.ndarray:
        """Generate an image of the board.

        Args:
            margin: Margin around the board in pixels.
            border_bits: Number of bits for the marker border.

        Returns:
            The generated board image.
        """
        min_width = (
            self.markers_x * self.marker_length
            + (self.markers_x - 1) * self.marker_separation
            + margin
        )
        min_height = (
            self.markers_y * self.marker_length
            + (self.markers_y - 1) * self.marker_separation
            + margin
        )

        img_width = int(min_width)
        img_height = int(min_height)

        board_image = self.board.generateImage(
            (img_width, img_height),
            None,
            margin,
            border_bits,
        )
        return board_image
