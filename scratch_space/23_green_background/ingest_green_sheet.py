"""Ingest a photo of a green board using the phase-4 resolution flow (phase 5).

Demonstrates the driver-side ingest the notebooks will use once real photos
exist: decode the QR to get ``board_config_id``, resolve the stored
``SheetArucoConfig`` from disk with ``load_sheet_config_by_id`` (mask already
enabled), then run ``SheetAruco.load_sheet``. No config is built by hand (D14).

With no argument it ingests a generated ``greendemo`` board PNG as a stand-in
(no physical pieces, so zero pieces but the metadata and mask are exercised).
Pass a photo path to ingest a real capture once printed and photographed:

    python scratch_space/23_green_background/ingest_green_sheet.py path/to/photo.jpg
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger as lg

from snap_fit.aruco.board_config_resolver import BoardConfigNotFoundError
from snap_fit.aruco.board_config_resolver import load_sheet_config_by_id
from snap_fit.aruco.sheet_metadata import SheetMetadataDecoder
from snap_fit.image.utils import load_image
from snap_fit.params.snap_fit_params import get_snap_fit_params
from snap_fit.puzzle.sheet_aruco import SheetAruco

_DEFAULT_BOARD_ID = "greendemo"


def _default_photo() -> Path:
    """Fall back to a generated greendemo board PNG as a stand-in photo."""
    board_dir = get_snap_fit_params().paths.aruco_board_fol / _DEFAULT_BOARD_ID
    return board_dir / "sheet_00.png"


def ingest(photo_fp: Path) -> None:
    """Decode, resolve the config by id, and load the sheet."""
    img = load_image(photo_fp)
    metadata = SheetMetadataDecoder().decode(img)
    if metadata is None:
        msg = f"No QR metadata decoded from {photo_fp.name}; cannot resolve config"
        raise RuntimeError(msg)
    lg.info(f"Decoded board_config_id={metadata.board_config_id!r}")

    try:
        config = load_sheet_config_by_id(metadata.board_config_id)
    except BoardConfigNotFoundError as exc:
        lg.error(f"No stored config for this board: {exc}")
        raise

    mask = config.preprocess.background_mask
    lg.info(f"Resolved config; background_mask={mask}")

    sheet = SheetAruco(config).load_sheet(photo_fp)
    lg.info(f"metadata: {sheet.metadata}")
    lg.info(f"pieces detected: {len(sheet.pieces)}")
    for piece in sheet.pieces[:10]:
        lg.info(f"  piece {piece.piece_id.piece_id:>3}  label={piece.label!r}")


if __name__ == "__main__":
    fp = Path(sys.argv[1]) if len(sys.argv) > 1 else _default_photo()
    ingest(fp)
