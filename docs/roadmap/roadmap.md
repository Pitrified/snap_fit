# Roadmap

## IDEAs

### Scale invariant pictures (done ✅)

We should create scale invariant pictures by adding a ruler to the image.
Or a bunch of qr codes of known size and position.
This will help with the calibration of the images.

### OCR for piece labels (planned 📋)

Extract text
some UI to check it?

### SheetLoader ABC (SheetAruco.load_sheet) (planned 📋)

Define ABC for sheet loading
SheetAruco could implement it
Let SheetManager accept that

### SheetManager getters (done ✅)

Get a list of segment ids available in this manager (sheet.piece.edge)
Given a segment id, get

- segment
- piece
- segment from other pieces

### PieceID data model (done ✅)

Create a PieceID data model to identify pieces across sheets.
Fields:

- sheet_id: str
- piece_id: int
  then use it in SegmentId instead of (str, int)

### Piece object update (planned 📋)

remove img_fp, now info is in piece_id

### Puzzle generator (done ✅)

this but in python: https://github.com/Draradech/jigsaw/tree/master
(cloned in libs/jigsaw for reference)

1. generate pieces
2. write texts on them to recognize them
3. generate aruco board with the pieces spaced in a few sheets

### SegmentMatcher (end overlapped version)

#### Debug algo (done ✅)

Check the algo cause the result are terrible

- is the transform correct? and applied to the right things

#### Pre shape check (done ✅)

Check the shape in/out/flat before even matching with transform

#### Normalization (planned 📋)

We might normalize on `s1_len`, those are the number of partial dist we are adding.
`similarity = tot_dist / max(s1_len, s2_len)`

### SegmentMatcher no overlap

#### Refactor away similarity computation (planned 📋)

The contour similarity is not really part of the segment matcher,
that piece just receives two lists and matches them.
--> move it to separate func.

#### Implement SM no overlap (planned 📋)

1. get the two segments
2. transform them on an axis, maintain the len between the ends
3. match with the new func

### Segment (done ✅)

Add attribute enum

- IN
- OUT
- EDGE
- weird ???

### PieceMatcher (done ✅)

Move the logic in `match_pieces` and `match_all_pieces` from `scratch_space/contour_/01_match_.ipynb` into dedicate `PieceMatcher` class.
The `PieceMatcher` would use `SegmentMatcher` internally, and `SheetManager` to get pieces/segments by `SegmentId`.
It handles symmetry (A, B) == (B, A) and stores results in a structured way.
It will hold internally the results of piece matches, and provide methods to query them.

### Puzzle solver

Build the map of where the pieces would be

#### Grid model (planned 📋)

- pieces have positions (row, col) in the grid and orientations (0, 90, 180, 270)
- grid has place types (corner, edge, inner), with also desired edge orientations (eg top edge, left edge, etc, defined as orientation enum)
  (maintain list of positions for each type/subtype for easy access)
  (and a way to get the desired edge type and orientations for a given position)

during piece loading/initialization

- define a piece type (corner, edge, inner) based on number of flat edges
- assign base piece edge orientation (eg edge is on right side, which will be a value in the orientation enum)
  so that we can match rotation on a desired "edge is on left side" basis (we have two orientations base and desired, we can compute the orientation needed)

some utility functions

- to get rotated segments of a piece based on its orientation in the grid
- to get expected rotation for a piece to fit in a given edge of the grid cell
  (eg base orientation of piece has edge on right side, to fit in left edge of grid cell it needs to be rotated 180 degrees)

some functions to compute total score of the grid
with some caching of already computed matches between pieces (SegID), to avoid recomputing them all the time
which we should have in the PieceMatcher class `_lookup`, need to just add a getter for pair of ids

note that we don't actually know the actual size of the puzzle (number of rows and columns), only total number of pieces
compute all possible grid sizes given total pieces and piece types (corner/edge/inner)
a grid model will hold a single size configuration set in its init

#### Grid swap solver (planned 📋)

start from a random grid of pieces (respecting actual edge/corner pieces)
then swap pieces to improve the overall match score
repeat until no more improvement

