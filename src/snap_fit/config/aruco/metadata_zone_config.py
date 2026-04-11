"""Config models for the QR metadata strip and slot grid on board images."""

from typing import Literal

from pydantic import Field

from snap_fit.utils.basemodel_kwargs import BaseModelKwargs


class SlotGridConfig(BaseModelKwargs):
    """Defines a grid of piece slots within the board interior.

    Attributes:
        cols: Number of slot columns.
        rows: Number of slot rows.
        label_inset_px: Pixel inset from slot top-left corner for label text.
    """

    cols: int = Field(default=8)
    rows: int = Field(default=6)
    label_inset_px: int = Field(default=4)


class MetadataZoneConfig(BaseModelKwargs):
    """Controls the QR strip and slot grid on generated board images.

    Attributes:
        enabled: When False the zone is skipped entirely.
        qr_n_codes: Number of identical QR codes to render in the strip.
        qr_ecc: QR error-correction level.
        text_enabled: Whether to render a human-readable text line.
        slot_grid: Slot grid parameters.
    """

    enabled: bool = True
    qr_n_codes: int = 3
    qr_ecc: Literal["L", "M", "Q", "H"] = "M"
    text_enabled: bool = True
    slot_grid: SlotGridConfig = Field(default_factory=SlotGridConfig)
