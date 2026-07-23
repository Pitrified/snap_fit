"""Tests for SheetAruco crop geometry.

The cropped sheet must end up equal to the board's piece area: the ring interior
minus the QR strip. These tests pin the arithmetic that gets there, because a
20 px per side overshoot previously survived unnoticed (it cropped into the
piece area and truncated contours of pieces placed near the slot grid edge).
"""

from pathlib import Path

import cv2
import numpy as np
import pytest

from snap_fit.aruco.slot_grid import SlotGrid
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig
from snap_fit.config.aruco.metadata_zone_config import MetadataZoneConfig
from snap_fit.config.aruco.metadata_zone_config import SlotGridConfig
from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig
from snap_fit.puzzle.sheet_aruco import SheetAruco


def _board() -> ArucoBoardConfig:
    """Return the greendemo_small board geometry (560x700, ring_start 120)."""
    return ArucoBoardConfig(
        markers_x=4,
        markers_y=5,
        marker_length=100,
        marker_separation=40,
        margin=20,
    )


def _config(board: ArucoBoardConfig | None = None) -> SheetArucoConfig:
    """Return a SheetArucoConfig with a metadata zone (so the QR strip is cut)."""
    board = board or _board()
    return SheetArucoConfig(
        detector=ArucoDetectorConfig(rect_margin=50, board=board),
        metadata_zone=MetadataZoneConfig(slot_grid=SlotGridConfig(cols=2, rows=2)),
    )


# ------------------------------------------------------------------
# crop_margin / crop_offset
# ------------------------------------------------------------------


def test_crop_margin_stops_at_the_ring_inner_edge() -> None:
    """The computed crop lands exactly on the ring's inner edge.

    Object coordinates start at the first marker's outer corner and exclude the
    board margin, so the ring's inner edge in rectified space is at
    rect_margin + marker_length. Including board.margin here would overshoot.
    """
    sheet_aruco = SheetAruco(_config())
    assert sheet_aruco.crop_margin == 100 + 50


def test_crop_offset_is_the_ring_start() -> None:
    """crop_offset maps cropped (0, 0) onto the ring interior origin."""
    board = _board()
    sheet_aruco = SheetAruco(_config(board))
    ring_start = board.margin + board.marker_length
    assert sheet_aruco.crop_offset == ring_start


def test_crop_offset_agrees_with_slot_grid_interior() -> None:
    """crop_offset equals the interior origin SlotGrid computes independently."""
    board = _board()
    sheet_aruco = SheetAruco(_config(board))
    grid = SlotGrid(SlotGridConfig(cols=2, rows=2), board)
    assert sheet_aruco.crop_offset == grid._interior_x0
    assert sheet_aruco.crop_offset == grid._interior_y0


def test_explicit_crop_margin_keeps_the_offset_consistent() -> None:
    """An explicit crop_margin still yields a matching crop_offset.

    The offset formula is general, not a constant, so overriding the margin must
    shift the offset by the same amount.
    """
    board = _board()
    default = SheetAruco(_config(board))
    override = SheetAruco(
        SheetArucoConfig(
            crop_margin=default.crop_margin + 30,
            detector=ArucoDetectorConfig(rect_margin=50, board=board),
        )
    )
    assert override.crop_offset == default.crop_offset + 30


# ------------------------------------------------------------------
# end-to-end cropping through load_sheet
# ------------------------------------------------------------------


@pytest.fixture
def photo_path(tmp_path: Path) -> Path:
    """Write a tiny placeholder image; rectification is stubbed out."""
    fp = tmp_path / "sheet.jpg"
    cv2.imwrite(str(fp), np.zeros((40, 30, 3), dtype=np.uint8))
    return fp


def test_cropped_sheet_equals_the_piece_area(
    photo_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """load_sheet yields exactly the piece area: ring interior minus QR strip.

    Rectification is stubbed with a synthetic image of the size
    correct_perspective would produce, so this exercises the real cropping path
    without needing a photographed board.
    """
    board = _board()
    config = _config(board)
    sheet_aruco = SheetAruco(config)

    # correct_perspective sizes its output from the object points, which span
    # the board minus its margin on each side, plus rect_margin all round.
    board_w, board_h = board.board_dimensions()
    rect_margin = config.detector.rect_margin
    out_w = board_w - 2 * board.margin + 2 * rect_margin
    out_h = board_h - 2 * board.margin + 2 * rect_margin
    rectified = np.full((out_h, out_w, 3), 255, dtype=np.uint8)

    monkeypatch.setattr(sheet_aruco.aruco_detector, "rectify", lambda _img: rectified)

    sheet = sheet_aruco.load_sheet(photo_path)

    grid = SlotGrid(config.metadata_zone.slot_grid, board)  # type: ignore[union-attr]
    expected_w = grid._interior_x1 - grid._interior_x0
    expected_h = grid._piece_area_y1 - grid._interior_y0

    assert sheet.img_orig.shape[:2] == (expected_h, expected_w)
    assert sheet.crop_offset == grid._interior_x0


def test_cropped_sheet_matches_piece_area_on_the_default_board(
    photo_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same invariant holds for the 5x7 default board, not just 4x5."""
    board = ArucoBoardConfig()
    config = _config(board)
    sheet_aruco = SheetAruco(config)

    board_w, board_h = board.board_dimensions()
    rect_margin = config.detector.rect_margin
    rectified = np.full(
        (
            board_h - 2 * board.margin + 2 * rect_margin,
            board_w - 2 * board.margin + 2 * rect_margin,
            3,
        ),
        255,
        dtype=np.uint8,
    )
    monkeypatch.setattr(sheet_aruco.aruco_detector, "rectify", lambda _img: rectified)

    sheet = sheet_aruco.load_sheet(photo_path)

    grid = SlotGrid(config.metadata_zone.slot_grid, board)  # type: ignore[union-attr]
    assert sheet.img_orig.shape[:2] == (
        grid._piece_area_y1 - grid._interior_y0,
        grid._interior_x1 - grid._interior_x0,
    )
