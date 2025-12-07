"""Tests for ArucoBoardGenerator."""

import cv2
import numpy as np
import pytest

from snap_fit.aruco.aruco_board import ArucoBoardGenerator
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig


@pytest.fixture
def board_config() -> ArucoBoardConfig:
    """Fixture for ArucoBoardConfig."""
    return ArucoBoardConfig(
        markers_x=3,
        markers_y=3,
        marker_length=10,
        marker_separation=5,
        margin=5,
    )


def test_aruco_board_generator_init(board_config: ArucoBoardConfig) -> None:
    """Test initialization of ArucoBoardGenerator."""
    generator = ArucoBoardGenerator(board_config)
    assert generator.config == board_config
    assert isinstance(generator.dictionary, cv2.aruco.Dictionary)
    assert isinstance(generator.board, cv2.aruco.Board)


def test_create_ring_board_logic(board_config: ArucoBoardConfig) -> None:
    """Test that the ring board logic filters markers correctly."""
    # With 3x3 grid, the center marker (1,1) should be removed.
    # Total markers = 9. Ring markers = 8.
    generator = ArucoBoardGenerator(board_config)

    # Accessing private attributes for testing purposes,
    # or we can inspect the board object.
    # cv2.aruco.Board doesn't easily expose the number of markers directly
    # in python bindings sometimes, but we can check the ids.

    # In OpenCV 4.7+, board.getIds() returns the ids.
    ids = generator.board.getIds()
    assert len(ids) == 8

    # The center id for a 3x3 grid (indices 0-8)
    # Grid:
    # 0 1 2
    # 3 4 5
    # 6 7 8
    # Center is 4.
    # Let's verify if 4 is missing.
    assert 4 not in ids


def test_generate_image(board_config: ArucoBoardConfig) -> None:
    """Test image generation."""
    generator = ArucoBoardGenerator(board_config)
    image = generator.generate_image()

    assert isinstance(image, np.ndarray)
    # Check dimensions
    # Width = 3*10 + 2*5 + 5 = 30 + 10 + 5 = 45
    # Height = 3*10 + 2*5 + 5 = 45

    expected_width = (
        board_config.markers_x * board_config.marker_length
        + (board_config.markers_x - 1) * board_config.marker_separation
        + board_config.margin
    )
    expected_height = (
        board_config.markers_y * board_config.marker_length
        + (board_config.markers_y - 1) * board_config.marker_separation
        + board_config.margin
    )

    assert image.shape[0] == expected_height
    assert image.shape[1] == expected_width
