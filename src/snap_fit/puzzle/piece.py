"""A puzzle piece is a chunk of image with a piece in it."""

from pathlib import Path

import cv2
from cv2.typing import MatLike, Rect
import numpy as np

from snap_fit.image.process import convert_to_grayscale
from snap_fit.image.utils import draw_line, find_corner, translate_contour


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
        self.contour = contour  # REFA should be a Contour object
        self.region = region
        self.region_pad = region_pad

        self.img_gray = convert_to_grayscale(self.img_orig)

        self.translate_contour()

        self.build_cross_masked()
        self.find_corners()

        self.split_contour()

    def translate_contour(self) -> None:
        """Translate the contour from image to piece coordinates."""
        # REFA should be done in the Contour class
        x = -self.region_pad[0]
        y = -self.region_pad[1]
        self.contour_loc = translate_contour(self.contour, x, y)

    def build_cross_masked(self) -> None:
        """Build a cross mask for the piece and apply it."""
        shap = self.img_bw.shape

        # create a mask with a diagonal cross
        diag_mask = np.zeros(shap, dtype=np.uint8)
        thick = int(sum(shap) / 2 / 4 * 1.05)
        diag_mask = draw_line(diag_mask, (0, 0), (shap[1], shap[0]), 255, thick)
        diag_mask = draw_line(diag_mask, (0, shap[0]), (shap[1], 0), 255, thick)
        self.cross_mask = diag_mask

        # apply the mask to the image
        self.img_crossmasked = cv2.bitwise_and(self.img_bw, self.cross_mask)

    def find_corners(self) -> None:
        """Find the corner of the piece by sweeping the image.

        The function sweeps the image with a line starting from the corner,
        orthogonal to the diagonal of the image, and stops when the line hits the
        crossmasked image.
        The corner is then the point where the line hits the crossmasked image.

        Args:
            img_crossmasked (np.ndarray): The image with the diagonal line.
            which_corner (str): The corner to find, one of
                "top_left", "top_right", "bottom_left", "bottom_right".

        Returns:
            tuple: The coordinates of the corner, as a tuple (x, y).
        """
        self.corners = {}
        for which_corner in [
            "top_left",
            "top_right",
            "bottom_left",
            "bottom_right",
        ]:
            self.corners[which_corner] = find_corner(self.img_crossmasked, which_corner)

    def split_contour(self) -> None:
        """Split the contour into four segments."""
        # REFA should be done in the Contour class

        # find the point on the contour closest to each corner
        self.contour_corner_idxs = {}
        self.contour_corner_coords = {}
        for which_corner in [
            "top_left",
            "top_right",
            "bottom_left",
            "bottom_right",
        ]:
            corner = self.corners[which_corner]
            con_diff = self.contour_loc - corner
            corner_idx = abs(con_diff).sum(axis=1).sum(axis=1).argmin()
            self.contour_corner_idxs[which_corner] = corner_idx
            self.contour_corner_coords[which_corner] = self.contour_loc[corner_idx][0]

        # split the contour into four segments
        self.contour_segments = {}
