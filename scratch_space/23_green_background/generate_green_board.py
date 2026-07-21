"""Generate a printable green-background ArUco board set (phase 5).

Produces, under ``data/aruco_boards/{BOARD_CONFIG_ID}/``:
  - ``sheet_XX.png``          printable board images (green background)
  - ``{id}_ArucoBoardConfig.json``
  - ``{id}_SheetArucoConfig.json``  ingest config with the mask auto-enabled

This mirrors the print-time flow of
``scratch_space/20_piece_markers/01_print_read_board.ipynb`` but with a green
preset and the phase-4 ``derive_background_mask`` step, so the saved ingest
config already carries the enabled background mask (Q12/D14). Print the PNGs,
place pieces, photograph, then ingest with ``load_sheet_config_by_id``.

Run: ``python scratch_space/23_green_background/generate_green_board.py``
"""

from __future__ import annotations

import json

import cv2
from loguru import logger as lg

from snap_fit.aruco.board_config_resolver import derive_background_mask
from snap_fit.aruco.board_image_composer import BoardImageComposer
from snap_fit.aruco.sheet_metadata import SheetMetadata
from snap_fit.aruco.sheet_metadata import SheetMetadataDecoder
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig
from snap_fit.config.aruco.metadata_zone_config import MetadataZoneConfig
from snap_fit.config.aruco.metadata_zone_config import SlotGridConfig
from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig
from snap_fit.params.snap_fit_params import get_snap_fit_params

TAG = "greendemo"
BOARD_CONFIG_ID = "greendemo"
TOTAL_SHEETS = 2


def main() -> None:
    """Generate and save the green board set, then verify it."""
    params = get_snap_fit_params()
    save_dir = params.paths.aruco_board_fol / BOARD_CONFIG_ID
    save_dir.mkdir(parents=True, exist_ok=True)

    board_config = ArucoBoardConfig(background_preset="green")
    metadata_zone = MetadataZoneConfig(
        enabled=True,
        qr_n_codes=3,
        qr_ecc="M",
        text_enabled=True,
        slot_grid=SlotGridConfig(cols=4, rows=3),
    )
    # Full ingest config; derive the mask so the saved JSON carries it (D14).
    # min_area is set for this board's scale: pieces measure 10k-16k px^2 in the
    # rectified sheet on the greendemo captures, far below the 80k global default.
    sheet_aruco_config = SheetArucoConfig(
        min_area=5_000,
        detector=ArucoDetectorConfig(board=board_config),
        metadata_zone=metadata_zone,
    )
    sheet_aruco_config = derive_background_mask(sheet_aruco_config)

    composer = BoardImageComposer(board_config, metadata_zone)
    generated_paths = []
    for i in range(TOTAL_SHEETS):
        metadata = SheetMetadata(
            tag_name=TAG,
            sheet_index=i,
            total_sheets=TOTAL_SHEETS,
            board_config_id=BOARD_CONFIG_ID,
        )
        img = composer.compose(metadata)
        out_path = save_dir / f"sheet_{i:02d}.png"
        cv2.imwrite(str(out_path), img)
        generated_paths.append(out_path)
        lg.info(f"Saved {out_path.name}  ({img.shape[1]}x{img.shape[0]} px)")

    board_cfg_path = save_dir / f"{BOARD_CONFIG_ID}_ArucoBoardConfig.json"
    board_cfg_path.write_text(json.dumps(board_config.model_dump(), indent=2))
    sheet_cfg_path = save_dir / f"{BOARD_CONFIG_ID}_SheetArucoConfig.json"
    sheet_cfg_path.write_text(sheet_aruco_config.model_dump_json(indent=2))
    lg.info(f"Saved configs to {save_dir}")

    _verify(generated_paths, sheet_cfg_path)


def _verify(generated_paths: list, sheet_cfg_path) -> None:
    """Confirm the QR round-trips and the saved config has the mask enabled."""
    decoder = SheetMetadataDecoder()
    for path in generated_paths:
        img = cv2.imread(str(path))
        meta = decoder.decode(img)
        if meta is None:
            msg = f"QR did not decode on {path.name}"
            raise RuntimeError(msg)
        lg.info(f"QR OK on {path.name}: {meta.board_config_id}")

    reloaded = SheetArucoConfig.model_validate_json(sheet_cfg_path.read_text())
    mask = reloaded.preprocess.background_mask
    if mask is None or not mask.enabled:
        msg = "Saved SheetArucoConfig does not have the background mask enabled"
        raise RuntimeError(msg)
    lg.info(f"Saved config mask enabled: mode={mask.mode}")
    lg.info("Green board set ready to print.")


if __name__ == "__main__":
    main()
