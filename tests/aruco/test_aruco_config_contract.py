"""Tests for the additive ArUco config contract."""

from pathlib import Path

from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.sheet_aruco_config import BackgroundMaskConfig
from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig


def test_aruco_board_config_defaults_to_white() -> None:
    """The new background preset defaults to the current white behavior."""
    config = ArucoBoardConfig()
    assert config.background_preset == "white"


def test_aruco_board_config_accepts_named_preset() -> None:
    """ArucoBoardConfig accepts additive preset values from JSON."""
    config = ArucoBoardConfig.model_validate_json(
        """
        {
          "background_preset": "green"
        }
        """
    )
    assert config.background_preset == "green"


def test_sheet_aruco_config_defaults_without_background_mask() -> None:
    """Existing sheet configs remain valid with the new field omitted."""
    config = SheetArucoConfig.model_validate_json(
        """
        {
          "min_area": 80000,
          "crop_margin": null,
          "detector": {
            "adaptive_thresh_win_size_min": 3,
            "adaptive_thresh_win_size_max": 23,
            "adaptive_thresh_win_size_step": 10,
            "rect_margin": 50,
            "board": {
              "markers_x": 5,
              "markers_y": 7,
              "marker_length": 100,
              "marker_separation": 100,
              "dictionary_id": 10,
              "margin": 20,
              "border_bits": 1
            }
          }
        }
        """
    )
    assert config.background_mask is None


def test_sheet_aruco_config_accepts_background_mask() -> None:
    """The background mask parses as an additive nested config."""
    config = SheetArucoConfig.model_validate_json(
        """
        {
          "min_area": 80000,
          "crop_margin": null,
          "detector": {
            "adaptive_thresh_win_size_min": 3,
            "adaptive_thresh_win_size_max": 23,
            "adaptive_thresh_win_size_step": 10,
            "rect_margin": 50,
            "board": {
              "markers_x": 5,
              "markers_y": 7,
              "marker_length": 100,
              "marker_separation": 100,
              "dictionary_id": 10,
              "margin": 20,
              "border_bits": 1,
              "background_preset": "green"
            }
          },
          "background_mask": {
            "enabled": true,
            "lower_hsv": [35, 40, 40],
            "upper_hsv": [95, 255, 255]
          }
        }
        """
    )
    assert isinstance(config.background_mask, BackgroundMaskConfig)
    assert config.background_mask.enabled is True
    assert config.background_mask.lower_hsv == (35, 40, 40)
    assert config.background_mask.upper_hsv == (95, 255, 255)
    assert config.detector.board.background_preset == "green"


def test_existing_sample_sheet_configs_still_validate() -> None:
    """Real sample configs still load after the contract extension."""
    sample_paths = [
        Path("data/demo/demo_SheetArucoConfig.json"),
        Path("data/milano1/milano1_SheetArucoConfig.json"),
        Path("data/oca/oca_SheetArucoConfig.json"),
    ]
    for config_path in sample_paths:
        config = SheetArucoConfig.model_validate_json(config_path.read_text())
        assert config.background_mask is None
