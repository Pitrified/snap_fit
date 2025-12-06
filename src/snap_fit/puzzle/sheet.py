"""A sheet is a photo full of pieces."""

from pathlib import Path

from cv2.typing import Rect

from snap_fit.image.contour import Contour
from snap_fit.image.process import (
    apply_dilation,
    apply_erosion,
    apply_gaussian_blur,
    apply_threshold,
    convert_to_grayscale,
    find_contours,
)
from snap_fit.image.utils import (
    flip_colors_bw,
    load_image,
)
from snap_fit.puzzle.piece import Piece


class Sheet:
    """A sheet is a photo full of pieces."""

    def __init__(
        self,
        img_fp: Path,
        min_area: int = 80_000,
    ) -> None:
        """Initialize the sheet with the image file path."""
        self.img_fp = img_fp
        self.min_area = min_area

        self.load_image()

        # REFA should be a config object
        #      together with the preprocess params
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
        self.contours = [p for p in self.contours if p.area > self.min_area]

    def build_pieces(self) -> None:
        """Build the pieces from the contours."""
        pad = 30

        self.pieces: list[Piece] = []
        for piece_id, contour in enumerate(self.contours):
            piece = Piece.from_contour(
                contour=contour,
                full_img_orig=self.img_orig,
                full_img_bw=self.img_bw,
                img_fp=self.img_fp,
                piece_id=piece_id,
                pad=pad,
            )
            self.pieces.append(piece)

    @property
    def regions(self) -> list[Rect]:
        """Get the regions of all pieces in the sheet, in the sheet coordinates."""
        return [contour.region for contour in self.contours]
