"""Utils related to image processing."""

from collections.abc import Sequence
from pathlib import Path

import cv2
from cv2.typing import MatLike
from cv2.typing import Point
from cv2.typing import Rect
from cv2.typing import Scalar
import matplotlib.pyplot as plt
import numpy as np

from snap_fit.config.types import CornerPos


def load_image(file_path: Path) -> np.ndarray:
    """Load an image from the specified file path.

    Args:
        file_path (Path): The path to the image file.

    Returns:
        np.ndarray: The loaded image.
    """
    if not file_path.exists():
        msg = f"File not found: {file_path}"
        raise FileNotFoundError(msg)
    image = cv2.imread(str(file_path))
    if image is None:
        msg = f"Failed to load image from: {file_path}"
        raise ValueError(msg)
    return image


def display_image(image: np.ndarray, window_name: str = "Image") -> None:
    """Display the given image in a window.

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
    """Display the given image using Matplotlib.

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
    """Save the given image to the specified file path.

    Args:
        image (np.ndarray): The image to save.
        output_path (Path): The path where the image will be saved.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    success = cv2.imwrite(str(output_path), image)
    if not success:
        msg = f"Failed to save image to: {output_path}"
        raise ValueError(msg)


def draw_regions(
    image: np.ndarray,
    regions: list[Rect],
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """Draws bounding rectangles for regions on the given image.

    Args:
        image (np.ndarray): The original image on which to draw the rectangles.
        regions (list[Rect]): A list of bounding rectangles representing regions.
        color (tuple[int, int, int]): The color of the rectangle.
            Default is green in BGR.
        thickness (int): The thickness of the rectangle border (default is 2).

    Returns:
        np.ndarray: The image with the bounding rectangles drawn.
    """
    if image is None:
        msg = "Input image is None."
        raise ValueError(msg)

    # Create a copy of the image to draw on, preserving the original
    output_image = image.copy()

    # Draw each rectangle on the image
    for x, y, w, h in regions:
        cv2.rectangle(output_image, (x, y), (x + w, y + h), color, thickness)

    return output_image


def sort_rects(rects: list[Rect]) -> list[Rect]:
    """Sorts the list of rectangles based on the area.

    Args:
        rects (list[Rect]): The list of rectangles to sort.

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
    """Compute the area of a rectangle.

    Args:
        rect (Rect): The rectangle to compute the area for.

    Returns:
        int: The area of the rectangle.
    """
    return rect[2] * rect[3]


def compute_rects_area(rects: list[Rect]) -> list[int]:
    """Compute the area of multiple rectangles.

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
    """Pad a rectangle with additional pixels.

    If an image is provided, the function will check if the padding is valid and
    adjust it if necessary.

    Args:
        rect (Rect): The rectangle to pad.
        padding (int): The number of pixels to add to each side of the rectangle.
        image (np.ndarray | None): The image to check the padding against.

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
    color: int | tuple[int, ...] = (0, 255, 0),
    radius: int = 5,
) -> np.ndarray:
    """Draws circles at the detected corners on the given image.

    Args:
        image (np.ndarray): The original image to draw the corners on.
        corners (list[tuple[int, int]]): A list of corner coordinates as (x, y).
        color (tuple[int, int, int]): The color of the corners.
            Default is green in BGR.
        radius (int): The radius of the circles to draw.

    Returns:
        np.ndarray: The image with corners drawn.
    """
    # Make a copy of the image to draw on
    output_image = image.copy()

    cs = color_to_scalar(color, image)

    # Draw each corner as a circle
    for x, y in corners:
        cv2.circle(output_image, (x, y), radius, cs, -1)

    return output_image


def draw_keypoints(
    image: MatLike,
    keypoints: list[cv2.KeyPoint],
    color: tuple[int, int, int] = (0, 255, 0),
) -> np.ndarray:
    """Draws keypoints on the given image.

    Args:
        image (np.ndarray): The original image to draw the keypoints on.
        keypoints (list[cv2.KeyPoint]): The detected keypoints.
        color (tuple[int, int, int]): The color of the keypoints.
            Default is green in BGR.

    Returns:
        np.ndarray: The image with keypoints drawn.
    """
    return cv2.drawKeypoints(
        image,
        keypoints,
        image,
        color,
        cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
    )


