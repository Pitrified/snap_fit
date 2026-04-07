# `aruco`

> Module: `src/snap_fit/aruco/`
> Related tests: `tests/aruco/`

## Purpose

ArUco marker detection and board generation for spatial calibration. Puzzle sheet photos include ArUco markers on the border to enable perspective correction (homography-based image rectification).

## Submodule Overview

| Module | Description |
|--------|-------------|
| [`detector`](detector.md) | Detects markers and applies perspective correction |
| [`board`](board.md) | Generates ring-layout ArUco boards |

## Usage

```python
from snap_fit.aruco.aruco_detector import ArucoDetector
from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig

config = ArucoDetectorConfig()
detector = ArucoDetector(config)

corners, ids, rejected = detector.detect_markers(image)
rectified = detector.rectify(image)
```

## Related Modules

- [`puzzle/sheet_aruco`](../puzzle/sheet_aruco.md) - high-level wrapper that uses `ArucoDetector`
- [`config`](../config/index.md) - ArUco config models (`ArucoBoardConfig`, `ArucoDetectorConfig`)
