"""Test the snap_fit paths."""


from snap_fit.config.snap_fit_config import get_snap_fit_paths


def test_snap_fit_paths() -> None:
    """Test the snap_fit paths."""
    snap_fit_paths = get_snap_fit_paths()
    assert snap_fit_paths.src_fol.name == "snap_fit"
    assert snap_fit_paths.root_fol.name == "snap_fit"
    assert snap_fit_paths.data_fol.name == "data"
