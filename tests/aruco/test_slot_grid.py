"""Tests for SlotGrid geometry and label rendering."""

import numpy as np
import pytest

from snap_fit.aruco.slot_grid import SlotGrid
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.metadata_zone_config import SlotGridConfig


@pytest.fixture
def default_board_config() -> ArucoBoardConfig:
    """Return default ArucoBoardConfig (5x7 ring, 940x1340 px)."""
    return ArucoBoardConfig()


@pytest.fixture
def default_grid_config() -> SlotGridConfig:
    """Return standard 8-column by 6-row slot grid config."""
    return SlotGridConfig(cols=8, rows=6)


@pytest.fixture
def slot_grid(
    default_grid_config: SlotGridConfig,
    default_board_config: ArucoBoardConfig,
) -> SlotGrid:
    """Return SlotGrid built from default configs."""
    return SlotGrid(default_grid_config, default_board_config)


# ------------------------------------------------------------------
# board_dimensions
# ------------------------------------------------------------------


def test_board_dimensions_default() -> None:
    """Default ArucoBoardConfig produces 940x1340."""
    cfg = ArucoBoardConfig()
    assert cfg.board_dimensions() == (940, 1340)


def test_board_dimensions_custom() -> None:
    """Custom config dimensions match the formula."""
    cfg = ArucoBoardConfig(
        markers_x=3,
        markers_y=4,
        marker_length=50,
        marker_separation=50,
        margin=10,
    )
    w = 3 * 50 + 2 * 50 + 2 * 10
    h = 4 * 50 + 3 * 50 + 2 * 10
    assert cfg.board_dimensions() == (w, h)


# ------------------------------------------------------------------
# Interior region
# ------------------------------------------------------------------


def test_interior_bounds_default(slot_grid: SlotGrid) -> None:
    """Interior region for default config is x=120..820, y=120..1220."""
    assert slot_grid._interior_x0 == 120
    assert slot_grid._interior_x1 == 820
    assert slot_grid._interior_y0 == 120
    assert slot_grid._interior_y1 == 1220


def test_piece_area_y1_default(slot_grid: SlotGrid) -> None:
    """Piece area bottom = interior_y1 - ring_start = 1220 - 120 = 1100."""
    assert slot_grid._piece_area_y1 == 1100


# ------------------------------------------------------------------
# label_for_slot
# ------------------------------------------------------------------


def test_label_top_left(slot_grid: SlotGrid) -> None:
    """First slot (0, 0) gets label A1."""
    assert slot_grid.label_for_slot(0, 0) == "A1"


def test_label_bottom_right_8x6(slot_grid: SlotGrid) -> None:
    """Last slot of 8x6 grid gets label H6."""
    assert slot_grid.label_for_slot(7, 5) == "H6"


def test_label_middle(slot_grid: SlotGrid) -> None:
    """Middle slot (2, 3) gets label C4."""
    assert slot_grid.label_for_slot(2, 3) == "C4"


def test_label_two_letter_digits() -> None:
    """Grids with more than 26 cols use two letter digits."""
    cfg = SlotGridConfig(cols=27, rows=1)
    grid = SlotGrid(cfg, ArucoBoardConfig())
    # col=26 in base-26 with 2 digits: low digit A (0), high digit B (1) -> "BA1"
    assert grid.label_for_slot(26, 0) == "BA1"


# ------------------------------------------------------------------
# slot_centers
# ------------------------------------------------------------------


def test_slot_centers_count(slot_grid: SlotGrid) -> None:
    """One centre per slot: cols * rows total."""
    centers = slot_grid.slot_centers()
    assert len(centers) == 8 * 6


def test_slot_centers_within_piece_area(slot_grid: SlotGrid) -> None:
    """All slot centres lie within the piece area bounds."""
    for cx, cy in slot_grid.slot_centers():
        assert slot_grid._interior_x0 <= cx < slot_grid._interior_x1
        assert slot_grid._interior_y0 <= cy < slot_grid._piece_area_y1


