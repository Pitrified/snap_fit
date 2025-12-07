# Use aruco markers to square the photos

## Experiments

scratch_space/aruco_setup/01_aruco_experiments.ipynb

## Porting to snap_fit

### Overview

1. Create aruco board generation utility in `src/snap_fit/aruco/aruco_board.py`
2. Create aruco detection and perspective correction utility in `src/snap_fit/aruco/aruco_detector.py`
3. Create SheetAruco that handles detection and correction in `src/snap_fit/puzzle/sheet_aruco.py`, which will then generate a Sheet from the corrected image, after removing the aruco markers border.

### Configuration Strategy

We need structured configuration for the Aruco components to ensure reproducibility and easy tuning.

**Location:** `src/snap_fit/config/aruco/`

**Models:**

1.  **`ArucoBoardConfig`** (in `aruco_board_config.py`)
    *   Inherits from: `BaseModelKwargs`
    *   Fields:
        *   `markers_x`: int
        *   `markers_y`: int
        *   `marker_length`: int
        *   `marker_separation`: int
        *   `dictionary_id`: int (cv2 constant)

2.  **`ArucoDetectorConfig`** (in `aruco_detector_config.py`)
    *   Inherits from: `BaseModelKwargs`
    *   Fields:
        *   `adaptiveThreshWinSizeMin`: int
        *   `adaptiveThreshWinSizeMax`: int
        *   `adaptiveThreshWinSizeStep`: int
        *   (And other relevant `cv2.aruco.DetectorParameters` fields we want to expose)
    *   Method: `to_detector_parameters() -> cv2.aruco.DetectorParameters`

### Detailed Plan

1.  [ ] **Define Config Models**
    *   Create `src/snap_fit/config/aruco/aruco_board_config.py`.
    *   Create `src/snap_fit/config/aruco/aruco_detector_config.py`.
    *   Implement `ArucoBoardConfig` and `ArucoDetectorConfig`.

2.  [ ] **Refactor ArucoBoardGenerator**
    *   Update `__init__` to accept `ArucoBoardConfig` (or keep kwargs but use config in higher levels).
    *   Ensure defaults match the config defaults.

3.  [ ] **Refactor ArucoDetector**
    *   Update `__init__` to accept `ArucoDetectorConfig`.
    *   Implement logic to convert `ArucoDetectorConfig` to `cv2.aruco.DetectorParameters`.

4.  [ ] **Implement SheetAruco**
    *   Create `src/snap_fit/puzzle/sheet_aruco.py`.
    *   Use the config models to initialize the generator and detector.
