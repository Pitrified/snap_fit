"""A sheet is a photo full of pieces."""

from pathlib import Path
from typing import Sequence

from cv2.typing import MatLike, Point, Rect, Scalar

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
from snap_fit.puzzle.piece import Piece


class Sheet:
    """A sheet is a photo full of pieces."""

    def __init__(self, img_fp: Path) -> None:
        """Initialize the sheet with the image file path."""
        self.img_fp = img_fp
        self.load_image()

        self.threshold = 130
        self.preprocess()

        self.find_pieces()
        self.sort_pieces()
        self.filter_pieces()
        self.build_pieces()

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
        self.contours = find_contours(self.img_bw)
        self.regions = compute_bounding_rectangles(self.contours)
        self.region_areas = compute_rects_area(self.regions)
        self.pieces_data = [
            {"contour": contour, "region": region, "area": area}
            for contour, region, area in zip(
                self.contours, self.regions, self.region_areas
            )
        ]

    def sort_pieces(self) -> None:
        """Sort the pieces based on their area."""
        self.pieces_data.sort(key=lambda piece: piece["area"], reverse=True)
        self._update_attrs_from_data()

    def filter_pieces(self) -> None:
        """Filter the pieces based on the area."""
        min_area = 80_000
        self.pieces_data = [p for p in self.pieces_data if p["area"] > min_area]
        self._update_attrs_from_data()

    def _update_attrs_from_data(self) -> None:
        """Update the attributes from the pieces data.

        This method is used to update the attributes after filtering the pieces.
        Will update the contours, regions, and region_areas attributes.
        """
        self.contours: Sequence[MatLike] = [
            piece["contour"] for piece in self.pieces_data
        ]
        self.regions: list[Rect] = [piece["region"] for piece in self.pieces_data]
        self.region_areas: list[int] = [piece["area"] for piece in self.pieces_data]

    def build_pieces(self) -> None:
        """Build the pieces from the regions."""
        pad = 30

        self.pieces = []
        for pd in self.pieces_data:
            region = pd["region"]
            contour = pd["contour"]
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
