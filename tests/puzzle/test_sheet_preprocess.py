"""Tests for Sheet.preprocess and the optional HSV background mask (phase 3)."""

from pathlib import Path

import cv2
import numpy as np

from snap_fit.config.aruco.sheet_aruco_config import BackgroundMaskConfig
from snap_fit.config.aruco.sheet_aruco_config import SheetPreprocessConfig
from snap_fit.image.process import apply_dilation
from snap_fit.image.process import apply_erosion
from snap_fit.image.process import apply_gaussian_blur
from snap_fit.image.process import apply_threshold
from snap_fit.image.process import convert_to_grayscale
from snap_fit.image.utils import flip_colors_bw
from snap_fit.puzzle.sheet import Sheet

_GREEN_BGR = (0, 255, 0)
_RED_BGR = (0, 0, 255)
_DUMMY_FP = Path("synthetic_sheet.png")


def _baseline_img_bw(image: np.ndarray) -> np.ndarray:
    """Reproduce the historical hardcoded preprocess pipeline."""
    blurred = apply_gaussian_blur(image, kernel_size=(21, 21))
    gray = convert_to_grayscale(blurred)
    binary = apply_threshold(gray, threshold=130)
    binary = apply_erosion(binary, kernel_size=3, iterations=2)
    binary = apply_dilation(binary, kernel_size=3, iterations=1)
    return flip_colors_bw(binary)


def _white_bg_with_dark_blob() -> np.ndarray:
    """White canvas with a dark centered blob (a classic piece-on-white).

    A filled circle is used instead of a square: a rectangular contour has four
    flat edges, which the piece-type derivation in `find_pieces` rejects.
    """
    canvas = np.full((200, 200, 3), 255, dtype=np.uint8)
    cv2.circle(canvas, (100, 100), 40, (40, 40, 40), thickness=-1)
    return canvas


def _green_bg_with_red_blob() -> np.ndarray:
    """Green canvas with a red centered blob (a piece on a green board)."""
    canvas = np.full((200, 200, 3), _GREEN_BGR, dtype=np.uint8)
    cv2.circle(canvas, (100, 100), 40, _RED_BGR, thickness=-1)
    return canvas


def test_disabled_mask_matches_baseline() -> None:
    """Default preprocess is byte-identical to the historical pipeline."""
    image = _white_bg_with_dark_blob()
    sheet = Sheet(img_fp=_DUMMY_FP, min_area=0, image=image)
    assert np.array_equal(sheet.img_bw, _baseline_img_bw(image))


def test_as_threshold_mask_extracts_piece_on_green() -> None:
    """as_threshold turns green into background and keeps the red piece."""
    image = _green_bg_with_red_blob()
    cfg = SheetPreprocessConfig(
        background_mask=BackgroundMaskConfig(enabled=True, mode="as_threshold")
    )
    sheet = Sheet(img_fp=_DUMMY_FP, min_area=0, image=image, preprocess=cfg)

    # In img_bw, foreground pieces are white (255), background is black (0).
    assert sheet.img_bw[100, 100] == 255  # piece center
    assert sheet.img_bw[10, 10] == 0  # green background corner


def test_flatten_to_white_mask_extracts_piece_on_green() -> None:
    """flatten_to_white paints green white, then the normal path finds the piece."""
    image = _green_bg_with_red_blob()
    cfg = SheetPreprocessConfig(
        background_mask=BackgroundMaskConfig(enabled=True, mode="flatten_to_white")
    )
    sheet = Sheet(img_fp=_DUMMY_FP, min_area=0, image=image, preprocess=cfg)

    assert sheet.img_bw[100, 100] == 255  # piece center
    assert sheet.img_bw[10, 10] == 0  # green background corner


def test_flatten_to_white_is_baseline_on_white_frame() -> None:
    """With no green to repaint, flatten_to_white equals the baseline output."""
    image = _white_bg_with_dark_blob()
    cfg = SheetPreprocessConfig(
        background_mask=BackgroundMaskConfig(enabled=True, mode="flatten_to_white")
    )
    sheet = Sheet(img_fp=_DUMMY_FP, min_area=0, image=image, preprocess=cfg)
    assert np.array_equal(sheet.img_bw, _baseline_img_bw(image))


def _hsv_to_bgr(h: int, s: int, v: int) -> tuple[int, int, int]:
    """Convert a single OpenCV-scale HSV triple to a BGR tuple."""
    px = np.array([[[h, s, v]]], dtype=np.uint8)
    b, g, r = cv2.cvtColor(px, cv2.COLOR_HSV2BGR)[0, 0]
    return (int(b), int(g), int(r))


def test_glare_lit_piece_survives_default_bounds() -> None:
    """A piece sharing the background hue but darker stays foreground.

    Regression for the greendemo captures: pieces lit by reflected board light
    read H~75 S~100 V~60, the same hue as the V~200 background. The default
    value floor must exclude them, or the mask erodes the pieces away.
    """
    background = _hsv_to_bgr(80, 245, 200)
    glare_lit_piece = _hsv_to_bgr(75, 100, 60)

    canvas = np.full((200, 200, 3), background, dtype=np.uint8)
    cv2.circle(canvas, (100, 100), 40, glare_lit_piece, thickness=-1)

    cfg = SheetPreprocessConfig(
        background_mask=BackgroundMaskConfig(enabled=True, mode="as_threshold")
    )
    sheet = Sheet(img_fp=_DUMMY_FP, min_area=0, image=canvas, preprocess=cfg)

    assert sheet.img_bw[100, 100] == 255  # piece center stays foreground
    assert sheet.img_bw[10, 10] == 0  # bright background stays background


def test_disabled_flag_ignores_mask_config() -> None:
    """A present-but-disabled mask leaves the default pipeline untouched."""
    image = _white_bg_with_dark_blob()
    cfg = SheetPreprocessConfig(
        background_mask=BackgroundMaskConfig(enabled=False, mode="as_threshold")
    )
    sheet = Sheet(img_fp=_DUMMY_FP, min_area=0, image=image, preprocess=cfg)
    assert np.array_equal(sheet.img_bw, _baseline_img_bw(image))
