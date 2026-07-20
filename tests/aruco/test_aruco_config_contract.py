"""Tests for the additive ArUco config contract."""

from pathlib import Path

from pydantic import ValidationError
import pytest

from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.sheet_aruco_config import BackgroundMaskConfig
from snap_fit.config.aruco.sheet_aruco_config import InvalidHsvBoundsError
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
    """Existing sheet configs remain valid with the new fields omitted."""
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
    assert config.preprocess.background_mask is None
    # Preprocess defaults reproduce the historical hardcoded values.
    assert config.preprocess.threshold == 130
    assert config.preprocess.blur_kernel_size == 21


def test_sheet_aruco_config_accepts_nested_background_mask() -> None:
    """The background mask parses nested inside preprocess (Q11)."""
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
          "preprocess": {
            "background_mask": {
              "enabled": true,
              "mode": "flatten_to_white",
              "lower_hsv": [35, 40, 40],
              "upper_hsv": [95, 255, 255]
            }
          }
        }
        """
    )
    mask = config.preprocess.background_mask
    assert isinstance(mask, BackgroundMaskConfig)
    assert mask.enabled is True
    assert mask.mode == "flatten_to_white"
    assert mask.lower_hsv == (35, 40, 40)
    assert mask.upper_hsv == (95, 255, 255)
    assert config.detector.board.background_preset == "green"


def test_background_mask_defaults_mode_as_threshold() -> None:
    """Mode defaults to the threshold-replacement strategy (D13)."""
    mask = BackgroundMaskConfig(enabled=True)
    assert mask.mode == "as_threshold"


def test_background_mask_rejects_out_of_range_hue() -> None:
    """Hue above the OpenCV max (179) is rejected."""
    with pytest.raises(ValidationError) as excinfo:
        BackgroundMaskConfig(upper_hsv=(200, 255, 255))
    assert excinfo.value.errors()[0]["type"] == "value_error"


def test_background_mask_rejects_inverted_bounds() -> None:
    """A lower bound above its matching upper bound is rejected."""
    with pytest.raises(ValidationError):
        BackgroundMaskConfig(lower_hsv=(95, 40, 40), upper_hsv=(35, 255, 255))


def test_invalid_hsv_bounds_is_value_error() -> None:
    """The named exception is a ValueError so pydantic wraps it cleanly."""
    assert issubclass(InvalidHsvBoundsError, ValueError)


def test_existing_sample_sheet_configs_still_validate() -> None:
    """Real sample configs still load after the contract extension."""
    sample_paths = [
        Path("data/demo/demo_SheetArucoConfig.json"),
        Path("data/milano1/milano1_SheetArucoConfig.json"),
        Path("data/oca/oca_SheetArucoConfig.json"),
    ]
    for config_path in sample_paths:
        config = SheetArucoConfig.model_validate_json(config_path.read_text())
        assert config.preprocess.background_mask is None
