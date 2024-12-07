"""Utils related to image processing."""

from pathlib import Path

import cv2
from cv2.typing import MatLike, Point, Rect, Scalar
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


def show_image_mpl(image: np.ndarray, figsize: tuple[int, int] = (10, 10)) -> None:
    """Displays the given image using Matplotlib.

    Args:
        image (np.ndarray): The image to display.
        figsize (tuple[int, int]): The size of the output plot (default is (10, 10)).
            Measured in inches.
    """
    plt.figure(figsize=figsize)
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


def compute_rect_area(rect: Rect) -> int:
    """Computes the area of a rectangle.

    Args:
        rect (Rect): The rectangle to compute the area for.

    Returns:
        int: The area of the rectangle.
    """
    return rect[2] * rect[3]


def compute_rects_area(rects: list[Rect]) -> list[int]:
    """Computes the area of multiple rectangles.

    Args:
        rects (list[Rect]): The list of rectangles to compute the area for.

    Returns:
        list[int]: The areas of the rectangles.
    """
    return [compute_rect_area(rect) for rect in rects]


def cut_rect_from_image(image: np.ndarray, rect: Rect) -> np.ndarray:
    """Cuts a rectangle from an image.

    Args:
        image (np.ndarray): The input image.
        rect (Rect): The rectangle to cut from the image.

    Returns:
        np.ndarray: The cut out region from the image.
    """
    x, y, w, h = rect
    return image[y : y + h, x : x + w]


def pad_rect(
    rect: Rect,
    padding: int,
    image: np.ndarray | None = None,
) -> Rect:
    """Pads a rectangle with additional pixels.

    If an image is provided, the function will check if the padding is valid and adjust it if necessary.

    Args:
        rect (Rect): The rectangle to pad.
        padding (int): The number of pixels to add to each side of the rectangle.

    Returns:
        Rect: The padded rectangle.
    """
    x, y, w, h = rect

    # Add padding to the rectangle
    x -= padding
    y -= padding
    w += 2 * padding
    h += 2 * padding

    # Ensure the padded rectangle is within the image bounds
    if image is not None:
        x = max(0, x)
        y = max(0, y)
        w = min(w, image.shape[1] - x)
        h = min(h, image.shape[0] - y)

    return x, y, w, h


def draw_corners(
    image: np.ndarray,
    corners: list[tuple[int, int]],
    color: tuple[int, ...] = (0, 255, 0),
    radius: int = 5,
) -> np.ndarray:
    """
    Draws circles at the detected corners on the given image.

    Args:
        image (np.ndarray): The original image to draw the corners on.
        corners (list[tuple[int, int]]): A list of corner coordinates as (x, y).
        color (tuple[int, int, int]): The color of the corners (default is green in BGR).
        radius (int): The radius of the circles to draw.

    Returns:
        np.ndarray: The image with corners drawn.
    """
    # Make a copy of the image to draw on
    output_image = image.copy()

    # Draw each corner as a circle
    for x, y in corners:
        cv2.circle(output_image, (x, y), radius, color, -1)

    return output_image


def draw_keypoints(
    image: np.ndarray,
    keypoints: list[cv2.KeyPoint],
    color: tuple[int, int, int] = (0, 255, 0),
) -> np.ndarray:
    """
    Draws keypoints on the given image.

    Args:
        image (np.ndarray): The original image to draw the keypoints on.
        keypoints (list[cv2.KeyPoint]): The detected keypoints.
        color (tuple[int, int, int]): The color of the keypoints (default is green in BGR).

    Returns:
        np.ndarray: The image with keypoints drawn.
    """
    return cv2.drawKeypoints(
        image, keypoints, None, color, cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
    )


def draw_contours(
    image: np.ndarray,
    contours: list[np.ndarray],
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """
    Draws contours on the given image.

    Args:
        image (np.ndarray): The original image to draw the contours on.
        contours (list[np.ndarray]): A list of contours, as returned by cv2.findContours.
        color (tuple[int, int, int]): The color of the contours (default is green in BGR).
        thickness (int): The thickness of the contour lines (default is 2).

    Returns:
        np.ndarray: The image with contours drawn.
    """
    if image is None:
        raise ValueError("Input image is None.")

    # Make a copy of the image to draw on
    output_image = image.copy()

    # Draw the contours on the image
    cv2.drawContours(output_image, contours, -1, color, thickness)

    return output_image


def draw_contour(
    image: np.ndarray,
    contour: np.ndarray,
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """
    Draws a single contour on the given image.

    Args:
        image (np.ndarray): The original image to draw the contour on.
        contour (np.ndarray): The contour to draw.
        color (tuple[int, int, int]): The color of the contour (default is green in BGR).
        thickness (int): The thickness of the contour line (default is 2).

    Returns:
        np.ndarray: The image with the contour drawn.
    """
    return cv2.drawContours(image, [contour], -1, color, thickness)


def translate_contour(contour: np.ndarray, x_offset: int, y_offset: int) -> np.ndarray:
    """
    Translates a contour by the specified x and y offsets.

    Args:
        contour (np.ndarray): The input contour, a NumPy array of shape (n, 1, 2).
        x_offset (int): The offset by which to translate the contour along the x-axis.
        y_offset (int): The offset by which to translate the contour along the y-axis.

    Returns:
        np.ndarray: The translated contour.
    """
    if contour is None or not len(contour):
        raise ValueError("Input contour is empty or None.")

    # Add the offsets to the contour points
    translation_matrix = np.array([[x_offset, y_offset]])
    translated_contour = contour + translation_matrix

    return translated_contour


def draw_contour_derivative(
    image: np.ndarray,
    contour: np.ndarray,
    derivative: np.ndarray,
    skip: int = 5,
    arrow_length: int = 5,
) -> np.ndarray:
    """
    Draws the derivative of a contour on the given image.

    Args:
        image (np.ndarray): The original image to draw the contour derivative on.
        contour (np.ndarray): The original contour.
        derivative (np.ndarray): The derivative of the contour.

    Returns:
        np.ndarray: The image with the contour derivative drawn.
    """
    if image is None:
        raise ValueError("Input image is None.")

    # Make a copy of the image to draw on
    output_image = image.copy()

    # Draw the original contour
    cv2.drawContours(output_image, [contour], -1, (0, 255, 0), 2)

    # Draw the derivative of the contour
    for i in range(len(contour)):
        # Skip some points to avoid clutter
        if i % skip != 0:
            continue
        x, y = contour[i][0]
        dx, dy = derivative[i][0]
        # make the arrow longer
        dx *= arrow_length
        dy *= arrow_length
        # draw the arrow
        cv2.arrowedLine(
            output_image,
            (x, y),
            (x + int(dx), y + int(dy)),
            (0, 0, 255),
            1,
        )

    return output_image


def draw_line(
    image: np.ndarray,
    pt1: Point,
    pt2: Point,
    color: int | Scalar,
    # color: Scalar,
    thickness: int = 0,
) -> MatLike:
    """Draws a line on the given image."""
    if isinstance(color, int):
        # check the shape of the image to determine the number of channels
        if len(image.shape) == 2:
            color = (color,)
        elif len(image.shape) == 3:
            color = (color, color, color)
        else:
            raise ValueError("Invalid image shape.")
    return cv2.line(image, pt1, pt2, color, thickness)
