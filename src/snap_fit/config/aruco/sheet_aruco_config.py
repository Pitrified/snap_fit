"""Configuration for Sheet ArUco processing."""

from pydantic import Field

from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig
from snap_fit.config.aruco.metadata_zone_config import MetadataZoneConfig
from snap_fit.utils.basemodel_kwargs import BaseModelKwargs


class BackgroundMaskConfig(BaseModelKwargs):
    """Optional background-removal mask settings for sheet preprocessing."""

    enabled: bool = Field(default=False, description="Enable the mask override")
    lower_hsv: tuple[int, int, int] = Field(
        default=(35, 40, 40),
        description="Lower HSV bound for the background mask",
    )
    upper_hsv: tuple[int, int, int] = Field(
        default=(95, 255, 255),
        description="Upper HSV bound for the background mask",
    )


class SheetArucoConfig(BaseModelKwargs):
    """Configuration for sheet processing using ArUco markers.

    Attributes:
        min_area: Minimum area for detected pieces.
        crop_margin: Pixels to crop after rectification. If None, computed from
            the detector/board settings.
        detector: `ArucoDetectorConfig` used to construct the detector.
        background_mask: Optional mask config for background-colored boards.
        metadata_zone: Optional config for QR strip and slot grid. When None,
            existing behaviour is unchanged.
    """

    min_area: int = Field(default=80_000, description="Minimum area for pieces")
    crop_margin: int | float | None = Field(
        default=None, description="Margin to crop from rectified image"
    )
    detector: ArucoDetectorConfig = Field(
        default_factory=ArucoDetectorConfig, description="Aruco detector config"
    )
    background_mask: BackgroundMaskConfig | None = Field(
        default=None, description="Optional background-mask preprocess config"
    )
    metadata_zone: MetadataZoneConfig | None = Field(
        default=None, description="QR strip and slot grid config"
    )
