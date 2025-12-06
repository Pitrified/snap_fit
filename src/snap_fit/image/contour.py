"""A contour is a curve joining all the continuous points (along the boundary).

Each individual contour is a Numpy array of (x,y) coordinates of boundary points of the object.

https://docs.opencv.org/3.4/d4/d73/tutorial_py_contours_begin.html
"""

from __future__ import annotations

import numpy as np

from snap_fit.config.types import CORNER_POSS, EDGE_ENDS_TO_CORNER, CornerPos, EdgePos
from snap_fit.image.process import compute_bounding_rectangle
from snap_fit.image.segment import Segment
from snap_fit.image.utils import compute_rect_area, translate_contour


class Contour:
    """A contour is a curve joining all the continuous points (along the boundary)."""

    def __init__(
        self,
        cv_contour: np.ndarray,
    ) -> None:
        """Initialize the contour with the OpenCV contour."""
        self.cv_contour = cv_contour
        self.region = compute_bounding_rectangle(cv_contour)
        self.area = compute_rect_area(self.region)

    def translate(self, x_offset: int, y_offset: int) -> Contour:
        """Translates the contour by the specified x and y offsets.

        Args:
            x_offset (int): The x offset.
            y_offset (int): The y offset.

        Returns:
            Contour: A new contour translated by the specified offsets.
        """
        new_cv_contour = translate_contour(self.cv_contour, x_offset, y_offset)
        return Contour(new_cv_contour)

    def derive(
        self,
        step: int = 5,
    ) -> None:
        """Derives the contour to get the orientation and curvature.

        For each point on the contour, the derivative is calculated using the central difference method.
        The step size determines the distance between the points used for the derivative.

        Args:
            step (int): The step size for the derivative (default is 5).
        """
        # as the contour is a closed curve, we can calculate the derivative by
        # wrapping around the end points to the start points
        c_wrap = np.vstack((self.cv_contour, self.cv_contour[:step]))
        # also wrap around the start points to the end points
        c_wrap = np.vstack((self.cv_contour[-step:], c_wrap))
        # > print(c_wrap[:10, 0])
        # > print(c_wrap[-10:, 0])
        # Calculate the derivative of the contour
        d_wrap = np.gradient(c_wrap, step, axis=0)
        # Remove the wrapped points
        d = d_wrap[step:-step]
        self.derivative = d

    def build_segments(self, corners: dict[CornerPos, tuple[int, int]]) -> None:
        """Split the contour into four segments."""
        self.match_corners(corners)
        self.split_contour()

    def match_corners(self, corners: dict[CornerPos, tuple[int, int]]) -> None:
        """Match the given corners to the closest points on the contour.

        Will find the indexes of the closest points on the contour to the given corners.
        Will also store the coordinates of the closest points.

        Args:
            corners (dict[CornerPos, tuple[int, int]]): The corners to match to the contour.
        """
        self.corner_idxs = {}
        self.corner_coords = {}
        for which_corner in CORNER_POSS:
            corner = corners[which_corner]
            con_diff = self.cv_contour - corner
            corner_idx = abs(con_diff).sum(axis=1).sum(axis=1).argmin()
            self.corner_idxs[which_corner] = corner_idx
            self.corner_coords[which_corner] = self.cv_contour[corner_idx][0]

    def split_contour(self) -> None:
        """Split the contour into four segments."""
        self.segments: dict[EdgePos, Segment] = {}
        for edge_name, edge_ends in EDGE_ENDS_TO_CORNER.items():
            start_idx = self.corner_idxs[edge_ends[0]]
            end_idx = self.corner_idxs[edge_ends[1]]
            segment = Segment(self, start_idx, end_idx)
            self.segments[edge_name] = segment
