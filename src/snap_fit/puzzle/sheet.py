"""A sheet is a photo full of pieces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger as lg

from snap_fit.data_models.piece_id import PieceId

if TYPE_CHECKING:
    from pathlib import Path

    from cv2.typing import Rect
    import numpy as np

    from snap_fit.aruco.sheet_metadata import SheetMetadata
    from snap_fit.aruco.slot_grid import SlotGrid

from snap_fit.config.aruco.sheet_aruco_config import BackgroundMaskConfig
from snap_fit.config.aruco.sheet_aruco_config import SheetPreprocessConfig
from snap_fit.image.contour import Contour
from snap_fit.image.process import apply_dilation
from snap_fit.image.process import apply_erosion
from snap_fit.image.process import apply_gaussian_blur
from snap_fit.image.process import apply_threshold
from snap_fit.image.process import compute_hsv_mask
from snap_fit.image.process import convert_to_grayscale
from snap_fit.image.process import find_contours
from snap_fit.image.process import paint_masked_white
from snap_fit.image.utils import flip_colors_bw
from snap_fit.image.utils import load_image
from snap_fit.puzzle.piece import Piece


class Sheet:
    """A sheet is a photo full of pieces."""

    def __init__(
        self,
        img_fp: Path,
        min_area: int = 80_000,
        image: np.ndarray | None = None,
        sheet_id: str | None = None,
        slot_grid: SlotGrid | None = None,
        crop_offset: int = 0,
        preprocess: SheetPreprocessConfig | None = None,
    ) -> None:
        """Initialize the sheet with the image file path."""
        self.img_fp = img_fp
        self.min_area = min_area
        self.sheet_id = sheet_id or img_fp.stem
        self.crop_offset = crop_offset
        self.preprocess_config = preprocess or SheetPreprocessConfig()

        self.metadata: SheetMetadata | None = None
        self.slot_grid: SlotGrid | None = slot_grid

        if image is not None:
            self.img_orig = image
        else:
            self.load_image()

        self.preprocess()

        self.find_pieces()

    def load_image(self) -> None:
        """Load the image from the file path."""
        self.img_orig = load_image(self.img_fp)

    def preprocess(self) -> None:
        """Preprocess the image into the binary `img_bw` used for contours."""
        cfg = self.preprocess_config
        blurred = apply_gaussian_blur(
            self.img_orig, kernel_size=(cfg.blur_kernel_size, cfg.blur_kernel_size)
        )

        mask_cfg = cfg.background_mask
        if mask_cfg is not None and mask_cfg.enabled:
            binary = self._binary_from_mask(blurred, mask_cfg, cfg.threshold)
        else:
            gray = convert_to_grayscale(blurred)
            binary = apply_threshold(gray, threshold=cfg.threshold)

        binary = apply_erosion(
            binary,
            kernel_size=cfg.erosion_kernel_size,
            iterations=cfg.erosion_iterations,
        )
        binary = apply_dilation(
            binary,
            kernel_size=cfg.dilation_kernel_size,
            iterations=cfg.dilation_iterations,
        )
        self.img_bw = flip_colors_bw(binary)

    def _binary_from_mask(
        self,
        blurred: np.ndarray,
        mask_cfg: BackgroundMaskConfig,
        threshold: int,
    ) -> np.ndarray:
        """Build the binary image from the HSV background mask.

        Runs between blur and erosion, in place of the grayscale + threshold
        step. Output keeps the standard polarity (background 255, pieces 0).
        """
        mask = compute_hsv_mask(blurred, mask_cfg.lower_hsv, mask_cfg.upper_hsv)
        if mask_cfg.mode == "as_threshold":
            return mask
        # flatten_to_white: repaint the masked background, then threshold as usual.
        flattened = paint_masked_white(blurred, mask)
        gray = convert_to_grayscale(flattened)
        return apply_threshold(gray, threshold=threshold)

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
        lg.debug(f"kept {len(self.contours)} contours with {self.min_area}")

    def build_pieces(self) -> None:
        """Build the pieces from the contours."""
        pad = 30

        self.pieces: list[Piece] = []
        for piece_id_int, contour in enumerate(self.contours):
            piece_id = PieceId(sheet_id=self.sheet_id, piece_id=piece_id_int)
            piece = Piece.from_contour(
                contour=contour,
                full_img_orig=self.img_orig,
                full_img_bw=self.img_bw,
                img_fp=self.img_fp,
                piece_id=piece_id,
                pad=pad,
            )
            if self.slot_grid is not None:
                cx, cy = contour.centroid
                cx_board = cx + self.crop_offset
                cy_board = cy + self.crop_offset
                slot = self.slot_grid.slot_for_centroid(cx_board, cy_board)
                if slot is not None:
                    piece.label = self.slot_grid.label_for_slot(*slot)
            self.pieces.append(piece)

    @property
    def regions(self) -> list[Rect]:
        """Get the regions of all pieces in the sheet, in the sheet coordinates."""
        return [contour.region for contour in self.contours]
