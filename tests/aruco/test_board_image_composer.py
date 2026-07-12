"""Tests for BoardImageComposer background preset colorization."""

import cv2
import numpy as np
import pytest

from snap_fit.aruco.aruco_board import ArucoBoardGenerator
from snap_fit.aruco.board_image_composer import BoardImageComposer
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig


@pytest.fixture
def board_config() -> ArucoBoardConfig:
    """Small board config for fast tests."""
    return ArucoBoardConfig(
        markers_x=3,
        markers_y=3,
        marker_length=10,
        marker_separation=5,
        margin=5,
    )


def test_white_preset_matches_current_behavior(board_config: ArucoBoardConfig) -> None:
    """Default white preset output is byte-identical to plain grayscale-to-BGR."""
    gray = ArucoBoardGenerator(board_config).generate_image()
    expected = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    result = BoardImageComposer(board_config).compose()

    np.testing.assert_array_equal(result, expected)


def test_green_preset_colors_background_and_keeps_markers_black(
    board_config: ArucoBoardConfig,
) -> None:
    """Green preset paints background pixels green; marker ink stays black."""
    board_config = board_config.model_copy(update={"background_preset": "green"})
    gray = ArucoBoardGenerator(board_config).generate_image()

    result = BoardImageComposer(board_config).compose()

    background_mask = gray == 255
    marker_mask = gray == 0

    assert (result[background_mask] == np.array([0, 255, 0])).all()
    assert (result[marker_mask] == np.array([0, 0, 0])).all()


def test_blue_preset_colors_background_and_keeps_markers_black(
    board_config: ArucoBoardConfig,
) -> None:
    """Blue preset paints background pixels blue; marker ink stays black."""
    board_config = board_config.model_copy(update={"background_preset": "blue"})
    gray = ArucoBoardGenerator(board_config).generate_image()

    result = BoardImageComposer(board_config).compose()

    background_mask = gray == 255
    marker_mask = gray == 0

    assert (result[background_mask] == np.array([255, 0, 0])).all()
    assert (result[marker_mask] == np.array([0, 0, 0])).all()


def test_colorized_output_shape_matches_gray(board_config: ArucoBoardConfig) -> None:
    """Colorized output shape matches the grayscale render, plus channels."""
    board_config = board_config.model_copy(update={"background_preset": "green"})
    gray = ArucoBoardGenerator(board_config).generate_image()

    result = BoardImageComposer(board_config).compose()

    assert result.shape == (*gray.shape, 3)
