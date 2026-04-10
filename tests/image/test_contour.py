"""Tests for Contour.centroid property."""

import numpy as np
import pytest

from snap_fit.image.contour import Contour


def _make_square_contour(x: int, y: int, size: int) -> Contour:
    """Return a Contour for a square with top-left at (x, y)."""
    pts = np.array(
        [
            [[x, y]],
            [[x + size, y]],
            [[x + size, y + size]],
            [[x, y + size]],
        ],
        dtype=np.int32,
    )
    return Contour(pts)


def _make_circle_contour(cx: int, cy: int, radius: int, n: int = 64) -> Contour:
    """Return a Contour approximating a circle."""
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pts = np.round(
        np.stack(
            [cx + radius * np.cos(angles), cy + radius * np.sin(angles)],
            axis=1,
        )
    ).astype(np.int32)
    return Contour(pts[:, np.newaxis, :])


def test_centroid_square() -> None:
    """Centroid of a square is at its geometric center."""
    contour = _make_square_contour(10, 20, 40)
    cx, cy = contour.centroid
    assert cx == pytest.approx(30, abs=2)
    assert cy == pytest.approx(40, abs=2)


def test_centroid_returns_ints() -> None:
    """Centroid coordinates are plain Python ints."""
    contour = _make_square_contour(0, 0, 100)
    cx, cy = contour.centroid
    assert isinstance(cx, int)
    assert isinstance(cy, int)


def test_centroid_circle() -> None:
    """Centroid of a circle approximation is near its centre."""
    contour = _make_circle_contour(200, 150, 50)
    cx, cy = contour.centroid
    assert cx == pytest.approx(200, abs=3)
    assert cy == pytest.approx(150, abs=3)


def test_centroid_degenerate_falls_back_to_bounding_rect() -> None:
    """Zero-area contour falls back to bounding rect centre without raising."""
    # A single-point contour has zero area - moments M00 == 0
    pts = np.array([[[50, 60]]], dtype=np.int32)
    contour = Contour(pts)
    cx, cy = contour.centroid
    # Should not raise and should return integers
    assert isinstance(cx, int)
    assert isinstance(cy, int)
