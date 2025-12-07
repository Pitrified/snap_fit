"""SnapFit project params.

Parameters are actual value of the config.
"""

from loguru import logger as lg

from snap_fit.metaclasses.singleton import Singleton
from snap_fit.params.snap_fit_paths import SnapFitPaths


class SnapFitParams(metaclass=Singleton):
    """SnapFit project parameters."""

    def __init__(self) -> None:
        """Initialize the SnapFit params."""
        lg.info("Loading SnapFit params")
        self.paths = SnapFitPaths()

    def __str__(self) -> str:
        """Get the string representation of the SnapFit params."""
        s = "SnapFitParams:"
        s += f"\n{self.paths}"
        return s

    def __repr__(self) -> str:
        """Get the repr representation of the SnapFit params."""
        return str(self)


def get_snap_fit_params() -> SnapFitParams:
    """Get the snap_fit params."""
    return SnapFitParams()


def get_snap_fit_paths() -> SnapFitPaths:
    """Get the snap_fit paths."""
    return get_snap_fit_params().paths
