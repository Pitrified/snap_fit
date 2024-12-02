"""A puzzle piece is a chunk of image with a piece in it."""

from pathlib import Path

from cv2.typing import MatLike, Rect
import numpy as np


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
