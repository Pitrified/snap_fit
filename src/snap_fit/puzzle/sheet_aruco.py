"""Sheet with ArUco markers for perspective correction."""

from pathlib import Path

from loguru import logger as lg

from snap_fit.aruco.aruco_detector import ArucoDetector
from snap_fit.puzzle.sheet import Sheet


class SheetAruco(Sheet):
    """A sheet that uses ArUco markers for perspective correction."""

    def __init__(
        self,
        img_fp: Path,
        aruco_detector: ArucoDetector,
        min_area: int = 80_000,
        crop_margin: int = 0,
    ) -> None:
        """Initialize the SheetAruco.

        Args:
            img_fp: Path to the image file.
            aruco_detector: The ArucoDetector instance.
            min_area: Minimum area for pieces.
            crop_margin: Margin to crop from the rectified image (to remove markers).
        """
        self.aruco_detector = aruco_detector
        self.crop_margin = crop_margin
        super().__init__(img_fp, min_area)

    def load_image(self) -> None:
        """Load and rectify the image."""
        super().load_image()

        lg.info("Detecting ArUco markers and correcting perspective...")
        corners, ids, _ = self.aruco_detector.detect_markers(self.img_orig)

        rectified = self.aruco_detector.correct_perspective(
            self.img_orig,
            corners,  # pyright: ignore[reportArgumentType] opencv weirdness
            ids,
        )

        if rectified is not None:
            self.img_orig = rectified

            if self.crop_margin > 0:
                h, w = self.img_orig.shape[:2]
                self.img_orig = self.img_orig[
                    self.crop_margin : h - self.crop_margin,
                    self.crop_margin : w - self.crop_margin,
                ]
                lg.info(f"Cropped margin of {self.crop_margin} pixels.")
        else:
            lg.warning("Perspective correction failed. Using original image.")
