"""Utils related to image processing."""

from pathlib import Path

import cv2
from cv2.typing import Rect
import matplotlib.pyplot as plt
import numpy as np


def load_image(file_path: Path) -> np.ndarray:
    """Loads an image from the specified file path.

    Args:
        file_path (Path): The path to the image file.

    Returns:
        np.ndarray: The loaded image.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    image = cv2.imread(str(file_path))
    if image is None:
        raise ValueError(f"Failed to load image from: {file_path}")
    return image


def display_image(image: np.ndarray, window_name: str = "Image") -> None:
    """Displays the given image in a window.

    Args:
        image (np.ndarray): The image to display.
        window_name (str): The name of the display window.
    """
    # resize down to max 1000px
    image_small = image
    max_dim = 1000
    if image.shape[0] > max_dim or image.shape[1] > max_dim:
        scale = max_dim / max(image.shape[0], image.shape[1])
        image_small = cv2.resize(image, None, fx=scale, fy=scale)
    cv2.imshow(window_name, image_small)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def show_image_mpl(image: np.ndarray) -> None:
    """Displays the given image using Matplotlib.

    Args:
        image (np.ndarray): The image to display.
    """

    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.axis("off")
    plt.show()


def save_image(image: np.ndarray, output_path: Path) -> None:
    """Saves the given image to the specified file path.

    Args:
        image (np.ndarray): The image to save.
        output_path (Path): The path where the image will be saved.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    success = cv2.imwrite(str(output_path), image)
    if not success:
        raise ValueError(f"Failed to save image to: {output_path}")


def draw_regions(
    image: np.ndarray,
    regions: list[Rect],
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """
    Draws bounding rectangles for regions on the given image.

    Args:
        image (np.ndarray): The original image on which to draw the rectangles.
        regions (list[tuple[int, int, int, int]]): A list of bounding rectangles representing regions.
        color (tuple[int, int, int]): The color of the rectangle (default is green in BGR).
        thickness (int): The thickness of the rectangle border (default is 2).

    Returns:
        np.ndarray: The image with the bounding rectangles drawn.
    """
    if image is None:
        raise ValueError("Input image is None.")

    # Create a copy of the image to draw on, preserving the original
    output_image = image.copy()

    # Draw each rectangle on the image
    for x, y, w, h in regions:
        cv2.rectangle(output_image, (x, y), (x + w, y + h), color, thickness)

    return output_image


def sort_rects(rects: list[Rect]) -> list[Rect]:
    """Sorts the list of rectangles based on the area.

    Args:
        list[Rect]: The list of rectangles to sort.

    Returns:
        list[Rect]: The sorted list of rectangles.
    """

    return sorted(rects, key=lambda rect: rect[2] * rect[3], reverse=True)


def flip_colors_bw(image: np.ndarray) -> np.ndarray:
    """Flips the colors of a black and white image.

    Args:
        image (np.ndarray): The input image.

    Returns:
        np.ndarray: The image with the colors flipped.
    """
    return cv2.bitwise_not(image)
