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
| `board_image_composer` | Composes the printable/displayable board: ring, background preset, slot labels, QR strip |
| `sheet_metadata` | Encodes and decodes the per-sheet QR identity payload |
| `slot_grid` | Computes slot centers and labels (`A1`, `B3`, ...) inside the ring |
| `board_config_resolver` | Resolves a decoded `board_config_id` to the stored ingest config on disk |

## Usage

```python
from snap_fit.aruco.aruco_detector import ArucoDetector
from snap_fit.config.aruco.aruco_detector_config import ArucoDetectorConfig

config = ArucoDetectorConfig()
detector = ArucoDetector(config)

corners, ids, rejected = detector.detect_markers(image)
rectified = detector.rectify(image)
```

### Resolving a board config from a photo

`board_config_resolver` closes the loop between a photographed sheet and the config it was
rendered with, so an ingest driver never rebuilds a config by hand:

```python
from snap_fit.aruco.board_config_resolver import load_sheet_config_by_id
from snap_fit.aruco.sheet_metadata import SheetMetadataDecoder

metadata = SheetMetadataDecoder().decode(image)
config = load_sheet_config_by_id(metadata.board_config_id)
```

It reads `data/aruco_boards/{id}/{id}_SheetArucoConfig.json`, raises `BoardConfigNotFoundError`
when a board folder has no stored ingest config, and applies `derive_background_mask()` so a
green or blue board cannot be ingested with its mask accidentally off.

## Related Modules

- [`puzzle/sheet_aruco`](../puzzle/sheet_aruco.md) - high-level wrapper that uses `ArucoDetector`
- [`config`](../config/index.md) - ArUco config models (`ArucoBoardConfig`, `ArucoDetectorConfig`)
- [Green background boards](../../guides/green_background.md) - colored-board capture workflow
