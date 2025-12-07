"""Paths and folders for data files."""

from pathlib import Path

import snap_fit


class SnapFitPaths:
    """Paths and folders for data and resources."""

    def __init__(
        self,
    ) -> None:
        """Load the config for data folders."""
        self.load_config()

    def load_config(self) -> None:
        """Load the config for data folders."""
        self.load_common_config_pre()

    def load_common_config_pre(self) -> None:
        """Pre load the common config."""
        # src folder of the package
        self.src_fol = Path(snap_fit.__file__).parent
        # root folder of the project repository
        self.root_fol = self.src_fol.parents[1]
        # cache
        self.cache_fol = self.root_fol / "cache"
        # data
        self.data_fol = self.root_fol / "data"
        self.sample_img_fol = self.data_fol / "sample"
        # static
        self.static_fol = self.root_fol / "static"

    def __str__(self) -> str:
        """Get the string representation of the SnapFit paths."""
        s = "SnapFitPaths:\n"
        s += f"   src_fol: {self.src_fol}\n"
        s += f"  root_fol: {self.root_fol}\n"
        s += f" cache_fol: {self.cache_fol}\n"
        s += f"  data_fol: {self.data_fol}\n"
        s += f"static_fol: {self.static_fol}\n"
        return s
