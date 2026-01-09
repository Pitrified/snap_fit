"""Shape detector takes in a contour data and decides the shape of the segment.

Can use several strategies to determine the shape.
"""

from enum import StrEnum

import numpy as np

from snap_fit.config.types import SegmentShape
from snap_fit.image.process import estimate_affine_transform
from snap_fit.image.process import transform_contour


class ShapeDetectorStrategy(StrEnum):
    """Shape detector strategy enumeration."""

    NAIVE = "naive"


class ShapeDetector:
    """Shape detector class."""

    def __init__(
        self,
        strategy: ShapeDetectorStrategy = ShapeDetectorStrategy.NAIVE,
    ) -> None:
        """Initialize the shape detector with a strategy.

        Args:
            strategy (ShapeDetectorStrategy): The strategy to use for shape detection.
        """
        self.strategy = strategy

    def _align_points_horizontally(
        self,
        source_coords: np.ndarray,
        points: np.ndarray,
    ) -> np.ndarray:
        """Align the points horizontally based on the source coordinates.

        Args:
            source_coords (np.ndarray): The source coordinates of the segment.
            points (np.ndarray): The points of the segment.

        Returns:
            np.ndarray: The transformed points.
        """
        target = np.array([[0, 0], [0, 500]])
        transform_matrix = estimate_affine_transform(source_coords, target)
        points_transformed = transform_contour(points, transform_matrix)
        return points_transformed

    def detect_shape(
        self,
        source_coords: np.ndarray,
        points: np.ndarray,
    ) -> SegmentShape:
        """Compute the shape of the segment."""
        # align the points horizontally
        points_transformed = self._align_points_horizontally(source_coords, points)

        # get only x coords
        s1_xs = points_transformed[:, 0, 0]

        # count how many points are far from the center line
        flat_th = 20
        out_count = (s1_xs < -flat_th).sum()
        in_count = (s1_xs > flat_th).sum()

        # check if more than a certain number of points are far from the line
        count_th = 5
        is_out = bool(out_count > count_th)
        is_in = bool(in_count > count_th)

        # decide the shape
        match (is_out, is_in):
            case True, False:
                return SegmentShape.OUT
            case False, True:
                return SegmentShape.IN
            case False, False:
                return SegmentShape.EDGE
            case True, True:
                return SegmentShape.WEIRD
            case _:
                msg = "how did you manage this?"
                raise ValueError(msg)
