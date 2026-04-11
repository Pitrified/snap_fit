# Marked board sample use

## Overview

we want to create a notebook to demonstrate the use of the piece identity markers

create a bunch of board images with the markers (several sheets), save it to disk
where (`aruco_boards`?), how to config it, how to run the code to generate it, and what the output looks like together with its configuration

then the user takes some pictures of the board with the markers and the physical pieces, and we run the detection code to show how it works in practice
how, where the configs are reloaded (check and print), how to ingest the images, run the detection, and visualize the results (e.g. print the detected piece identities and their positions on the board, show the detected pieces and their identities, ...)
where should they be saved, in which folder structure, which config and additional data is needed

plan, then update the notebook `scratch_space/20_piece_markers/01_print_read_board.ipynb`

## Plan

### Overview

The notebook is split into two main parts.

**Part 1 - Print Time:** Generate several board images with embedded slot-grid labels and QR codes.
Save the PNGs to `data/aruco_boards/{board_config_id}/` and write the matching config JSON alongside so the operator can reproduce or reload the config exactly.

**Part 2 - Ingest Time:** Reload the saved config from disk, run `SheetAruco.load_sheet()` on photos of the board-with-physical-pieces, inspect `sheet.metadata` (decoded from QR), show how piece labels are assigned via the slot grid, and visualise results.

A stand-in demo (loading the generated board PNG as if it were a photo) is included so all code cells are runnable without a physical puzzle.

---

### Folder Structure

```
data/
├── aruco_boards/
│   └── demo/                      # generated board images + configs
│       ├── sheet_00.png
│       ├── sheet_01.png
│       ├── sheet_02.png
│       ├── demo_ArucoBoardConfig.json
│       └── demo_SheetArucoConfig.json
└── demo/
    └── sheets/                    # user places real photos here
        ├── photo_sheet_00.jpg
        └── ...
```

---

### Sections

| # | Section | Content |
|---|---------|---------|
| 1 | Imports | All project and third-party imports, display helper |
| 2 | Params and paths | `get_snap_fit_params()`, print paths |
| 3 | Define config | `ArucoBoardConfig`, `SlotGridConfig`, `MetadataZoneConfig`, `SheetArucoConfig`; rprint |
| 4 | Generate board images | `BoardImageComposer.compose()` x N sheets, save PNG, log |
| 5 | Save config JSON | `ArucoBoardConfig` + `SheetArucoConfig` as JSON in the board folder |
| 6 | Display board images | `matplotlib` inline display of every saved PNG |
| 7 | Verify QR round-trip | `SheetMetadataDecoder().decode()` on each generated image |
| 8 | Inspect slot grid | `SlotGrid.label_for_slot()` table, slot-centre overlay image |
| 9 | Reload config from disk | `SheetArucoConfig.model_validate_json()` from saved JSON |
| 10 | Demo ingest (stand-in) | `SheetAruco.load_sheet()` on a generated PNG; show `sheet.metadata`, piece count |
| 11 | Real photo ingest | Folder setup; `SheetManager.add_sheets()` with real photos; `PieceRecord.label` |
| 12 | Visualise detections | Draw slot centres + piece centroids + labels on sheet image |

---

### Key classes used

- `BoardImageComposer(board_config, metadata_zone).compose(metadata)` - full board PNG
- `SheetMetadataDecoder().decode(img)` - reads QR payload from a raw image
- `SlotGrid(grid_config, board_config)` - computes geometry; `slot_centers()`, `label_for_slot()`
- `SheetAruco(config).load_sheet(img_fp)` - QR decode + rectify + crop + slot label assignment
- `SheetManager.add_sheets(folder, sheet_aruco)` - bulk ingest of a folder of photos
