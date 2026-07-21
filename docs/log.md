# docs/log.md - Documentation Change Log

> **LLM-maintained file.** Append a new entry for every doc write, ingest, or lint pass.
> Never edit or delete past entries. Format: `## [YYYY-MM-DD] <operation> | <scope>`
> Operations: `write` · `ingest` · `lint` · `update` · `index`

Grep tip: `grep "^## \[" docs/log.md | tail -10` shows the last 10 entries.

---

## [2026-07-21] ingest | scratch_space/23_green_background

Compiled the green-background feature into the wiki. New guide
`guides/green_background.md` covering the screen-displayed board workflow: generate a board set
with a green preset, photograph it, and ingest by decoding the QR and resolving the stored config
by `board_config_id`, with the QR sheet_index plus slot label used as the manual tracking key.
Updated `puzzle/sheet` (SheetPreprocessConfig replaces the hardcoded preprocess parameters, HSV
background mask with as_threshold / flatten_to_white modes; removed the stale `threshold`
attribute and "threshold is hard-coded" pitfall), `puzzle/sheet_aruco` (preprocess threading,
resolver-based ingest, min_area guidance), `aruco/board` (background presets), `aruco` overview
(composer, sheet_metadata, slot_grid, board_config_resolver), and `config` (SheetPreprocessConfig,
BackgroundMaskConfig, OpenCV HSV scale pitfall). Pitfalls captured from real captures: min_area
80k filters out every piece on a rectified board sheet, and too low a mask value floor silently
erodes pieces that reflect board light.

## [2026-04-16] write | guides/coordinate_spaces

New technical guide documenting the four pixel coordinate spaces (board-image, object-coord, rectified, cropped-sheet), transformation chain, crop_offset, piece image cropping pipeline, and pitfalls. Created to support the image crop fix in get_piece_img().

## [2026-04-07] write | all modules (full package)

Complete library documentation for all 35 tracked modules across 10 subpackages:
config, data_models, params, puzzle (9 modules), image (6 modules), grid (6 modules),
solver (2 modules), aruco (3 modules), persistence, webapp. Each page includes
purpose, usage examples, API reference, pitfalls, and cross-links. Index updated
to 35/35 complete.

## [2026-04-07] index | all

Initial catalog created in `docs/index.md`. All 35 modules marked `missing`. Wiki spine established:
`docs/index.md` (catalog) and `docs/log.md` (this file). No library pages exist yet.
