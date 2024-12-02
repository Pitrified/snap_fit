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
    ) -> None:
        """Initialize the piece with the contour, region, and area."""
        self.img_fp = img_fp
        self.img_orig = img_orig
        self.img_bw = img_bw
        self.contour = contour
        self.region = region