def test_slot_centers_order(slot_grid: SlotGrid) -> None:
    """Row-major order: first 8 centers belong to row 0."""
    centers = slot_grid.slot_centers()
    # All first-row centers have smaller y than first second-row center
    row0_ys = [cy for _, cy in centers[:8]]
    row1_ys = [cy for _, cy in centers[8:16]]
    assert max(row0_ys) < min(row1_ys)


# ------------------------------------------------------------------
# slot_for_centroid
# ------------------------------------------------------------------


def test_slot_for_centroid_top_left(slot_grid: SlotGrid) -> None:
    """Centroid near top-left of interior maps to (0, 0)."""
    cx = slot_grid._interior_x0 + 5
    cy = slot_grid._interior_y0 + 5
    assert slot_grid.slot_for_centroid(cx, cy) == (0, 0)


def test_slot_for_centroid_bottom_right(slot_grid: SlotGrid) -> None:
    """Centroid just inside bottom-right of piece area maps to last slot."""
    cx = slot_grid._interior_x1 - 1
    cy = slot_grid._piece_area_y1 - 1
    col, row = slot_grid.slot_for_centroid(cx, cy)  # type: ignore[misc]
    assert col == slot_grid.grid_config.cols - 1
    assert row == slot_grid.grid_config.rows - 1


def test_slot_for_centroid_at_center(slot_grid: SlotGrid) -> None:
    """Slot centres computed by slot_centers() map back to their own slot."""
    centers = slot_grid.slot_centers()
    for idx, (cx, cy) in enumerate(centers):
        expected_col = idx % slot_grid.grid_config.cols
        expected_row = idx // slot_grid.grid_config.cols
        result = slot_grid.slot_for_centroid(cx, cy)
        assert result == (expected_col, expected_row), (
            f"Center {idx} ({cx},{cy}) -> {result}, "
            f"expected ({expected_col},{expected_row})"
        )


def test_slot_for_centroid_outside_x_left(slot_grid: SlotGrid) -> None:
    """Centroid left of interior returns None."""
    assert slot_grid.slot_for_centroid(slot_grid._interior_x0 - 1, 500) is None


def test_slot_for_centroid_outside_x_right(slot_grid: SlotGrid) -> None:
    """Centroid at interior right edge returns None."""
    assert slot_grid.slot_for_centroid(slot_grid._interior_x1, 500) is None


def test_slot_for_centroid_outside_y_top(slot_grid: SlotGrid) -> None:
    """Centroid above interior returns None."""
    assert slot_grid.slot_for_centroid(500, slot_grid._interior_y0 - 1) is None


def test_slot_for_centroid_in_qr_strip(slot_grid: SlotGrid) -> None:
    """Centroids in the QR strip (below piece area) are rejected."""
    cx = slot_grid._interior_x0 + 50
    cy = slot_grid._piece_area_y1 + 5
    assert slot_grid.slot_for_centroid(cx, cy) is None


# ------------------------------------------------------------------
# render_labels
# ------------------------------------------------------------------


def test_render_labels_returns_copy(slot_grid: SlotGrid) -> None:
    """render_labels returns a new array, not a view of the input."""
    board = np.ones((1340, 940, 3), dtype=np.uint8) * 255
    result = slot_grid.render_labels(board)
    assert result is not board


def test_render_labels_modifies_image(slot_grid: SlotGrid) -> None:
    """render_labels draws text that changes at least some pixels."""
    board = np.ones((1340, 940, 3), dtype=np.uint8) * 255
    result = slot_grid.render_labels(board)
    assert not np.array_equal(result, board)


def test_render_labels_shape_preserved(slot_grid: SlotGrid) -> None:
    """render_labels preserves the input image shape."""
    board = np.ones((1340, 940, 3), dtype=np.uint8) * 255
    result = slot_grid.render_labels(board)
    assert result.shape == board.shape
