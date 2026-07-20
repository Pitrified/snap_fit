"""Resolve a stored board config from a decoded board_config_id.

Drivers (notebooks, services) use these helpers to go from a QR-decoded
`board_config_id` to a fully resolved `SheetArucoConfig`, without `SheetAruco`
or `Sheet` ever touching JSON on disk (D14). The derivation helper applies the
Q12 precedence so a green/blue board auto-enables its background mask, while an
explicit `background_mask` in the config always wins.
"""

from pathlib import Path

from snap_fit.config.aruco.sheet_aruco_config import BackgroundMaskConfig
from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig
from snap_fit.params.snap_fit_params import get_snap_fit_paths

# Presets whose boards need the background mask enabled by default (Q12).
_MASKED_PRESETS = frozenset({"green", "blue"})


class BoardConfigNotFoundError(FileNotFoundError):
    """Raised when no stored SheetArucoConfig exists for a board_config_id."""


def board_config_dir(board_config_id: str) -> Path:
    """Return the on-disk folder for a board_config_id."""
    return get_snap_fit_paths().aruco_board_fol / board_config_id


def load_sheet_config_by_id(board_config_id: str) -> SheetArucoConfig:
    """Load the stored SheetArucoConfig for a decoded board_config_id.

    Applies the mask derivation (`derive_background_mask`) as a safety net so a
    green board whose saved config predates the auto-enable rule still ingests
    with the mask on.

    Args:
        board_config_id: The id decoded from the sheet QR metadata.

    Returns:
        The parsed `SheetArucoConfig` with the mask derivation applied.

    Raises:
        BoardConfigNotFoundError: If the folder or the config file is absent.
            Old board folders may hold only an `_ArucoBoardConfig.json`; the
            driver is expected to catch this and fall back.
    """
    config_path = (
        board_config_dir(board_config_id) / f"{board_config_id}_SheetArucoConfig.json"
    )
    if not config_path.is_file():
        msg = (
            f"No SheetArucoConfig for board_config_id {board_config_id!r} "
            f"at {config_path}"
        )
        raise BoardConfigNotFoundError(msg)
    config = SheetArucoConfig.model_validate_json(config_path.read_text())
    return derive_background_mask(config)


def derive_background_mask(config: SheetArucoConfig) -> SheetArucoConfig:
    """Apply the Q12 precedence: a masked preset auto-enables the mask.

    - An explicit `background_mask` (any `enabled` value) always wins and is
      left untouched, including an explicit `enabled=false` to force it off.
    - Otherwise a green/blue board preset enables the mask with default HSV
      bounds; a white preset leaves it disabled.

    Mutates `config.preprocess.background_mask` in place and returns `config`.
    Call it at config-build time before saving, and again when loading a config
    whose preset and mask might disagree.
    """
    if config.preprocess.background_mask is not None:
        return config
    preset = config.detector.board.background_preset
    if preset in _MASKED_PRESETS:
        config.preprocess.background_mask = BackgroundMaskConfig(enabled=True)
    return config
