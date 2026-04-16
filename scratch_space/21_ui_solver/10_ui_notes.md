# UI notes

## label of placed pieces

when a piece is placed on the grid, we show a small label with the piece ID to help track placements

## orientation of suggested pieces

when showing a suggested piece, we need to show it in the correct orientation. This requires the piece image endpoint to support rotation, and the UI to render the image with the correct rotation applied. Show that orientation also as text for clarity (e.g. "Place piece #5 rotated 90° clockwise")

## side by side matching preview

when proposing a match, we want to also preview the rotated/translated/reshaped piece image
existing piece on grid is static, new piece image is rotated/translated/reshaped according to the proposed placement. This will help users understand the suggestion and build intuition about how the solver is working.
the ends of the two matching segments in the contour can be matched
overlap the two piece images with some transparency to show how they fit together

## rotated label on the piece

to help keep track of the labels, we can also show the piece ID label directly on the piece image, rotated according to the piece orientation
