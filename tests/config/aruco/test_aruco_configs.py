"""Tests for Aruco configurations."""

import cv2

from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig


def test_aruco_board_config_defaults() -> None:
    """Test ArucoBoardConfig default values."""
    config = ArucoBoardConfig()
    assert config.markers_x == 5
    assert config.markers_y == 7
    assert config.marker_length == 100
    assert config.marker_separation == 100
    assert config.dictionary_id == cv2.aruco.DICT_6X6_250
    assert config.margin == 20
    assert config.border_bits == 1


def test_aruco_detector_config_defaults() -> None:
    """Test ArucoDetectorConfig default values."""
    config = ArucoDetectorConfig()
    assert config.adaptive_thresh_win_size_min == 3
    assert config.adaptive_thresh_win_size_max == 23
    assert config.adaptive_thresh_win_size_step == 10
    assert config.rect_margin == 50


def test_aruco_detector_config_to_detector_parameters() -> None:
    """Test conversion to cv2.aruco.DetectorParameters."""
    config = ArucoDetectorConfig(
        adaptive_thresh_win_size_min=5,
        adaptive_thresh_win_size_max=25,
        adaptive_thresh_win_size_step=5,
    )
    params = config.to_detector_parameters()
    assert isinstance(params, cv2.aruco.DetectorParameters)
    assert params.adaptiveThreshWinSizeMin == 5
    assert params.adaptiveThreshWinSizeMax == 25
    assert params.adaptiveThreshWinSizeStep == 5
