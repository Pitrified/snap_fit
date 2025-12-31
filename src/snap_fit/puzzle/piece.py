"""A puzzle piece is a chunk of image with a piece in it."""

from dataclasses import dataclass
from pathlib import Path
from typing import Self

import cv2
from cv2.typing import MatLike
from cv2.typing import Rect
import numpy as np

from snap_fit.config.types import CornerPos
from snap_fit.config.types import EdgePos
from snap_fit.config.types import SegmentShape
from snap_fit.data_models.piece_id import PieceId
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation import OrientedPieceType
from snap_fit.grid.orientation_utils import detect_base_orientation
from snap_fit.grid.orientation_utils import get_original_edge_pos
from snap_fit.grid.orientation_utils import get_piece_type
from snap_fit.image.contour import Contour
from snap_fit.image.process import convert_to_grayscale
from snap_fit.image.segment import Segment
from snap_fit.image.utils import cut_rect_from_image
from snap_fit.image.utils import draw_line
from snap_fit.image.utils import find_corner
from snap_fit.image.utils import pad_rect


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
        piece_id: PieceId,
        img_fp: Path,
        img_orig: np.ndarray,
        img_bw: np.ndarray,
        contour: Contour,
    ) -> None:
        """Initialize the piece with the contour, region, and area.

        Args:
            piece_id (PieceId): The piece ID.
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
        piece_id: PieceId,
        pad: int = 30,
    ) -> Self:
        """Create a piece from a contour and the full image.

        Will cut the piece from the full image, after padding the region of the contour.

        Args:
            contour (Contour): The contour of the piece.
            full_img_orig (np.ndarray): The original full image.
            full_img_bw (np.ndarray): The black and white full image.
            img_fp (Path): The image file path.
            piece_id (PieceId): The piece ID.
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
        for which_corner in CornerPos:
            self.corners[which_corner] = find_corner(self.img_crossmasked, which_corner)

    def split_contour(self) -> None:
        """Split the contour into four segments."""
        self.contour.build_segments(self.corners)
        # for ease of access, store the segments as attributes
        self.segments: dict[EdgePos, Segment] = self.contour.segments

        # Derive OrientedPieceType after segments are built
        self._derive_oriented_piece_type()

    def _derive_oriented_piece_type(self) -> None:
        """Derive and store the OrientedPieceType based on flat edges."""
        # Find which edges are flat (EDGE shape)
        flat_edges: list[EdgePos] = [
            edge_pos
            for edge_pos, segment in self.segments.items()
            if segment.shape == SegmentShape.EDGE
        ]

        # Get piece type from flat edge count
        piece_type = get_piece_type(len(flat_edges))

        # Get base orientation from flat edge positions
        orientation = detect_base_orientation(flat_edges)

        self.oriented_piece_type = OrientedPieceType(
            piece_type=piece_type, orientation=orientation
        )

        # Store flat edges for reference
        self.flat_edges = flat_edges

    def get_segment_at(
        self, edge_pos: EdgePos, rotation: Orientation = Orientation.DEG_0
    ) -> Segment:
        """Get the segment at a given edge position, considering rotation.

        When a piece is rotated, its edges move to new positions. This method
        returns the segment that would be at the given edge position after
        the piece is rotated by the specified amount.

        Args:
            edge_pos: The edge position to get (in the rotated frame).
            rotation: The rotation applied to the piece (default: no rotation).

        Returns:
            The segment at the requested position after rotation.

        Example:
            If rotation is 90° and edge_pos is TOP, this returns the segment
            that was originally at LEFT (since rotating 90° clockwise moves
            LEFT to TOP).
        """
        # Get the original edge position before rotation
        original_pos = get_original_edge_pos(edge_pos, rotation)
        return self.segments[original_pos]

    @property
    def region(self) -> Rect:
        """Get the region of the piece, in the coordinate of the piece."""
        return self.contour.region
