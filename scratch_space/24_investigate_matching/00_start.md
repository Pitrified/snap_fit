# investigate matching

## draft

in
`data/greendemo_small/sheets`

we have 12 pictures of 3 boards, at 4 different zoom levels

`AAA__gds_pM_xZ.jpg`

where M is the board number (1,2,3) and Z is the zoom level (1,2,4,5)
and AAA is a prefix we can ignore (IMG or PXL with timestamp).

```
IMG_20260723_223210__gds_p1_x4.jpg
IMG_20260723_223612__gds_p2_x4.jpg
IMG_20260723_223822__gds_p3_x4.jpg
PXL_20260723_202949294__gds_p1_x2.jpg
PXL_20260723_203005406__gds_p1_x5.jpg
PXL_20260723_203015962__gds_p1_x1.jpg
PXL_20260723_203538742__gds_p2_x2.jpg
PXL_20260723_203549280__gds_p2_x5.jpg
PXL_20260723_203556185__gds_p2_x1.jpg
PXL_20260723_203749409__gds_p3_x2.jpg
PXL_20260723_203755958__gds_p3_x5.jpg
PXL_20260723_203801631__gds_p3_x1.jpg
```

### task 1

all p1 images are cut badly: a piece is cut off slightly.

are there some patches we can do in the reprojection/cut code to fix this?
in the original photo with the aruco rings, the piece is well within the frame.

### task 2

we want to compare and analyze the different zoom levels and camera modes

which one produces the cleanest contours?

### task 3

all these pieces match in a few groups of a few pieces
we can drive the matching code by hand and see if we can get a good match for all pieces
so that we can create a ground truth for the matching code
and then we can test some things in the matching code or preprocessing configs to see how we can maximize the matching scores

## ...

...
