# Some memos about getting started with SnapFit

1. generate an [aruco board](../scratch_space/aruco_setup/03_generate_aruco_board.ipynb)
   this will generate:
   - aruco board image (to be printed)
   - aruco board definition file (`_ArucoBoardConfig.json`)
2. take some pictures of pieces on the printed aruco board
3. load the sheets with a [SheetAruco](../scratch_space/aruco_setup/04_load_sheets.ipynb)
   - this will use the aruco board definition file to detect the aruco markers and set up the sheets
   - you can set some parameters for detection
   - will create the sheet config files (`_SheetArucoConfig.json`)
4. use the `SheetManager` to load the sheets and access pieces
   - sheet aruco has the loader function `sheet_aruco.load_sheet`
5. match two pieces using a `SegmentMatcher`
   - see [02_match_debug.ipynb](../scratch_space/contour_/02_match_debug.ipynb) for an example
6. match all pieces using a `PieceMatcher`
   - see [piece_matcher/02_usage.ipynb](../scratch_space/piece_matcher/02_usage.ipynb) for an example
   - this will cache the matches to volatile memory for faster access
7. `GridModel` is a model of the grid, has info about grid points, neighbors, slot types, orientations, etc
8. `PlacementState` links pieces to grid points, can check for validity of placements, etc
9. a solver like `NaiveLinearSolver` can build a placement state from matches
   - see [naive_linear_solver/02_usage.ipynb](../scratch_space/naive_linear_solver/02_usage.ipynb)
