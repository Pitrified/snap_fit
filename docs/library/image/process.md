# `image/process`

> Module: `src/snap_fit/image/process.py`
> Related tests: `tests/`

## Purpose

Collection of image processing functions wrapping OpenCV operations. Used by `Sheet` for preprocessing and by `SegmentMatcher`/`ShapeDetector` for affine transforms.

## Usage

### Preprocessing pipeline (as used by Sheet)

```python
from snap_fit.image.process import (
    apply_gaussian_blur,
    convert_to_grayscale,
    apply_threshold,
    apply_erosion,
    apply_dilation,
    find_contours,
)

image = apply_gaussian_blur(image, kernel_size=(21, 21))
image = convert_to_grayscale(image)
image = apply_threshold(image, threshold=130)
image = apply_erosion(image, kernel_size=3, iterations=2)
image = apply_dilation(image, kernel_size=3, iterations=1)
contours = find_contours(image)
```

### Affine transforms

```python
from snap_fit.image.process import estimate_affine_transform, transform_contour

matrix = estimate_affine_transform(source_coords, target_coords)
transformed = transform_contour(points, matrix)
```

## API Reference

Key functions:

| Function | Description |
|----------|-------------|
| `convert_to_grayscale(image)` | BGR to grayscale |
| `apply_threshold(image, threshold)` | Binary threshold |
| `apply_erosion(image, kernel_size, iterations)` | Morphological erosion |
| `apply_dilation(image, kernel_size, iterations)` | Morphological dilation |
| `find_contours(image)` | External contours from binary image |
| `find_white_regions(image)` | Bounding rects of white regions |
| `compute_bounding_rectangle(contour)` | Bounding rect for single contour |
| `find_corners(image, ...)` | Shi-Tomasi corner detection |
| `find_sift_keypoints(image)` | SIFT feature detection |
| `estimate_affine_transform(src, dst)` | 2x3 affine matrix |
| `transform_contour(points, matrix)` | Apply affine to contour points |

## Related Modules

- [`puzzle/sheet`](../puzzle/sheet.md) - uses preprocessing functions
- [`image/segment_matcher`](segment_matcher.md) - uses affine transform functions
- [`image/shape_detector`](shape_detector.md) - uses affine alignment for shape detection
