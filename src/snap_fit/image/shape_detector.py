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
    ADAPTIVE = "adaptive"


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
        match self.strategy:
            case ShapeDetectorStrategy.ADAPTIVE:
                return self._detect_shape_adaptive(source_coords, points)
            case ShapeDetectorStrategy.NAIVE:
                return self._detect_shape_naive(source_coords, points)
            case _:
                msg = f"Unknown shape detection strategy: {self.strategy}"
                raise ValueError(msg)

    def _detect_shape_naive(
        self,
        source_coords: np.ndarray,
        points: np.ndarray,
    ) -> SegmentShape:
        """Detect shape using naive fixed-threshold strategy."""
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

    def _detect_shape_adaptive(
        self,
        source_coords: np.ndarray,
        points: np.ndarray,
    ) -> SegmentShape:
        """Detect shape using adaptive threshold strategy.

        Adapts thresholds based on segment statistics to reduce false WEIRD
        classifications while maintaining safety by preferring WEIRD when ambiguous.

        Algorithm:
        1. Calculate flat_th from segment standard deviation
        2. Calculate count_th as percentage of segment length
        3. Count points beyond each threshold
        4. Only classify IN/OUT when confident, else classify as WEIRD
        """
        # align the points horizontally
        points_transformed = self._align_points_horizontally(source_coords, points)

        # get only x coords
        s1_xs = points_transformed[:, 0, 0]

        # adaptive thresholds based on segment statistics
        flat_th = max(10.0, np.std(s1_xs) * 1.5)
        count_th = max(3, len(s1_xs) * 0.05)

        # count points beyond thresholds
        out_count = (s1_xs < -flat_th).sum()
        in_count = (s1_xs > flat_th).sum()

        # convert to python bools for pattern matching
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
