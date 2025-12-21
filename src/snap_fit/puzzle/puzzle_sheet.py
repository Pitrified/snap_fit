"""Sheet composition for puzzle pieces with ArUco boards."""

import math
from pathlib import Path

import cv2
from loguru import logger as lg
import numpy as np

from snap_fit.puzzle.puzzle_config import SheetLayout
from snap_fit.puzzle.puzzle_generator import PuzzleGenerator
from snap_fit.puzzle.puzzle_generator import PuzzlePiece
from snap_fit.puzzle.puzzle_rasterizer import PuzzleRasterizer


class PuzzleSheetComposer:
    """Composes puzzle pieces onto ArUco board images."""

    def __init__(
        self,
        layout: SheetLayout,
        aruco_board_image: np.ndarray | None = None,
    ) -> None:
        """Initialize the sheet composer.

        Args:
            layout: Sheet layout configuration.
            aruco_board_image: Pre-generated ArUco board image.
                If None, uses blank white.
        """
        self.layout = layout
        self.rasterizer = PuzzleRasterizer(dpi=layout.dpi)

        # Calculate pixel dimensions
        self.sheet_width_px = int(layout.sheet_width * self.rasterizer.scale)
        self.sheet_height_px = int(layout.sheet_height * self.rasterizer.scale)

        if aruco_board_image is not None:
            # Resize ArUco board to match sheet dimensions
            self.base_image = cv2.resize(
                aruco_board_image,
                (self.sheet_width_px, self.sheet_height_px),
            )
        else:
            # Create blank white sheet
            self.base_image = (
                np.ones((self.sheet_height_px, self.sheet_width_px, 3), dtype=np.uint8)
                * 255
            )

    def place_pieces(
        self,
        pieces: list[PuzzlePiece],
        generator: PuzzleGenerator,
        start_idx: int = 0,
    ) -> np.ndarray:
        """Place puzzle pieces onto a sheet.

        Args:
            pieces: List of pieces to place.
            generator: PuzzleGenerator to get piece SVGs.
            start_idx: Starting index in the pieces list.

        Returns:
            Composed sheet image (BGR numpy array).
        """
        sheet = self.base_image.copy()

        # Calculate how many pieces fit
        piece_width = generator.config.piece_width
        piece_height = generator.config.piece_height
        pieces_per_row, pieces_per_col = self.layout.pieces_per_sheet(
            piece_width, piece_height
        )
        max_pieces = pieces_per_row * pieces_per_col

        # Get pieces for this sheet
        end_idx = min(start_idx + max_pieces, len(pieces))
        sheet_pieces = pieces[start_idx:end_idx]

        lg.info(
            f"Placing {len(sheet_pieces)} pieces on sheet "
            f"({pieces_per_row}x{pieces_per_col} grid)"
        )

        # Calculate piece dimensions in pixels
        # Include tab extension
        tab_extend = piece_width * generator.config.tab_size * 1.5
        piece_total_width = piece_width + 2 * tab_extend
        piece_total_height = piece_height + 2 * tab_extend

        for i, piece in enumerate(sheet_pieces):
            row = i // pieces_per_row
            col = i % pieces_per_row

            # Calculate position on sheet (in mm)
            x_mm = self.layout.margin + col * (piece_width + self.layout.piece_spacing)
            y_mm = self.layout.margin + row * (piece_height + self.layout.piece_spacing)

            # Generate piece SVG and rasterize
            piece_svg = generator.piece_to_svg(piece.row, piece.col, include_label=True)
            piece_img = self.rasterizer.rasterize(piece_svg)

            # Calculate pixel positions
            x_px = int(x_mm * self.rasterizer.scale)
            y_px = int(y_mm * self.rasterizer.scale)

            # Resize piece image if needed
            target_w = int(piece_total_width * self.rasterizer.scale)
            target_h = int(piece_total_height * self.rasterizer.scale)

            if piece_img.shape[1] != target_w or piece_img.shape[0] != target_h:
                piece_img = cv2.resize(piece_img, (target_w, target_h))

            # Overlay piece onto sheet
            self._overlay_piece(sheet, piece_img, x_px, y_px)

        return sheet

    def _overlay_piece(
        self,
        sheet: np.ndarray,
        piece_img: np.ndarray,
        x: int,
        y: int,
    ) -> None:
        """Overlay a piece image onto the sheet.

        Non-white pixels from the piece replace sheet pixels.
        """
        h, w = piece_img.shape[:2]
        sheet_h, sheet_w = sheet.shape[:2]

        # Calculate valid region
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(sheet_w, x + w)
        y2 = min(sheet_h, y + h)

        # Calculate piece region
        px1 = x1 - x
        py1 = y1 - y
        px2 = px1 + (x2 - x1)
        py2 = py1 + (y2 - y1)

        if x2 <= x1 or y2 <= y1:
            return

        # Get regions
        sheet_region = sheet[y1:y2, x1:x2]
        piece_region = piece_img[py1:py2, px1:px2]

        # Create mask: non-white pixels
        # Consider near-white as white (threshold)
        gray = cv2.cvtColor(piece_region, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

        # Apply piece where mask is set
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) > 0
        sheet_region[mask_3ch] = piece_region[mask_3ch]

    def generate_all_sheets(
        self,
        generator: PuzzleGenerator,
    ) -> list[np.ndarray]:
        """Generate all sheets needed for a puzzle.

        Args:
            generator: PuzzleGenerator with generated pieces.

        Returns:
            List of sheet images.
        """
        pieces = generator.generate()
        piece_width = generator.config.piece_width
        piece_height = generator.config.piece_height
        pieces_per_row, pieces_per_col = self.layout.pieces_per_sheet(
            piece_width, piece_height
        )
        pieces_per_sheet = pieces_per_row * pieces_per_col

        num_sheets = math.ceil(len(pieces) / pieces_per_sheet)
        lg.info(f"Generating {num_sheets} sheets for {len(pieces)} pieces")

        sheets = []
        for i in range(num_sheets):
            start_idx = i * pieces_per_sheet
            sheet = self.place_pieces(pieces, generator, start_idx)
            sheets.append(sheet)
            lg.info(f"Generated sheet {i + 1}/{num_sheets}")

        return sheets

    def save_sheets(
        self,
        sheets: list[np.ndarray],
        output_dir: str,
        prefix: str = "puzzle_sheet",
    ) -> list[str]:
        """Save sheets to image files.

        Args:
            sheets: List of sheet images.
            output_dir: Output directory.
            prefix: Filename prefix.

        Returns:
            List of saved file paths.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        paths = []
        for i, sheet in enumerate(sheets):
            filepath = output_path / f"{prefix}_{i + 1:03d}.png"
            cv2.imwrite(str(filepath), sheet)
            paths.append(str(filepath))
            lg.info(f"Saved {filepath}")

        return paths
