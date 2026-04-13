"""Sheet with ArUco markers for perspective correction."""

from pathlib import Path

from loguru import logger as lg

from snap_fit.aruco.aruco_detector import ArucoDetector
from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig
from snap_fit.image.utils import load_image
from snap_fit.puzzle.sheet import Sheet


class SheetAruco:
    """A sheet that uses ArUco markers for perspective correction."""

    def __init__(self, config: SheetArucoConfig) -> None:
        """Initialize the SheetAruco with a `SheetArucoConfig`.

        Args:
            config: `SheetArucoConfig` containing `detector`, `min_area`, and
                optional `crop_margin`.
        """
        self.config = config
        self.aruco_detector = ArucoDetector(config.detector)

        if config.crop_margin is None:
            board_config = config.detector.board
            self.crop_margin = (
                board_config.marker_length
                + board_config.margin
                + config.detector.rect_margin
            )
        else:
            self.crop_margin = config.crop_margin

    def load_sheet(self, img_fp: Path) -> Sheet:
        """Load and rectify the image, then return a Sheet instance.

        Args:
            img_fp: Path to the image file.

        Returns:
            A Sheet instance with the rectified image. `min_area` is read from
            `self.config.min_area`.
        """
        lg.info(f"Loading image from {img_fp}")
        img_orig = load_image(img_fp)

        # Decode metadata BEFORE rectification (QR codes may be cropped out after).
        from snap_fit.aruco.sheet_metadata import SheetMetadataDecoder  # noqa: PLC0415

        metadata = SheetMetadataDecoder().decode(img_orig)
        if metadata is None:
            lg.debug(f"No sheet metadata QR found in {img_fp.name}")

        lg.info("Detecting ArUco markers and correcting perspective...")
        rectified = self.aruco_detector.rectify(img_orig)

        crop_offset = 0
        if rectified is not None:
            img_final = rectified

            if self.crop_margin > 0:
                h, w = img_final.shape[:2]
                img_final = img_final[
                    self.crop_margin : h - self.crop_margin,
                    self.crop_margin : w - self.crop_margin,
                ]
                lg.info(f"Cropped margin of {self.crop_margin} pixels.")
                crop_offset = int(
                    self.crop_margin
                    - self.config.detector.rect_margin
                    + self.config.detector.board.margin
                )

            if self.config.metadata_zone is not None:
                board_config = self.config.detector.board
                qr_strip_h = board_config.margin + board_config.marker_length
                h_now = img_final.shape[0]
                img_final = img_final[: h_now - qr_strip_h, :]
                lg.info(f"Cropped QR strip ({qr_strip_h} px from bottom).")
        else:
            lg.warning("Perspective correction failed. Using original image.")
            img_final = img_orig

        slot_grid = None
        if self.config.metadata_zone is not None:
            from snap_fit.aruco.slot_grid import SlotGrid  # noqa: PLC0415

            slot_grid = SlotGrid(
                self.config.metadata_zone.slot_grid,
                self.config.detector.board,
            )

        sheet = Sheet(
            img_fp=img_fp,
            min_area=self.config.min_area,
            image=img_final,
            slot_grid=slot_grid,
            crop_offset=crop_offset,
        )
        sheet.metadata = metadata

        return sheet
