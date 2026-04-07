# `aruco/detector`

> Module: `src/snap_fit/aruco/aruco_detector.py`
> Related tests: `tests/aruco/`

## Purpose

Detects ArUco markers in images and corrects perspective distortion. Uses a ring-layout ArUco board for reference points and computes a homography to warp the image into a rectified, orthographic view.

## Usage

### Minimal example

```python
from snap_fit.aruco.aruco_detector import ArucoDetector
from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig

config = ArucoDetectorConfig()
detector = ArucoDetector(config)

# Detect markers
corners, ids, rejected = detector.detect_markers(image)

# Full rectification pipeline
rectified = detector.rectify(image)
if rectified is not None:
    print(f"Rectified to {rectified.shape}")
else:
    print("Rectification failed")
```

## API Reference

### `ArucoDetector`

Constructor: `ArucoDetector(config: ArucoDetectorConfig)` - builds the detector parameters and board from config.

| Method | Returns | Description |
|--------|---------|-------------|
| `detect_markers(image)` | `(corners, ids, rejected)` | Detect ArUco markers |
| `correct_perspective(image, corners, ids)` | `np.ndarray \| None` | Warp image using detected markers |
| `rectify(image)` | `np.ndarray \| None` | Detect + correct in one call |

The `correct_perspective` method requires at least 4 matched points. It computes a homography mapping detected marker corners to their known board positions.

## Common Pitfalls

- **Returns None on failure**: Both `correct_perspective` and `rectify` return `None` if markers cannot be detected or there are insufficient points. Always check the return value.
- **Green border**: The warped image uses green `(0, 255, 0)` as the border fill. Areas outside the rectified region will be green.

## Related Modules

- [`aruco/board`](board.md) - generates the reference board
- [`puzzle/sheet_aruco`](../puzzle/sheet_aruco.md) - wraps this into a sheet-loading pipeline
- [`config`](../config/index.md) - `ArucoDetectorConfig` with threshold and margin parameters
