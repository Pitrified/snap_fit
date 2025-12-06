"""A Segment is a part of a contour that is between two corners."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from snap_fit.image.contour import Contour


class Segment:
    """A Segment is a part of a contour that is between two corners."""

    def __init__(
        self,
        contour: Contour,
        start_idx: int,
        end_idx: int,
    ) -> None:
        """Initialize the segment with the contour and the start and end indices.

        Args:
            contour (Contour): The contour to which the segment belongs.
            start_idx (int): The start index of the segment.
            end_idx (int): The end index of the segment.
        """
        self.contour = contour
        self.start_idx = start_idx
        self.end_idx = end_idx

        # get the points of the segment
        self.get_points()

        # get the end points of the segment
        self.start_coord = self.points[0][0]
        self.end_coord = self.points[-1][0]
        self.coords = np.vstack((self.start_coord, self.end_coord))
        self.swap_coords = np.flip(self.coords, axis=0)

    def get_points(self) -> None:
        """Get the points of the segment.

        Returns:
            list[np.ndarray]: The points of the segment.
        """
        # if the start index is greater than the end index,
        # the segment wraps around the contour
        self.is_wrapped = self.start_idx > self.end_idx

        if self.is_wrapped:
            # if the segment wraps around the contour,
            # get the points from the start to the end of the contour
            # and then from the start of the contour to the end
            to_end = self.contour.cv_contour[self.start_idx :]
            from_start = self.contour.cv_contour[: self.end_idx + 1]
            self.points = np.vstack((to_end, from_start))
        else:
            # if the segment does not wrap around the contour,
            # get the points from the start to the end
            self.points = self.contour.cv_contour[self.start_idx : self.end_idx + 1]

    def __len__(self) -> int:
        """Return the number of points in the segment."""
        return self.points.shape[0]
