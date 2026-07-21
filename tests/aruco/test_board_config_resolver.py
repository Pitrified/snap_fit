"""Tests for board config resolution at ingest (phase 4)."""

from pathlib import Path
from typing import Literal

import pytest

from snap_fit.aruco import board_config_resolver
from snap_fit.aruco.board_config_resolver import BoardConfigNotFoundError
from snap_fit.aruco.board_config_resolver import derive_background_mask
from snap_fit.aruco.board_config_resolver import load_sheet_config_by_id
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig
from snap_fit.config.aruco.sheet_aruco_config import BackgroundMaskConfig
from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig


def _config_with_preset(
    preset: Literal["white", "green", "blue"],
    mask: BackgroundMaskConfig | None = None,
) -> SheetArucoConfig:
    """Build a SheetArucoConfig for a given board background preset."""
    config = SheetArucoConfig(
        detector=ArucoDetectorConfig(board=ArucoBoardConfig(background_preset=preset)),
    )
    if mask is not None:
        config.preprocess.background_mask = mask
    return config


class _FakePaths:
    """Minimal stand-in for SnapFitPaths with a redirected board folder."""

    def __init__(self, aruco_board_fol: Path) -> None:
        self.aruco_board_fol = aruco_board_fol


@pytest.fixture
def board_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the resolver's board folder to a temp directory."""
    monkeypatch.setattr(
        board_config_resolver,
        "get_snap_fit_paths",
        lambda: _FakePaths(tmp_path),
    )
    return tmp_path


def _write_config(
    board_root: Path, board_config_id: str, config: SheetArucoConfig
) -> None:
    """Save a SheetArucoConfig where the loader expects to find it."""
    folder = board_root / board_config_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{board_config_id}_SheetArucoConfig.json").write_text(
        config.model_dump_json()
    )


# --- derive_background_mask (Q12 precedence) -------------------------------


def test_derive_auto_enables_mask_for_green() -> None:
    """A green board with no explicit mask gets the mask enabled by default."""
    config = derive_background_mask(_config_with_preset("green"))
    mask = config.preprocess.background_mask
    assert mask is not None
    assert mask.enabled is True
    # Bounds come from the model defaults, which are tuned against real captures.
    assert mask.lower_hsv == BackgroundMaskConfig().lower_hsv
    assert mask.upper_hsv == BackgroundMaskConfig().upper_hsv


def test_derive_auto_enables_mask_for_blue() -> None:
    """Blue is a masked preset too."""
    config = derive_background_mask(_config_with_preset("blue"))
    assert config.preprocess.background_mask is not None
    assert config.preprocess.background_mask.enabled is True


def test_derive_leaves_white_disabled() -> None:
    """A white board keeps the default disabled (None) mask."""
    config = derive_background_mask(_config_with_preset("white"))
    assert config.preprocess.background_mask is None


def test_derive_respects_explicit_disable_on_green() -> None:
    """An explicit enabled=false wins even on a green board."""
    explicit = BackgroundMaskConfig(enabled=False)
    config = derive_background_mask(_config_with_preset("green", mask=explicit))
    assert config.preprocess.background_mask is explicit
    assert explicit.enabled is False


def test_derive_respects_explicit_enable_on_white() -> None:
    """An explicit enabled mask wins even on a white board."""
    explicit = BackgroundMaskConfig(enabled=True, mode="flatten_to_white")
    config = derive_background_mask(_config_with_preset("white", mask=explicit))
    assert config.preprocess.background_mask is explicit
    assert explicit.mode == "flatten_to_white"


# --- load_sheet_config_by_id ----------------------------------------------


def test_loader_hit_applies_derivation(board_root: Path) -> None:
    """Loading a saved green config with no mask returns it with the mask on."""
    _write_config(board_root, "greenboard", _config_with_preset("green"))
    loaded = load_sheet_config_by_id("greenboard")
    assert loaded.detector.board.background_preset == "green"
    assert loaded.preprocess.background_mask is not None
    assert loaded.preprocess.background_mask.enabled is True


def test_loader_preserves_explicit_disable(board_root: Path) -> None:
    """A saved green config that explicitly disabled the mask stays disabled."""
    config = _config_with_preset("green", mask=BackgroundMaskConfig(enabled=False))
    _write_config(board_root, "greenoff", config)
    loaded = load_sheet_config_by_id("greenoff")
    assert loaded.preprocess.background_mask is not None
    assert loaded.preprocess.background_mask.enabled is False


def test_loader_missing_id_raises(board_root: Path) -> None:
    """An unknown id raises the named exception for the driver to catch."""
    with pytest.raises(BoardConfigNotFoundError):
        load_sheet_config_by_id("does_not_exist")


def test_loader_missing_sheet_config_raises(board_root: Path) -> None:
    """A folder with only a board config (old layout) still raises."""
    (board_root / "oldboard").mkdir()
    (board_root / "oldboard" / "oldboard_ArucoBoardConfig.json").write_text("{}")
    with pytest.raises(BoardConfigNotFoundError):
        load_sheet_config_by_id("oldboard")
