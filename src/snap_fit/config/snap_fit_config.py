"""SnapFit project configuration."""

from pydantic import Field

from snap_fit.data_models.basemodel_kwargs import BaseModelKwargs


class SnapFitConfig(BaseModelKwargs):
    """SnapFit project configuration."""

    kwargs: dict = Field(default_factory=dict)
