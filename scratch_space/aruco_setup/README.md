# Use aruco markers to square the photos

## Experiments

... scratch_space/aruco_setup/01_aruco_experiments.ipynb

## Porting to snap_fit

### Overview

...

minimal feature, to be integrated if needed

1. Create aruco board generation utility in `src/snap_fit/aruco/aruco_board.py`
2. Create aruco detection and perspective correction utility in `src/snap_fit/aruco/aruco_detector.py`
3. Create SheetAruco that handles detection and correction in `src/snap_fit/puzzle/sheet_aruco.py`, which will then generate a Sheet from the corrected image, after removing the aruco markers border.

### Detailed plan

...
