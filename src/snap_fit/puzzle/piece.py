"""A puzzle piece is a chunk of image with a piece in it."""

from dataclasses import dataclass
from pathlib import Path
from typing import Self

import cv2
from cv2.typing import MatLike, Rect
import numpy as np

from snap_fit.config.types import CORNER_POSS, CornerPos, EdgePos
from snap_fit.image.contour import Contour
from snap_fit.image.process import convert_to_grayscale
from snap_fit.image.segment import Segment
from snap_fit.image.utils import cut_rect_from_image, draw_line, find_corner, pad_rect


@dataclass
class PieceRaw:
    """Raw piece data."""

    contour: MatLike
    region: Rect
    area: int


class Piece:
    """A piece is a chunk of image with a piece in it."""

    def __init__(
        self,
        piece_id: int,
        img_fp: Path,
        img_orig: np.ndarray,
        img_bw: np.ndarray,
        contour: Contour,
    ) -> None:
        """Initialize the piece with the contour, region, and area.

        Args:
            img_fp (Path): The image file path.
            img_orig (np.ndarray): The original image.
            img_bw (np.ndarray): The black and white image.
            contour (Contour): The contour of the piece.
        """
        self.piece_id = piece_id
        self.img_fp = img_fp
        self.img_orig = img_orig
        self.img_bw = img_bw
        self.contour = contour
        self.contour_loc = contour.cv_contour

        self.name = img_fp.stem

        self.img_gray = convert_to_grayscale(self.img_orig)

        self.build_cross_masked()
        self.find_corners()

        self.split_contour()

    @classmethod
    def from_contour(
        cls,
        contour: Contour,
        full_img_orig: np.ndarray,
        full_img_bw: np.ndarray,
        img_fp: Path,
        piece_id: int,
        pad: int = 30,
    ) -> Self:
        """Create a piece from a contour and the full image.

        Will cut the piece from the full image, after padding the region of the contour.

        Args:
            contour (Contour): The contour of the piece.
            full_img_orig (np.ndarray): The original full image.
            full_img_bw (np.ndarray): The black and white full image.
            img_fp (Path): The image file path.
            pad (int): The padding around the region of the contour.

        Returns:
            Piece: The piece created from the contour and the full image.
        """
        region = contour.region
        region_pad = pad_rect(region, pad, full_img_bw)
        img_orig_cut = cut_rect_from_image(full_img_orig, region_pad)
        img_bw_cut = cut_rect_from_image(full_img_bw, region_pad)
        # translate the contour to the new coordinates
        contour_cut = contour.translate(-region_pad[0], -region_pad[1])
        c = cls(
            piece_id=piece_id,
            img_fp=img_fp,
            img_orig=img_orig_cut,
            img_bw=img_bw_cut,
            contour=contour_cut,
        )
        return c

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
        self.corners: dict[CornerPos, tuple[int, int]] = {}
        for which_corner in CORNER_POSS:
            self.corners[which_corner] = find_corner(self.img_crossmasked, which_corner)

    def split_contour(self) -> None:
        """Split the contour into four segments."""
        self.contour.build_segments(self.corners)
        # for ease of access, store the segments as attributes
        self.segments: dict[EdgePos, Segment] = self.contour.segments
