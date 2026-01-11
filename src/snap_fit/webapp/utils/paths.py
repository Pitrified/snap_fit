"""Path utilities for locating webapp resources.

Leverages the repository layout to return resource paths for the webapp.
"""

from pathlib import Path


def repo_root() -> Path:
    """Return the repository root directory."""
    # src/snap_fit/webapp/utils/paths.py -> repo root is 4 parents up
    return Path(__file__).resolve().parents[4]


def resource_path(*parts: str) -> Path:
    """Return an absolute path inside webapp_resources/."""
    return repo_root() / "webapp_resources" / Path(*parts)


def data_path(*parts: str) -> Path:
    """Return an absolute path inside data/."""
    return repo_root() / "data" / Path(*parts)


def static_path(*parts: str) -> Path:
    """Return an absolute path inside static/ at repo root."""
    return repo_root() / "static" / Path(*parts)


def cache_path(*parts: str) -> Path:
    """Return an absolute path inside cache/."""
    return repo_root() / "cache" / Path(*parts)
