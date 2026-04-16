# UI notes

## label of placed pieces

when a piece is placed on the grid, we show a small label with the piece ID to help track placements

## orientation of suggested pieces

when showing a suggested piece, we need to show it in the correct orientation. Leverate existing rotation functionality. Show that orientation also as text for clarity (e.g. "Place piece #5 rotated 90° clockwise")

## side by side matching preview

when proposing a match, we want to also preview the rotated/translated/reshaped piece image
existing piece on grid is static, new piece image is rotated/translated/reshaped according to the proposed placement.
the ends of the two matching segments in the contour can be matched (some code in some random notebook does this)
overlap the two piece images with some transparency to show how they fit together
also show the label/description of the piece we are matching against, not just of the piece we are placing

## rotated label on the piece

to help keep track of the labels, we can also show the piece ID label directly on the piece image, rotated according to the piece orientation

## piece inspection

in the piece detail page, overlay the detected contour segments and corner points on top of the piece image

## piece edit

in the piece detail page, add options to change the detected in/out/edge segment labels
