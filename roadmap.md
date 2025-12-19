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
* segment
* piece
* segment from other pieces

### SegmentMatcher (end overlapped version)

#### Debug algo (done ✅)

Check the algo cause the result are terrible
* is the transform correct? and applied to the right things

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
* IN
* OUT
* EDGE
* weird ???

### PieceMatcher (done ✅)

Move the logic in `match_pieces` and `match_all_pieces` from `scratch_space/contour_/01_match_.ipynb` into dedicate `PieceMatcher` class.
The `PieceMatcher` would use `SegmentMatcher` internally, and `SheetManager` to get pieces/segments by `SegmentId`.
It handles symmetry (A, B) == (B, A) and stores results in a structured way.
It will hold internally the results of piece matches, and provide methods to query them.

### Consistency check (planned 📋)

Build the map of where the pieces would be
Might be in graph form is pieces are just squares

### Aruco config management (planned 📋)

qrcode printed on the aruco board with config info
also print using words
include a aruco config version number, with aruco config manager class to handle different versions and load old configs

## Small tweaks

- [ ] `Piece.get_img(which='bw', faint=0.1)` to get a fainter copy of the image
    (eg `p2_img = p2.img_bw.copy() // 10`).
- [ ] Cleaner segment match result func,
    not custom cell in `scratch_space/contour_/01_match_.ipynb`.
- [x] Basemodel for sheet/piece/edge instead of tuple
- [ ] Basemodel for match result + score
- [ ] Move detector and board config values in params. Note that there must be some way to match configs to what was used to take the picture.
- [ ] Add a way to tell which side of the board is up when taking pictures
- [ ] Draw contour should not draw closed loops
- [ ] Add a method to `EdgePos.to_edge_ends()`
- [ ] Add some kwargs to `show_image_mpl` to set title and similar
- [ ] Add `show_images_mpl` which accepts a list of images and does the subplots
- [ ] Remove `from __future__ import annotations`
- [ ] Document segment/contour/coords/swap_coords

## Docs

Write some docs about the overall architecture of the puzzle solver.

## Meta agent

plan-prototype(in notebook)-implement is old school, notebooks are legacy workflow for manual implementation
update the planning phase to be clear and comprehensive
then implement directly in `src/` with tests
only provide usage notebooks with finished features
if a feature is complex to implement and plan, it should be planned more carefully and optionally split in several sub-features

## Legend

* ✅ done 
* 🚧 doing
* 📋 planned
* ❌ rejected