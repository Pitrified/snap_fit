"""A sheet is a photo full of pieces."""

from pathlib import Path

from snap_fit.image.process import (
    apply_dilation,
    apply_erosion,
    apply_threshold,
    compute_bounding_rectangles,
    convert_to_grayscale,
    find_contours,
)
from snap_fit.image.utils import compute_rects_area, flip_colors_bw, load_image


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
        gray_image = convert_to_grayscale(self.img_orig)
        binary_image = apply_threshold(gray_image, threshold=self.threshold)
        eroded_image = apply_erosion(binary_image, kernel_size=3, iterations=2)
        dilated_image = apply_dilation(eroded_image, kernel_size=3, iterations=1)
        img_bw = flip_colors_bw(dilated_image)
        self.img_bw = img_bw

    def find_pieces(self) -> None:
        """Find the pieces in the image."""
        self.contours = find_contours(self.img_bw)
        self.regions = compute_bounding_rectangles(self.contours)
        self.region_areas = compute_rects_area(self.regions)
        self.sort_pieces()

    def sort_pieces(self) -> None:
        """Sort the pieces based on their area."""
        pieces_data = [
            {"contour": contour, "region": region, "area": area}
            for contour, region, area in zip(
                self.contours, self.regions, self.region_areas
            )
        ]
        pieces_data_sorted = sorted(
            pieces_data, key=lambda piece: piece["area"], reverse=True
        )
        self.contours = [piece["contour"] for piece in pieces_data_sorted]
        self.regions = [piece["region"] for piece in pieces_data_sorted]
        self.region_areas = [piece["area"] for piece in pieces_data_sorted]
