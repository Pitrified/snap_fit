"""Process images."""

from typing import Sequence

import cv2
from cv2.typing import MatLike, Rect
import numpy as np


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """Converts the given image to grayscale.

    Args:
        image (np.ndarray): The original image.

    Returns:
        np.ndarray: The grayscale image.
    """
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def apply_threshold(image: np.ndarray, threshold: int = 127) -> np.ndarray:
    """Applies a binary threshold to the image, converting it to black and white.

    Args:
        image (np.ndarray): The input image (assumed to be grayscale).
        threshold (int): The threshold value (0-255).

    Returns:
        np.ndarray: The thresholded image.
    """
    _, binary_image = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
    return binary_image


def apply_erosion(
    image: np.ndarray, kernel_size: int = 3, iterations: int = 1
) -> np.ndarray:
    """
    Applies erosion to the image.

    Args:
        image (np.ndarray): The input binary image.
        kernel_size (int): Size of the kernel (e.g., 3 for a 3x3 kernel).
        iterations (int): Number of erosion iterations.

    Returns:
        np.ndarray: The eroded image.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    return cv2.erode(image, kernel, iterations=iterations)


def apply_dilation(
    image: np.ndarray, kernel_size: int = 3, iterations: int = 1
) -> np.ndarray:
    """Applies dilation to the image.

    Args:
        image (np.ndarray): The input binary image.
        kernel_size (int): Size of the kernel (e.g., 3 for a 3x3 kernel).
        iterations (int): Number of dilation iterations.

    Returns:
        np.ndarray: The dilated image.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    return cv2.dilate(image, kernel, iterations=iterations)


def find_contours(image: np.ndarray) -> Sequence[MatLike]:
    """Finds contours in a binary image.

    Contours are white regions in the image.

    Args:
        image (np.ndarray): The input binary image (values should be 0 or 255).

    Returns:
        list[np.ndarray]: A list of contours found in the image.
    """
    if len(image.shape) != 2:
        # Ensure the image is binary (2D)
        # convert to grayscale if it is not
        image = convert_to_grayscale(image)

    # Find contours (white regions)
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return contours


def find_white_regions(image: np.ndarray) -> list[Rect]:
    """Finds white regions in a binary image.

    Args:
        image (np.ndarray): The input binary image (values should be 0 or 255).

    Returns:
        list[Rect]: A list of bounding rectangles for the white regions,
        where each rectangle is represented as (x, y, w, h).
    """
    contours = find_contours(image)

    # Compute bounding rectangles for each contour
    white_regions: list[Rect] = [cv2.boundingRect(contour) for contour in contours]

    return white_regions


def compute_bounding_rectangles(contours: Sequence[MatLike]) -> list[Rect]:
    """Computes bounding rectangles for the given contours.

    Args:
        image (np.ndarray): The original image.
        contours (list[np.ndarray]): A list of contours.

    Returns:
        list[Rect]: A list of bounding rectangles for the contours.
    """
    bounding_rectangles: list[Rect] = [
        cv2.boundingRect(contour) for contour in contours
    ]

    return bounding_rectangles


def find_corners(
    image: np.ndarray,
    max_corners: int = 100,
    quality_level: float = 0.01,
    min_distance: float = 10,
) -> list[tuple[int, int]]:
    """Finds corner keypoints in the given image using the Shi-Tomasi method.

    Args:
        image (np.ndarray): The input image, which should be grayscale.
        max_corners (int): The maximum number of corners to return.
        quality_level (float): The minimum quality of corners (0 to 1).
        min_distance (float): The minimum Euclidean distance between corners.

    Returns:
        list[tuple[int, int]]: A list of detected corner keypoints as (x, y) coordinates.
    """
    if len(image.shape) != 2:
        raise ValueError("Input image must be grayscale.")

    # Detect corners using cv2.goodFeaturesToTrack
    corners = cv2.goodFeaturesToTrack(
        image,
        maxCorners=max_corners,
        qualityLevel=quality_level,
        minDistance=min_distance,
    )

    if corners is not None:
        # Convert to a list of tuples
        return [(int(x), int(y)) for x, y in corners.reshape(-1, 2)]
    else:
        return []
