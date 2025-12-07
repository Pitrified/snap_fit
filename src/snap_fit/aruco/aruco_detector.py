"""Aruco detection and perspective correction utility."""

from collections.abc import Sequence

import cv2
from cv2.typing import MatLike
from loguru import logger as lg
import numpy as np

from snap_fit.aruco.aruco_board import ArucoBoardGenerator
from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig


class ArucoDetector:
    """Detects ArUco markers and corrects perspective."""

    def __init__(
        self,
        board_generator: ArucoBoardGenerator,
        config: ArucoDetectorConfig,
    ) -> None:
        """Initialize the ArucoDetector.

        Args:
            board_generator: The board generator instance used to create the board.
            config: Detector configuration.
        """
        self.board_generator = board_generator
        self.dictionary = board_generator.dictionary
        self.board = board_generator.board
        self.config = config
        self.detector_params = config.to_detector_parameters()

    def detect_markers(
        self, image: np.ndarray
    ) -> tuple[Sequence[MatLike], MatLike, Sequence[MatLike]]:
        """Detect markers in the image.

        Args:
            image: The input image.

        Returns:
            A tuple containing (corners, ids, rejected).
        """
        detector = cv2.aruco.ArucoDetector(self.dictionary, self.detector_params)
        corners, ids, rejected = detector.detectMarkers(image)
        lg.debug("Used ArucoDetector class.")

        if ids is not None:
            lg.info(f"Detected {len(ids)} markers.")
        else:
            lg.warning("No markers detected.")

        return corners, ids, rejected

    def correct_perspective(
        self,
        image: np.ndarray,
        corners: tuple,
        ids: np.ndarray,
    ) -> np.ndarray | None:
        """Correct the perspective of the image based on detected markers.

        Args:
            image: The input image.
            corners: Detected marker corners.
            ids: Detected marker IDs.

        Returns:
            The rectified image, or None if correction failed.
        """
        if ids is None or len(ids) == 0:
            lg.warning("No markers provided for rectification.")
            return None

        # Match image points
        obj_points, img_points = self.board.matchImagePoints(corners, ids)

        min_obj_points = 4
        if obj_points is None or len(obj_points) < min_obj_points:
            lg.warning("Not enough points to rectify image.")
            return None

        # 1. Prepare Source Points (from image)
        src_points = img_points.reshape(-1, 2)

        # 2. Prepare Destination Points (from board definition)
        object_points_2d = obj_points.reshape(-1, 3)[:, :2]  # Drop Z

        # Calculate bounds to determine output image size and offsets
        min_x = np.min(object_points_2d[:, 0])
        max_x = np.max(object_points_2d[:, 0])
        min_y = np.min(object_points_2d[:, 1])
        max_y = np.max(object_points_2d[:, 1])

        board_width = max_x - min_x
        board_height = max_y - min_y

        # Destination points in the output image
        dst_points = np.zeros_like(object_points_2d)
        dst_points[:, 0] = object_points_2d[:, 0] - min_x + self.config.rect_margin
        dst_points[:, 1] = object_points_2d[:, 1] - min_y + self.config.rect_margin

        # Output image size
        out_width = int(board_width + 2 * self.config.rect_margin)
        out_height = int(board_height + 2 * self.config.rect_margin)

        # 3. Compute Homography
        h, _ = cv2.findHomography(src_points, dst_points)

        # 4. Warp Perspective
        rectified_image = cv2.warpPerspective(
            image,
            h,
            (out_width, out_height),
            borderValue=(0, 255, 0),
        )

        lg.info(f"Image rectified to size {out_width}x{out_height}")
        return rectified_image
