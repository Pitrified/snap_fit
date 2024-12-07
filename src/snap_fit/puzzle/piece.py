"""A puzzle piece is a chunk of image with a piece in it."""

from pathlib import Path

import cv2
from cv2.typing import MatLike, Rect
import numpy as np

from snap_fit.image.process import convert_to_grayscale
from snap_fit.image.utils import draw_line, translate_contour


class Piece:
    """A piece is a chunk of image with a piece in it."""

    def __init__(
        self,
        img_fp: Path,
        img_orig: np.ndarray,
        img_bw: np.ndarray,
        contour: MatLike,
        region: Rect,
        region_pad: Rect,
    ) -> None:
        """Initialize the piece with the contour, region, and area.

        Args:
            img_fp (Path): The image file path.
            img_orig (np.ndarray): The original image.
            img_bw (np.ndarray): The black and white image.
            contour (MatLike): The contour of the piece.
            region (Rect): The bounding rectangle of the piece.
                It is the bounding rectangle of the contour.
            region_pad (Rect): The padded bounding rectangle of the piece.
        """
        self.img_fp = img_fp
        self.img_orig = img_orig
        self.img_bw = img_bw
        self.contour = contour
        self.region = region
        self.region_pad = region_pad

        self.img_gray = convert_to_grayscale(self.img_orig)

        self.translate_contour()

    def translate_contour(self) -> None:
        """Translate the contour from image to piece coordinates."""
        x = -self.region_pad[0]
        y = -self.region_pad[1]
        self.contour_loc = translate_contour(self.contour, x, y)

    def build_cross_mask(self) -> None:
        """Build a cross mask for the piece."""
        shap = self.img_bw.shape
        diag_mask = np.zeros(shap, dtype=np.uint8)
        thick = int(sum(shap) / 2 / 4 * 1.05)
        diag_mask = draw_line(diag_mask, (0, 0), (shap[1], shap[0]), 255, thick)
        diag_mask = draw_line(diag_mask, (0, shap[0]), (shap[1], 0), 255, thick)
        self.cross_mask = diag_mask

    def find_corners(self) -> None:
        """Find the corners of the piece."""
        pass
