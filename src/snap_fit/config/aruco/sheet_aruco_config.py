"""Configuration for Sheet ArUco processing."""

from pydantic import Field

from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig
from snap_fit.data_models.basemodel_kwargs import BaseModelKwargs


class SheetArucoConfig(BaseModelKwargs):
    """Configuration for sheet processing using ArUco markers.

    Attributes:
        min_area: Minimum area for detected pieces.
        crop_margin: Pixels to crop after rectification. If None, computed from
            the detector/board settings.
        detector: `ArucoDetectorConfig` used to construct the detector.
    """

    min_area: int = Field(default=80_000, description="Minimum area for pieces")
    crop_margin: int | float | None = Field(
        default=None, description="Margin to crop from rectified image"
    )
    detector: ArucoDetectorConfig = Field(
        default_factory=ArucoDetectorConfig, description="Aruco detector config"
    )
