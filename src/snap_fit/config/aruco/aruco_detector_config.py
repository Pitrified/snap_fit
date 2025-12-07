"""Configuration for Aruco detector."""

import cv2
from pydantic import Field

from snap_fit.data_models.basemodel_kwargs import BaseModelKwargs


class ArucoDetectorConfig(BaseModelKwargs):
    """Configuration for Aruco detector."""

    adaptive_thresh_win_size_min: int = Field(
        3, description="Minimum window size for adaptive thresholding"
    )
    adaptive_thresh_win_size_max: int = Field(
        23, description="Maximum window size for adaptive thresholding"
    )
    adaptive_thresh_win_size_step: int = Field(
        10, description="Window size step for adaptive thresholding"
    )

    def to_detector_parameters(self) -> cv2.aruco.DetectorParameters:
        """Convert config to cv2.aruco.DetectorParameters.

        Returns:
            cv2.aruco.DetectorParameters: The detector parameters.
        """
        params = cv2.aruco.DetectorParameters()
        params.adaptiveThreshWinSizeMin = self.adaptive_thresh_win_size_min
        params.adaptiveThreshWinSizeMax = self.adaptive_thresh_win_size_max
        params.adaptiveThreshWinSizeStep = self.adaptive_thresh_win_size_step
        return params
