"""Tests for ArucoDetector."""

from unittest.mock import MagicMock
from unittest.mock import patch

import cv2
import numpy as np
import pytest

from snap_fit.aruco.aruco_detector import ArucoDetector
from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig


@pytest.fixture
def detector_config() -> ArucoDetectorConfig:
    """Fixture for ArucoDetectorConfig."""
    return ArucoDetectorConfig()


@patch("snap_fit.aruco.aruco_detector.ArucoBoardGenerator")
def test_aruco_detector_init(
    mock_board_gen_cls: MagicMock, detector_config: ArucoDetectorConfig
) -> None:
    """Test initialization of ArucoDetector."""
    mock_instance = mock_board_gen_cls.return_value
    mock_instance.dictionary = MagicMock()
    mock_instance.board = MagicMock()

    detector = ArucoDetector(detector_config)

    assert detector.config == detector_config
    assert detector.board_generator == mock_instance
    # Ensure it was called with the board config from the detector config
    mock_board_gen_cls.assert_called_once_with(detector_config.board)
    assert isinstance(detector.detector_params, cv2.aruco.DetectorParameters)


@patch("snap_fit.aruco.aruco_detector.ArucoBoardGenerator")
def test_detect_markers(
    mock_board_gen_cls: MagicMock, detector_config: ArucoDetectorConfig
) -> None:
    """Test marker detection."""
    mock_instance = mock_board_gen_cls.return_value
    mock_instance.dictionary = MagicMock()
    # We don't strictly need board for detecting, but init sets it
    mock_instance.board = MagicMock()

    detector = ArucoDetector(detector_config)

    # Mock cv2.aruco.ArucoDetector
    with patch("cv2.aruco.ArucoDetector") as mock_aruco_detector:
        mock_detector_instance = mock_aruco_detector.return_value
        expected_corners = (np.array([[0, 0]]),)
        expected_ids = np.array([1])
        expected_rejected = ()
        mock_detector_instance.detectMarkers.return_value = (
            expected_corners,
            expected_ids,
            expected_rejected,
        )

        image = np.zeros((100, 100), dtype=np.uint8)
        corners, ids, rejected = detector.detect_markers(image)

        assert corners == expected_corners
        assert np.array_equal(ids, expected_ids)
        assert rejected == expected_rejected
        mock_detector_instance.detectMarkers.assert_called_once_with(image)


@patch("snap_fit.aruco.aruco_detector.ArucoBoardGenerator")
def test_correct_perspective_not_enough_points(
    mock_board_gen_cls: MagicMock, detector_config: ArucoDetectorConfig
) -> None:
    """Test correct_perspective with not enough points."""
    mock_instance = mock_board_gen_cls.return_value
    mock_instance.dictionary = MagicMock()
    mock_instance.board = MagicMock()

    detector = ArucoDetector(detector_config)
    image = np.zeros((100, 100), dtype=np.uint8)
    corners = [np.array([[0, 0]])]
    ids = np.array([1])

    # Mock matchImagePoints to return few points
    mock_instance.board.matchImagePoints.return_value = (
        np.array([[0, 0, 0]]),  # Only 1 point
        np.array([[0, 0]]),
    )

    result = detector.correct_perspective(image, corners, ids)
    assert result is None


@patch("snap_fit.aruco.aruco_detector.ArucoBoardGenerator")
def test_correct_perspective_success(
    mock_board_gen_cls: MagicMock, detector_config: ArucoDetectorConfig
) -> None:
    """Test correct_perspective success."""
    mock_instance = mock_board_gen_cls.return_value
    mock_instance.dictionary = MagicMock()
    mock_instance.board = MagicMock()

    detector = ArucoDetector(detector_config)
    image = np.zeros((100, 100), dtype=np.uint8)
    corners = [np.array([[0, 0]])] * 4
    ids = np.array([1, 2, 3, 4])

    # Mock matchImagePoints
    obj_points = np.array(
        [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]], dtype=np.float32
    )
    img_points = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float32)

    mock_instance.board.matchImagePoints.return_value = (obj_points, img_points)

    # Mock cv2.warpPerspective
    with patch("cv2.warpPerspective") as mock_warp:
        mock_warp.return_value = np.ones((100, 100), dtype=np.uint8)

        result = detector.correct_perspective(image, corners, ids)

        assert result is not None
        assert isinstance(result, np.ndarray)
        mock_warp.assert_called_once()
