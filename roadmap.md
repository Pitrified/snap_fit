# Roadmap

## IDEAs

### Scale invariant pictures

We should create scale invariant pictures by adding a ruler to the image.
Or a bunch of qr codes of known size and position.
This will help with the calibration of the images.

### OCR for piece labels

Extract text
some UI to check it?

### SheetLoader ABC (SheetAruco.load_sheet)

Define ABC for sheet loading
SheetAruco could implement it
Let SheetManager accept that

### SheetManager

Get a list of segment ids (sheet.piece.edge)
Given a segment id, get
* segment
* piece
* segment from other pieces

### SegmentMatcher (end overlapped version)

#### Debug algo

Check the algo cause the result are terrible
* is the transform correct? and applied to the right things

#### Pre shape check

Check the shape in/out/flat before even matching with transform

### Segment

Add attribute enum
* IN
* OUT
* EDGE
* weird ???

## Small tweaks

- [ ] `Piece.get_img(which='bw', faint=0.1)` to get a fainter copy of the image
    (eg `p2_img = p2.img_bw.copy() // 10`).
- [ ] Cleaner segment match result func,
    not custom cell in `scratch_space/contour_/01_match_.ipynb`.
- [ ] Basemodel for sheet/piece/edge instead of tuple
- [ ] Basemodel for match result + score
- [ ] Move detector and board config values in params
- [ ] Add a way to tell which side of the board is up when taking pictures
- [ ] Draw contour should not draw closed loops

