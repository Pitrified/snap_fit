# `aruco/board`

> Module: `src/snap_fit/aruco/aruco_board.py`
> Related tests: `tests/aruco/`

## Purpose

Generates custom ArUco boards using a ring layout (markers only on the border, none in the interior). This layout maximizes the usable interior area for puzzle pieces while still providing enough reference points for perspective correction.

## Usage

### Minimal example

```python
from snap_fit.aruco.aruco_board import ArucoBoardGenerator
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig

config = ArucoBoardConfig(markers_x=5, markers_y=7, marker_length=100)
generator = ArucoBoardGenerator(config)

# Generate board image
board_image = generator.generate_image()
print(f"Board image shape: {board_image.shape}")

# Access the OpenCV Board object
board = generator.board
```

## API Reference

### `ArucoBoardGenerator`

Constructor: `ArucoBoardGenerator(config: ArucoBoardConfig)` - creates the ring board by filtering edge markers from a temporary full grid board.

| Attribute | Type | Description |
|-----------|------|-------------|
| `board` | `cv2.aruco.Board` | The OpenCV Board object for marker matching |
| `dictionary` | ArUco dictionary | The marker dictionary (default: `DICT_6X6_250`) |
| `config` | `ArucoBoardConfig` | Board configuration |

Method: `generate_image() -> np.ndarray` - renders the board as a numpy image.

### Ring layout

Instead of filling the entire grid with markers, only the border markers are kept. For a 5x7 grid, this produces 20 markers (perimeter) instead of 35 (full grid).

## Related Modules

- [`aruco/detector`](detector.md) - uses the board for marker matching during detection
- [`config`](../config/index.md) - `ArucoBoardConfig` defines marker count, size, and spacing
