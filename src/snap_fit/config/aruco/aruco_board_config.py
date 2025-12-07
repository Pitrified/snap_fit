"""Configuration for Aruco board generation."""

import cv2
from pydantic import Field

from snap_fit.data_models.basemodel_kwargs import BaseModelKwargs


class ArucoBoardConfig(BaseModelKwargs):
    """Configuration for Aruco board generation."""

    markers_x: int = Field(5, description="Number of markers in X direction")
    markers_y: int = Field(7, description="Number of markers in Y direction")
    marker_length: int = Field(100, description="Length of the marker side in pixels")
    marker_separation: int = Field(
        100, description="Separation between markers in pixels"
    )
    dictionary_id: int = Field(
        cv2.aruco.DICT_6X6_250, description="ArUco dictionary ID"
    )
    margin: int = Field(20, description="Margin around the board in pixels")
    border_bits: int = Field(1, description="Number of bits for the marker border")
