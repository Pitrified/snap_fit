# UI based solver

## Overview

### preliminary changes to UI

1. fix on a dataset for the UI solver
1. add a "solver" tab to the UI
1. add some visualization primitives in the UI for showing pieces and matches visually

### main solve flow

pick a piece (corner, random, user selected)
start suggesting matches for that piece, sorted by confidence
user can click "accept" or "reject" on each suggestion, update the confidence
mark the placement of the piece on the solver's internal state
pick another "free" edge of the current solve island and repeat

### multiple solve islands

user can pick another piece to start a new "island" if they want to, we might want to keep that flexible from the start
assess how much the code complexity increases if we allow the user to pick any piece at any time, vs enforcing that they pick a piece that is adjacent to the current solve island

### ui updates

1. show the current solve island(s) in the UI
1. or at least a recap of all the matched pieces and their placements
1. high level overview of the solve progress, e.g. how many pieces placed, how many edges matched, etc.