def draw_contours(
    image: np.ndarray,
    # contours: list[np.ndarray],
    contours: Sequence[MatLike],
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """Draws contours on the given image.

    Args:
        image (np.ndarray): The original image to draw the contours on.
        contours (Sequence[MatLike]): List of contours, as returned by cv2.findContours.
        color (tuple[int, int, int]): The color of the contours.
            Default is green in BGR.
        thickness (int): The thickness of the contour lines (default is 2).

    Returns:
        np.ndarray: The image with contours drawn.
    """
    if image is None:
        msg = "Input image is None."
        raise ValueError(msg)

    # Make a copy of the image to draw on
    output_image = image.copy()

    # Draw the contours on the image
    cv2.drawContours(output_image, contours, -1, color, thickness)

    return output_image


def draw_contour(
    image: np.ndarray,
    contour: np.ndarray,
    color: int | tuple[int, ...] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """Draws a single contour on the given image.

    Args:
        image (np.ndarray): The original image to draw the contour on.
        contour (np.ndarray): The contour to draw.
        color (tuple[int, int, int]): The color of the contour.
            Default is green in BGR.
        thickness (int): The thickness of the contour line (default is 2).

    Returns:
        np.ndarray: The image with the contour drawn.
    """
    cs = color_to_scalar(color, image)
    return cv2.drawContours(image, [contour], -1, cs, thickness)


def translate_contour(contour: np.ndarray, x_offset: int, y_offset: int) -> np.ndarray:
    """Translate a contour by the specified x and y offsets.

    Args:
        contour (np.ndarray): The input contour, a NumPy array of shape (n, 1, 2).
        x_offset (int): The offset by which to translate the contour along the x-axis.
        y_offset (int): The offset by which to translate the contour along the y-axis.

    Returns:
        np.ndarray: The translated contour.
    """
    if contour is None or not len(contour):
        msg = "Input contour is empty or None."
        raise ValueError(msg)

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
    """Draws the derivative of a contour on the given image.

    Args:
        image (np.ndarray): The original image to draw the contour derivative on.
        contour (np.ndarray): The original contour.
        derivative (np.ndarray): The derivative of the contour.
        skip (int): The number of points to skip when drawing arrows.
            Default is 5.
        arrow_length (int): The length of the arrows to draw.
            Default is 5.

    Returns:
        np.ndarray: The image with the contour derivative drawn.
    """
    if image is None:
        msg = "Input image is None."
        raise ValueError(msg)

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
    # TODO: move to a more general utils func get_scalar_from_color
    if isinstance(color, int):
        # check the shape of the image to determine the number of channels
        if len(image.shape) == 2:  # noqa: PLR2004
            color = (color,)
        elif len(image.shape) == 3:  # noqa: PLR2004
            color = (color, color, color)
        else:
            msg = "Invalid image shape."
            raise ValueError(msg)
    return cv2.line(image, pt1, pt2, color, thickness)


def color_to_scalar(
    color: int | tuple[int, ...],
    ref_image: np.ndarray | None = None,
    num_channels: int | None = None,
) -> Scalar:
    """Convert a color tuple to a Scalar."""
    # if a color tuple is provided, return it
    if not isinstance(color, int):
        return color
    # check that a reference image or number of channels is provided
    if ref_image is None and num_channels is None:
        msg = "Either a reference image or number of channels must be provided."
        raise ValueError(msg)

    # if we had no channels, the reference image is used
    if num_channels is None:
        match ref_image.shape:  # type: ignore (the ref image cannot be none)
            case (_h, _w):
                num_channels = 1
            case (_h, _w, c):
                num_channels = c
            case _:
                msg = "Invalid image shape."
                raise ValueError(msg)

    # determine if the color should be triplicated
    match num_channels:
        case 1:
            triplicate = False
        case 3:
            triplicate = True
        case _:
            msg = "Invalid number of channels."
            raise ValueError(msg)

    # convert the color to a scalar
    if triplicate:
        return (color, color, color)
    return (color,)


def find_corner(
    img_crossmasked: np.ndarray,
    which_corner: CornerPos,
) -> tuple[int, int]:
    """Find the corner of the piece by sweeping the image.

    The function sweeps the image with a line starting from the corner,
    orthogonal to the diagonal of the image, and stops when the line hits the
    crossmasked image.
    The corner is then the point where the line hits the crossmasked image.

    Args:
        img_crossmasked (np.ndarray): The image with the diagonal line.
        which_corner (str): The corner to find, one of
            "top_left", "top_right", "bottom_left", "bottom_right".

    Returns:
        tuple: The coordinates of the corner, as a tuple (x, y).
    """
    shap = img_crossmasked.shape
    for i in range(min(shap)):
        for j in range(i):
            match which_corner:
                case CornerPos.TOP_LEFT:
                    x = j
                    y = i - j
                case CornerPos.BOTTOM_LEFT:
                    x = i - j
                    y = shap[0] - j - 1
                case CornerPos.TOP_RIGHT:
                    x = shap[1] - i + j
                    y = j
                case CornerPos.BOTTOM_RIGHT:
                    x = shap[1] - j - 1
                    y = shap[0] - i + j
                case _:
                    msg = f"Invalid corner {which_corner=}"
                    raise ValueError(msg)
            if img_crossmasked[y, x] > 0:
                return (x, y)
    return (0, 0)
