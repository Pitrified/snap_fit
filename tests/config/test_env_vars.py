"""Test that the environment variables are available."""

import os


def test_env_vars() -> None:
    """The environment var SNAP_FIT_SAMPLE_ENV_VAR is available."""
    assert "SNAP_FIT_SAMPLE_ENV_VAR" in os.environ
    assert os.environ["SNAP_FIT_SAMPLE_ENV_VAR"] == "sample"
