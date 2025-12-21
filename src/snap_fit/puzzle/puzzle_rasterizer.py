"""Puzzle rasterization using cairosvg."""

import re

import cairosvg
import cv2
from loguru import logger as lg
import numpy as np

# Image channel constants
RGBA_CHANNELS = 4
RGB_CHANNELS = 3


class PuzzleRasterizer:
    """Rasterizes SVG puzzles to numpy arrays."""

    def __init__(self, dpi: int = 300) -> None:
        """Initialize the rasterizer.

        Args:
            dpi: Dots per inch for rasterization.
        """
        self.dpi = dpi
        # Conversion factor: 1 inch = 25.4 mm
        self.scale = dpi / 25.4  # pixels per mm

    def rasterize(self, svg: str, *, background_color: str = "white") -> np.ndarray:
        """Rasterize an SVG string to a numpy array.

        Args:
            svg: SVG string.
            background_color: Background color for the image.

        Returns:
            BGR numpy array (OpenCV format).
        """
        # Parse SVG to get dimensions
        # The SVG should have width and height in mm
        width_match = re.search(r'width="([\d.]+)mm"', svg)
        height_match = re.search(r'height="([\d.]+)mm"', svg)

        if width_match and height_match:
            width_mm = float(width_match.group(1))
            height_mm = float(height_match.group(1))
            output_width = int(width_mm * self.scale)
            output_height = int(height_mm * self.scale)
        else:
            # Fallback to default size
            output_width = None
            output_height = None

        # Add background to SVG if needed
        if background_color != "transparent":
            svg = self._add_background(svg, background_color)

        # Convert SVG to PNG bytes
        png_result = cairosvg.svg2png(
            bytestring=svg.encode("utf-8"),
            output_width=output_width,
            output_height=output_height,
        )
        if png_result is None:
            msg = "cairosvg.svg2png returned None"
            raise ValueError(msg)
        png_bytes: bytes = png_result

        # Convert PNG bytes to numpy array
        nparr = np.frombuffer(png_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        # Convert RGBA to BGR if needed
        if img is None:
            msg = "Failed to decode PNG image"
            raise ValueError(msg)

        if img.shape[2] == RGBA_CHANNELS:
            # Composite alpha onto white background
            alpha = img[:, :, 3:4] / 255.0
            rgb = img[:, :, :3]
            bg = np.ones_like(rgb) * 255
            img = (rgb * alpha + bg * (1 - alpha)).astype(np.uint8)

        # Convert RGB to BGR for OpenCV
        if len(img.shape) == RGB_CHANNELS and img.shape[2] == RGB_CHANNELS:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        return img

    def _add_background(self, svg: str, color: str) -> str:
        """Add a background rectangle to the SVG."""
        # Find the viewBox or dimensions
        viewbox_match = re.search(r'viewBox="([^"]+)"', svg)
        if viewbox_match:
            viewbox = viewbox_match.group(1)
            parts = viewbox.split()
            x, y, w, h = parts[0], parts[1], parts[2], parts[3]
            bg_rect = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>'
        else:
            # Try width/height
            width_match = re.search(r'width="([\d.]+)', svg)
            height_match = re.search(r'height="([\d.]+)', svg)
            if width_match and height_match:
                w = width_match.group(1)
                h = height_match.group(1)
                bg_rect = f'<rect x="0" y="0" width="{w}" height="{h}" fill="{color}"/>'
            else:
                return svg

        # Insert background after opening svg tag
        insert_pos = svg.find(">") + 1
        return svg[:insert_pos] + bg_rect + svg[insert_pos:]

    def save(self, img: np.ndarray, filepath: str) -> None:
        """Save a rasterized image to file.

        Args:
            img: BGR numpy array.
            filepath: Output file path.
        """
        cv2.imwrite(filepath, img)
        lg.info(f"Saved rasterized image to {filepath}")
