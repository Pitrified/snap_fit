"""A contour is a curve joining all the continuous points (along the boundary).

Each individual contour is a Numpy array of (x,y) coordinates of boundary points of the object.

https://docs.opencv.org/3.4/d4/d73/tutorial_py_contours_begin.html
"""

import numpy as np

from snap_fit.image.process import compute_bounding_rectangle
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

    def translate(self, x_offset: int, y_offset: int) -> None:
        """Translates the contour by the specified x and y offsets."""
        self.cv_contour = translate_contour(self.cv_contour, x_offset, y_offset)

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
        print(c_wrap[:10, 0])
        print(c_wrap[-10:, 0])
        # Calculate the derivative of the contour
        d_wrap = np.gradient(c_wrap, step, axis=0)
        # Remove the wrapped points
        d = d_wrap[step:-step]
        self.derivative = d
