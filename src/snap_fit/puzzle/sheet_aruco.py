"""Sheet with ArUco markers for perspective correction."""

from pathlib import Path

from loguru import logger as lg

from snap_fit.aruco.aruco_detector import ArucoDetector
from snap_fit.image.utils import load_image
from snap_fit.puzzle.sheet import Sheet


class SheetAruco:
    """A sheet that uses ArUco markers for perspective correction."""

    def __init__(
        self,
        aruco_detector: ArucoDetector,
        crop_margin: int = 0,
    ) -> None:
        """Initialize the SheetAruco.

        Args:
            aruco_detector: The ArucoDetector instance.
            crop_margin: Margin to crop from the rectified image (to remove markers).
        """
        self.aruco_detector = aruco_detector
        self.crop_margin = crop_margin

    def load_sheet(self, img_fp: Path, min_area: int = 80_000) -> Sheet:
        """Load and rectify the image, then return a Sheet instance.

        Args:
            img_fp: Path to the image file.
            min_area: Minimum area for pieces.

        Returns:
            A Sheet instance with the rectified image.
        """
        lg.info(f"Loading image from {img_fp}")
        img_orig = load_image(img_fp)

        lg.info("Detecting ArUco markers and correcting perspective...")
        corners, ids, _ = self.aruco_detector.detect_markers(img_orig)

        rectified = self.aruco_detector.correct_perspective(
            img_orig,
            corners,  # pyright: ignore[reportArgumentType] opencv weirdness
            ids,
        )

        if rectified is not None:
            img_final = rectified

            if self.crop_margin > 0:
                h, w = img_final.shape[:2]
                img_final = img_final[
                    self.crop_margin : h - self.crop_margin,
                    self.crop_margin : w - self.crop_margin,
                ]
                lg.info(f"Cropped margin of {self.crop_margin} pixels.")
        else:
            lg.warning("Perspective correction failed. Using original image.")
            img_final = img_orig

        return Sheet(img_fp=img_fp, min_area=min_area, image=img_final)
