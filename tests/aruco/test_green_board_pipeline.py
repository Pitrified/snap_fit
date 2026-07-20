"""Green-board detection and synthetic ingest tests (phase 5, G6/D15/D17).

These validate the green path on a rendered board without needing real photos:
detection must still rectify a green board, and a green board with composited
pieces must ingest and extract them under both mask modes. Real
printed-and-photographed captures are validated separately once available.
"""

from pathlib import Path
from typing import Literal

import cv2
import numpy as np
import pytest

from snap_fit.aruco.aruco_detector import ArucoDetector
from snap_fit.aruco.board_config_resolver import derive_background_mask
from snap_fit.aruco.board_image_composer import BoardImageComposer
from snap_fit.aruco.sheet_metadata import SheetMetadata
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig
from snap_fit.config.aruco.metadata_zone_config import MetadataZoneConfig
from snap_fit.config.aruco.metadata_zone_config import SlotGridConfig
from snap_fit.config.aruco.sheet_aruco_config import BackgroundMaskConfig
from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig
from snap_fit.config.aruco.sheet_aruco_config import SheetPreprocessConfig
from snap_fit.puzzle.sheet_aruco import SheetAruco

# Inner-workspace blob centers as (x, y) fractions of the board size.
_BLOB_CENTERS = ((0.40, 0.40), (0.60, 0.45), (0.45, 0.60))
_BLOB_RADIUS = 55
_RED_BGR = (0, 0, 255)


def _metadata_zone() -> MetadataZoneConfig:
    return MetadataZoneConfig(
        enabled=True,
        qr_n_codes=3,
        qr_ecc="M",
        text_enabled=True,
        slot_grid=SlotGridConfig(cols=4, rows=3),
    )


def _compose_board(preset: Literal["white", "green", "blue"]) -> np.ndarray:
    """Render a full board (ring + slot labels + QR) for the given preset."""
    board_config = ArucoBoardConfig(background_preset=preset)
    composer = BoardImageComposer(board_config, _metadata_zone())
    meta = SheetMetadata(
        tag_name="synthetic",
        sheet_index=0,
        total_sheets=1,
        board_config_id="synthetic",
    )
    return composer.compose(meta)


def _stamp_blobs(img: np.ndarray) -> np.ndarray:
    """Composite red blobs onto the inner workspace to stand in for pieces."""
    out = img.copy()
    h, w = out.shape[:2]
    for fx, fy in _BLOB_CENTERS:
        cv2.circle(out, (int(w * fx), int(h * fy)), _BLOB_RADIUS, _RED_BGR, -1)
    return out


@pytest.mark.parametrize("preset", ["white", "green"])
def test_detector_rectifies_board(preset: Literal["white", "green"]) -> None:
    """The detector rectifies both a white and a green rendered board (G6)."""
    img = _compose_board(preset)
    detector = ArucoDetector(ArucoDetectorConfig(board=ArucoBoardConfig()))
    rectified = detector.rectify(img)
    assert rectified is not None
    assert rectified.ndim == 3


@pytest.mark.parametrize("mode", ["as_threshold", "flatten_to_white"])
def test_synthetic_green_ingest_extracts_pieces(
    mode: Literal["as_threshold", "flatten_to_white"],
    tmp_path: Path,
) -> None:
    """A green board with composited pieces ingests under both mask modes."""
    board_config = ArucoBoardConfig(background_preset="green")
    img = _stamp_blobs(_compose_board("green"))
    photo_fp = tmp_path / "green_sheet.png"
    cv2.imwrite(str(photo_fp), img)

    config = SheetArucoConfig(
        min_area=8_000,
        detector=ArucoDetectorConfig(board=board_config),
        metadata_zone=_metadata_zone(),
        preprocess=SheetPreprocessConfig(
            background_mask=BackgroundMaskConfig(enabled=True, mode=mode)
        ),
    )
    sheet = SheetAruco(config).load_sheet(photo_fp)

    assert sheet.metadata is not None
    assert sheet.metadata.board_config_id == "synthetic"
    assert len(sheet.pieces) == len(_BLOB_CENTERS)


def test_synthetic_green_ingest_uses_derived_mask(tmp_path: Path) -> None:
    """The derived (auto-enabled) mask extracts pieces without an explicit mode."""
    board_config = ArucoBoardConfig(background_preset="green")
    img = _stamp_blobs(_compose_board("green"))
    photo_fp = tmp_path / "green_sheet.png"
    cv2.imwrite(str(photo_fp), img)

    config = derive_background_mask(
        SheetArucoConfig(
            min_area=8_000,
            detector=ArucoDetectorConfig(board=board_config),
            metadata_zone=_metadata_zone(),
        )
    )
    assert config.preprocess.background_mask is not None
    sheet = SheetAruco(config).load_sheet(photo_fp)
    assert len(sheet.pieces) == len(_BLOB_CENTERS)
