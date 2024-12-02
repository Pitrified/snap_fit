"""Sample code to load a raw image and apply thresholding, erosion, and dilation."""

from snap_fit.config.snap_fit_config import get_snap_fit_paths
from snap_fit.image.process import (
    apply_dilation,
    apply_erosion,
    apply_threshold,
    convert_to_grayscale,
)
from snap_fit.image.utils import display_image, load_image, save_image

if __name__ == "__main__":
    sf_paths = get_snap_fit_paths()
    data_fol = sf_paths.data_fol
    sample_fol = data_fol / "sample"
    # img_fn = "PXL_20241130_105107220.jpg"
    # img_fn = "front_01.jpg"
    img_fn = "back_02.jpg"
    # img_fn = "puzzle_pieces_01.jpeg"
    img_fp = sample_fol / img_fn

    original_image = load_image(img_fp)
    display_image(original_image, "Original Image")

    gray_image = convert_to_grayscale(original_image)
    # display_image(gray_image, "Grayscale Image")

    threshold = 130
    binary_image = apply_threshold(gray_image, threshold)
    display_image(binary_image, "Black and White Image")

    eroded_image = apply_erosion(binary_image, kernel_size=3, iterations=2)
    display_image(eroded_image, "Eroded Image")

    dilated_image = apply_dilation(eroded_image, kernel_size=3, iterations=1)
    display_image(dilated_image, "Dilated Image")

    output_fp = sample_fol / "output" / f"{img_fn}"
    save_image(dilated_image, output_fp)