#### Iterative solver (planned 📋)

build the best guess of the puzzle layout iteratively

1. start from best matches
2. add pieces that fit with already placed pieces
3. repeat until no more pieces can be placed
   create some sort of GroupPiece class to hold placed pieces and their relative positions (does not use the grid model)

### Config management

#### Aruco config management (planned 📋)

qrcode printed on the aruco board with config info
also print using words
include a aruco config version number, with aruco config manager class to handle different versions and load old configs

#### Config for sheet preprocess/contour (done ✅)

- SheetAruco changes name to SheetArucoLoader (manual filename change)
- SheetArucoConfig
  - min_area
  - crop_margin
  - ArucoDetectorConfig
- update all users
  - SheetAruco use the new config class
  - load_sheet will not accept min_area anymore

Migration note: introduce `SheetArucoConfig` and update all call sites to
construct and pass that config to `SheetAruco`. `min_area` is now stored on
the config and `SheetAruco.load_sheet` no longer accepts a `min_area` argument.

#### Sheet loader config

attach aruco configs?

#### SheetLayout

what is that?

## Small tweaks

- [ ] `Piece.get_img(which='bw', faint=0.1)` to get a fainter copy of the image
      (eg `p2_img = p2.img_bw.copy() // 10`).
- [ ] Cleaner segment match result func,
      not custom cell in `scratch_space/contour_/01_match_.ipynb`.
- [x] Basemodel for sheet/piece/edge instead of tuple
- [x] Basemodel for match result + score
- [ ] Move detector and board config values in params. Note that there must be some way to match configs to what was used to take the picture.
- [ ] Add a way to tell which side of the board is up when taking pictures
- [ ] Draw contour should not draw closed loops
- [ ] Add a method to `EdgePos.to_edge_ends()`
- [ ] Add some kwargs to `show_image_mpl` to set title and similar
- [ ] Add `show_images_mpl` which accepts a list of images and does the subplots
- [ ] Remove `from __future__ import annotations`
- [ ] Document segment/contour/coords/swap_coords
- [ ] Unify edge types EdgePos EdgeType

## Docs

Write some docs about the overall architecture of the puzzle solver.

## Meta agent

### New dev flow (planned 📋)

plan-prototype(in notebook)-implement is old school, notebooks are legacy workflow for manual implementation
update the planning phase to be clear and comprehensive
then implement directly in `src/` with tests
only provide usage notebooks with finished features
if a feature is complex to implement and plan, it should be planned more carefully and optionally split in several sub-features

### roadmap split (planned 📋)

Split the roadmap in planned/done/ideas
in done add links to PRs/commits/notebooks/READMEs where the feature was implemented

### better docs agent

write good docs in `__init__.py` files
then auto-generate markdown files from them

### multiprocess (planned 📋)

run piece matching in parallel

### Shape Classification Fix (planned 📋)

Current shape classification for segments is leading to too many "WEIRD" shapes, causing many valid piece matches to be rejected. We need to improve the shape classification logic to reduce false WEIRD classifications.

### Virtual border (planned 📋)

When building a puzzle in a grid, consider adding a virtual border of EDGE segments around the puzzle to simplify edge matching logic.
With the softer shape constraint, this should help pieces fit better at the borders without needing to special-case edge and pieces.

### Softer matching constraint (planned 📋)

Shape compatibility is currently a hard gate in piece matching.
Consider using it as a softer constraint, applying a penalty to the similarity score instead of outright rejecting incompatible shapes.
Eg a multiplier to the score if shapes are incompatible.
Return a float instead of a bool from `is_compatible()`.

### Sheet preprocess config (planned 📋)

The preprocess steps before aruco detection (eg blurring, thresholding) should be configurable via a Pydantic config class.
Each preprocess step would have its own config model, and the overall config would hold a list of steps to apply in order.
This would allow tuning the preprocess pipeline for different types of images.

### Color based thresholding (planned 📋)

Add color based thresholding options to the sheet preprocess config.
E.g. use green background to segment pieces from the sheet.

## Legend

- ✅ done
- 🚧 doing
- 📋 planned
- ❌ rejected
