"""Tests for ArucoDetector."""

from unittest.mock import MagicMock
from unittest.mock import patch

import cv2
import numpy as np
import pytest

from snap_fit.aruco.aruco_board import ArucoBoardGenerator
from snap_fit.aruco.aruco_detector import ArucoDetector
from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig


@pytest.fixture
def mock_board_generator() -> MagicMock:
    """Fixture for mocked ArucoBoardGenerator."""
    generator = MagicMock(spec=ArucoBoardGenerator)
    generator.dictionary = MagicMock()
    generator.board = MagicMock()
    return generator


@pytest.fixture
def detector_config() -> ArucoDetectorConfig:
    """Fixture for ArucoDetectorConfig."""
    return ArucoDetectorConfig()


def test_aruco_detector_init(
    mock_board_generator: MagicMock, detector_config: ArucoDetectorConfig
) -> None:
    """Test initialization of ArucoDetector."""
    detector = ArucoDetector(mock_board_generator, detector_config)
    assert detector.board_generator == mock_board_generator
    assert detector.config == detector_config
    assert isinstance(detector.detector_params, cv2.aruco.DetectorParameters)


def test_detect_markers(
    mock_board_generator: MagicMock, detector_config: ArucoDetectorConfig
) -> None:
    """Test marker detection."""
    detector = ArucoDetector(mock_board_generator, detector_config)

    # Mock cv2.aruco.ArucoDetector
    with patch("cv2.aruco.ArucoDetector") as mock_aruco_detector:
        mock_instance = mock_aruco_detector.return_value
        expected_corners = (np.array([[0, 0]]),)
        expected_ids = np.array([1])
        expected_rejected = ()
        mock_instance.detectMarkers.return_value = (
            expected_corners,
            expected_ids,
            expected_rejected,
        )

        image = np.zeros((100, 100), dtype=np.uint8)
        corners, ids, rejected = detector.detect_markers(image)

        assert corners == expected_corners
        assert np.array_equal(ids, expected_ids)
        assert rejected == expected_rejected
        mock_instance.detectMarkers.assert_called_once_with(image)


def test_correct_perspective_not_enough_points(
    mock_board_generator: MagicMock, detector_config: ArucoDetectorConfig
) -> None:
    """Test correct_perspective with not enough points."""
    detector = ArucoDetector(mock_board_generator, detector_config)
    image = np.zeros((100, 100), dtype=np.uint8)
    corners = [np.array([[0, 0]])]
    ids = np.array([1])

    # Mock matchImagePoints to return few points
    # It returns objPoints, imgPoints
    mock_board_generator.board.matchImagePoints.return_value = (
        np.array([[0, 0, 0]]),  # Only 1 point
        np.array([[0, 0]]),
    )

    result = detector.correct_perspective(image, corners, ids)
    assert result is None


def test_correct_perspective_success(
    mock_board_generator: MagicMock, detector_config: ArucoDetectorConfig
) -> None:
    """Test correct_perspective success."""
    detector = ArucoDetector(mock_board_generator, detector_config)
    image = np.zeros((100, 100), dtype=np.uint8)
    corners = [np.array([[0, 0]])] * 4
    ids = np.array([1, 2, 3, 4])

    # Mock matchImagePoints
    # 4 points are enough
    obj_points = np.array(
        [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]], dtype=np.float32
    )
    img_points = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float32)

    mock_board_generator.board.matchImagePoints.return_value = (obj_points, img_points)

    # Mock cv2.warpPerspective
    with patch("cv2.warpPerspective") as mock_warp:
        mock_warp.return_value = np.ones((100, 100), dtype=np.uint8)

        result = detector.correct_perspective(image, corners, ids)

        assert result is not None
        assert isinstance(result, np.ndarray)
        mock_warp.assert_called_once()
