"""Match segments and compute the similarity between them."""

from math import floor

import numpy as np

from snap_fit.image.process import estimate_affine_transform
from snap_fit.image.process import transform_contour
from snap_fit.image.segment import Segment


class SegmentMatcher:
    """Match segments and compute the similarity between them."""

    def __init__(
        self,
        segment1: Segment,
        segment2: Segment,
    ) -> None:
        """Initialize the SegmentMatcher with two segments."""
        self.s1 = segment1
        self.s2 = segment2

        self._transform_s1()

    def _transform_s1(self) -> None:
        """Transform s1 so that it is over s2."""
        # estimate the affine transformation matrix
        # from the source segment to the target segment
        source = self.s1.coords
        target = self.s2.swap_coords
        transform_matrix = estimate_affine_transform(source, target)

        # transform the points of the source segment
        self.s1_points_transformed = transform_contour(self.s1.points, transform_matrix)

    def compute_similarity(self) -> float:
        """Compute the similarity between the two segments.

        Returns:
            float: The similarity between the two segments.
        """
        # TODO: check the shape in/out/flat

        # match the shape
        shape_similarity = self.match_shape()

        return shape_similarity

    def match_shape(self) -> float:
        """Match the shape of the two segments.

        Returns:
            float: The similarity of the shape of the two segments.
        """
        # compute the ratio to account for different segment lengths
        s1_len = len(self.s1)
        s2_len = len(self.s2)
        ratio = s2_len / s1_len

        # compute the similarity
        tot_dist: float = 0
        for i1 in range(s1_len):
            i2 = floor(i1 * ratio)
            p1 = self.s1_points_transformed[i1][0]
            p2 = self.s2.points[i2][0]
            dist = np.linalg.norm(p1 - p2)
            tot_dist += dist  # type: ignore - numpy floating to float

        # normalize the total distance
        similarity = tot_dist / max(s1_len, s2_len)

        # MAYBE should we rescale the dist on the distance between the ends?
        # MAYBE should we take the average of the distances between the points?

        return similarity
