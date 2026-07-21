"""Configuration for Sheet ArUco processing."""

from typing import Literal

from pydantic import Field
from pydantic import model_validator

from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig
from snap_fit.config.aruco.metadata_zone_config import MetadataZoneConfig
from snap_fit.utils.basemodel_kwargs import BaseModelKwargs

_HUE_MAX = 179
_CHANNEL_MAX = 255


class InvalidHsvBoundsError(ValueError):
    """Raised when a BackgroundMaskConfig HSV bound is out of range or inverted."""


class BackgroundMaskConfig(BaseModelKwargs):
    """Optional background-removal mask settings for sheet preprocessing.

    HSV bounds use the OpenCV scale: hue is 0-179, saturation and value 0-255.

    The default value floor of 100 is set from real captures, not from theory:
    a board background reads V 186-212, while pieces lit by reflected board
    light reach V 42-61 and share the background hue (70-81). A lower floor
    (the original 40) classifies those glare-lit piece pixels as background,
    which silently erodes every piece and can drop one entirely. Measured safe
    band on the greendemo captures: 60-120; above ~140 dim background regions
    stop being masked and merge into the pieces.
    """

    enabled: bool = Field(default=False, description="Enable the mask override")
    mode: Literal["as_threshold", "flatten_to_white"] = Field(
        default="as_threshold",
        description=(
            "How the mask feeds the pipeline. 'as_threshold' uses the in-range"
            " mask directly as the binary (replaces the threshold step)."
            " 'flatten_to_white' paints the masked pixels white and runs the"
            " normal grayscale + threshold path on the flattened image."
        ),
    )
    lower_hsv: tuple[int, int, int] = Field(
        default=(35, 40, 100),
        description="Lower HSV bound (OpenCV scale: H 0-179, S/V 0-255)",
    )
    upper_hsv: tuple[int, int, int] = Field(
        default=(95, 255, 255),
        description="Upper HSV bound (OpenCV scale: H 0-179, S/V 0-255)",
    )

    @model_validator(mode="after")
    def _validate_hsv_bounds(self) -> "BackgroundMaskConfig":
        """Reject out-of-range channels and lower bounds above their upper."""
        maxes = (_HUE_MAX, _CHANNEL_MAX, _CHANNEL_MAX)
        for name, bound in (
            ("lower_hsv", self.lower_hsv),
            ("upper_hsv", self.upper_hsv),
        ):
            for channel, value, hi in zip(("H", "S", "V"), bound, maxes, strict=True):
                if not 0 <= value <= hi:
                    msg = f"{name} {channel}={value} out of range [0, {hi}]"
                    raise InvalidHsvBoundsError(msg)
        for channel, lo, hi in zip(
            ("H", "S", "V"), self.lower_hsv, self.upper_hsv, strict=True
        ):
            if lo > hi:
                msg = f"lower_hsv {channel}={lo} exceeds upper_hsv {channel}={hi}"
                raise InvalidHsvBoundsError(msg)
        return self


class SheetPreprocessConfig(BaseModelKwargs):
    """Parameters for `Sheet.preprocess()`, previously hardcoded in `Sheet`.

    Defaults reproduce the historical preprocess behavior exactly, so an
    omitted `preprocess` field leaves existing sheets byte-identical.
    """

    blur_kernel_size: int = Field(
        default=21, description="Gaussian blur kernel size (odd)"
    )
    threshold: int = Field(default=130, description="Binary threshold value (0-255)")
    erosion_kernel_size: int = Field(default=3, description="Erosion kernel size")
    erosion_iterations: int = Field(default=2, description="Erosion iterations")
    dilation_kernel_size: int = Field(default=3, description="Dilation kernel size")
    dilation_iterations: int = Field(default=1, description="Dilation iterations")
    background_mask: BackgroundMaskConfig | None = Field(
        default=None,
        description="Optional HSV background-mask override; None keeps default path",
    )


class SheetArucoConfig(BaseModelKwargs):
    """Configuration for sheet processing using ArUco markers.

    Attributes:
        min_area: Minimum area for detected pieces.
        crop_margin: Pixels to crop after rectification. If None, computed from
            the detector/board settings.
        detector: `ArucoDetectorConfig` used to construct the detector.
        preprocess: `SheetPreprocessConfig` owning the `Sheet.preprocess`
            parameters, including the optional nested `background_mask` for
            background-colored boards.
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
    preprocess: SheetPreprocessConfig = Field(
        default_factory=SheetPreprocessConfig,
        description="Sheet preprocess parameters and optional background mask",
    )
    metadata_zone: MetadataZoneConfig | None = Field(
        default=None, description="QR strip and slot grid config"
    )
