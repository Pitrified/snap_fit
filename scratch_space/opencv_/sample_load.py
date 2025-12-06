"""Sample code to load a raw image and apply thresholding, erosion, and dilation."""  # noqa: INP001

from snap_fit.config.snap_fit_config import get_snap_fit_paths
from snap_fit.image.process import apply_dilation
from snap_fit.image.process import apply_erosion
from snap_fit.image.process import apply_gaussian_blur
from snap_fit.image.process import apply_threshold
from snap_fit.image.process import convert_to_grayscale
from snap_fit.image.utils import display_image
from snap_fit.image.utils import load_image
from snap_fit.image.utils import save_image

if __name__ == "__main__":
    sf_paths = get_snap_fit_paths()
    data_fol = sf_paths.data_fol
    sample_fol = data_fol / "sample"
    # > img_fn = "PXL_20241130_105107220.jpg"
    # > img_fn = "front_01.jpg"
    img_fn = "back_01.jpg"
    # > img_fn = "back_02.jpg"
    # > img_fn = "puzzle_pieces_01.jpeg"
    img_fp = sample_fol / img_fn

    # load original image
    image = load_image(img_fp)
    display_image(image, "Original Image")

    # blur image - gaussian blur
    # > ks = 51  # amazing results
    ks = 21  # darn good results
    # TODO: do we have configs of these preprocessing steps?
    image = apply_gaussian_blur(image, kernel_size=(ks, ks))
    display_image(image, "Blurred Image")

    # # blur image - bilateral filter
    # > d = 50
    # > image = apply_bilateral_filter(image, diameter=d)
    # > display_image(image, "Blurred Image")

    # convert to grayscale
    image = convert_to_grayscale(image)

    # apply thresholding
    threshold = 130
    image = apply_threshold(image, threshold)
    display_image(image, "Black and White Image")

    # apply erosion and dilation
    image = apply_erosion(image, kernel_size=3, iterations=2)
    display_image(image, "Eroded Image")
    image = apply_dilation(image, kernel_size=3, iterations=1)
    display_image(image, "Dilated Image")

    # save the output image
    output_fp = sample_fol / "output" / f"{img_fn}"
    save_image(image, output_fp)
