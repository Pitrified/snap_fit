"""A sheet is a photo full of pieces."""

from pathlib import Path
from typing import Sequence

from cv2.typing import MatLike, Point, Rect, Scalar

from snap_fit.image.contour import Contour
from snap_fit.image.process import (
    apply_dilation,
    apply_erosion,
    apply_gaussian_blur,
    apply_threshold,
    compute_bounding_rectangles,
    convert_to_grayscale,
    find_contours,
)
from snap_fit.image.utils import (
    compute_rects_area,
    cut_rect_from_image,
    flip_colors_bw,
    load_image,
    pad_rect,
)
from snap_fit.puzzle.piece import Piece, PieceRaw


class Sheet:
    """A sheet is a photo full of pieces."""

    def __init__(self, img_fp: Path) -> None:
        """Initialize the sheet with the image file path."""
        self.img_fp = img_fp
        self.load_image()

        self.threshold = 130
        self.preprocess()

        self.find_pieces()

    def load_image(self) -> None:
        """Loads the image from the file path."""
        self.img_orig = load_image(self.img_fp)

    def preprocess(self) -> None:
        """Preprocess the image."""
        image = self.img_orig
        image = apply_gaussian_blur(image, kernel_size=(21, 21))
        image = convert_to_grayscale(image)
        image = apply_threshold(image, threshold=self.threshold)
        image = apply_erosion(image, kernel_size=3, iterations=2)
        image = apply_dilation(image, kernel_size=3, iterations=1)
        image = flip_colors_bw(image)
        self.img_bw = image

    def find_pieces(self) -> None:
        """Find the pieces in the image."""
        self.find_contours()
        self.sort_contours()
        self.filter_contours()
        self.build_pieces()

    def find_contours(self) -> None:
        """Find the contours in the image."""
        cv_contours = find_contours(self.img_bw)
        self.contours = [Contour(cv_contour) for cv_contour in cv_contours]

    def sort_contours(self) -> None:
        """Sort the contours based on their area."""
        self.contours.sort(key=lambda piece: piece.area, reverse=True)

    def filter_contours(self) -> None:
        """Filter the contours based on the area."""
        min_area = 80_000
        self.contours = [p for p in self.contours if p.area > min_area]

    def build_pieces(self) -> None:
        """Build the pieces from the contours."""
        pad = 30

        self.pieces = []
        for pd in self.contours:
            region = pd.region
            contour = pd.cv_contour
            region_pad = pad_rect(region, pad, self.img_bw)
            img_bw_cut = cut_rect_from_image(self.img_bw, region_pad)
            img_orig_cut = cut_rect_from_image(self.img_orig, region_pad)
            piece = Piece(
                img_fp=self.img_fp,
                img_orig=img_orig_cut,
                img_bw=img_bw_cut,
                contour=contour,
                region=region,
                region_pad=region_pad,
            )
            self.pieces.append(piece)
