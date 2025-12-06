"""SnapFit project configuration."""

from loguru import logger as lg

from snap_fit.config.singleton import Singleton
from snap_fit.config.snap_fit_paths import SnapFitPaths


class SnapFitConfig(metaclass=Singleton):
    """SnapFit project configuration."""

    def __init__(self) -> None:
        """Initialize the SnapFit config."""
        lg.info("Loading SnapFit config")
        self.paths = SnapFitPaths()

    def __str__(self) -> str:
        """Get the string representation of the SnapFit config."""
        s = "SnapFitConfig:"
        s += f"\n{self.paths}"
        return s

    def __repr__(self) -> str:
        """Get the repr representation of the SnapFit config."""
        return str(self)


def get_snap_fit_config() -> SnapFitConfig:
    """Get the snap_fit config."""
    return SnapFitConfig()


def get_snap_fit_paths() -> SnapFitPaths:
    """Get the snap_fit paths."""
    return get_snap_fit_config().paths
