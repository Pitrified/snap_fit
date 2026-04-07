# `image`

> Module: `src/snap_fit/image/`
> Related tests: `tests/`

## Purpose

Computer vision primitives for contour extraction, segment splitting, shape classification, affine matching, and general image processing. This subpackage provides the low-level building blocks that the `puzzle` layer assembles into a pipeline.

## Submodule Overview

| Module | Description |
|--------|-------------|
| [`contour`](contour.md) | Wraps an OpenCV contour with corner matching and segment splitting |
| [`segment`](segment.md) | Represents one edge of a piece (between two corners) with shape classification |
| [`segment_matcher`](segment_matcher.md) | Affine-aligns two segments and computes similarity score |
| [`shape_detector`](shape_detector.md) | Classifies segments as IN/OUT/EDGE/WEIRD |
| [`process`](process.md) | Image preprocessing: grayscale, threshold, erosion, dilation, contour finding |

## Data Flow

```
Sheet photo
  -> process.py (grayscale, threshold, erode, dilate)
  -> process.find_contours() -> list[cv2 contour]
  -> Contour(cv_contour) -> .build_segments(corners)
  -> Segment(contour, start_idx, end_idx) -> .shape via ShapeDetector
  -> SegmentMatcher(seg1, seg2) -> .compute_similarity() -> float
```

## Related Modules

- [`puzzle/sheet`](../puzzle/sheet.md) - orchestrates the image processing pipeline
- [`puzzle/piece`](../puzzle/piece.md) - uses Contour and Segment for piece geometry
- [`config`](../config/index.md) - `SegmentShape` enum for shape classification results
