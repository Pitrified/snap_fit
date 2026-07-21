# Green background

## draft

Enable an optional green background in generated ArUco boards so pieces are
easier to separate visually in some photo conditions, while preserving current
white-background behavior by default.

## analysis

### Why this feature exists

- The current generated boards are grayscale from OpenCV board generation and,
  in practice, are white background with black markers.
- Some capture setups may benefit from chroma contrast (green background)
  during downstream piece segmentation.
- We need this as an option, not a forced behavior, because existing datasets
  and tests assume current defaults.

### Docs and code cross-check

Checked docs:

- docs/library/aruco/board.md
- docs/library/aruco/detector.md
- docs/library/puzzle/sheet_aruco.md
- docs/guides/coordinate_spaces.md
- docs/roadmap/roadmap.md

Checked code:

- src/snap_fit/aruco/aruco_board.py
- src/snap_fit/aruco/board_image_composer.py
- src/snap_fit/aruco/aruco_detector.py
- src/snap_fit/puzzle/sheet_aruco.py
- src/snap_fit/puzzle/sheet.py
- src/snap_fit/image/process.py
- src/snap_fit/aruco/sheet_metadata.py

Checked tests:

- tests/aruco/test_aruco_board.py
- tests/aruco/test_aruco_detector.py
- tests/aruco/test_sheet_metadata.py

### What is true today

- ArUco board generation is grayscale in ArucoBoardGenerator.generate_image().
- BoardImageComposer.compose() converts grayscale board output to BGR before
  overlays (slot labels and QR metadata).
- ArucoDetector.correct_perspective() already uses a green border fill
  borderValue=(0, 255, 0) for out-of-warp pixels (aruco_detector.py:114).
  NOTE: this is an artifact with different meaning, we can change it to another bright color like magenta.
  With a green board background plus an HSV green mask this fill collides with
  real background: the mask would also swallow the out-of-warp border.
  Recoloring the border to magenta is now scheduled in phase 3 (D16) so D9's
  independence is real in pixels, not just in intent.
- Sheet preprocessing is currently fixed in Sheet.preprocess(): blur,
  grayscale, binary threshold (130), erosion, dilation, color flip.
- There is no current config field to control board background color.
- There are tests for board generation and detector behavior, but no dedicated
  tests for BoardImageComposer itself.

### Constraints and risks

- Printed ArUco marker readability must remain reliable with green background.
- Any green-removal preprocessing must be optional and data-driven to avoid
  regressions on existing white-background captures.
  NOTE: this is a nice to have, but if it turns the code into spaghetti to
  address it, we can delete all the old captures and start fresh.
- Metadata strip and slot labels must remain legible if the base color changes.
- Existing APIs and JSON configs should remain backward-compatible.
  NOTE: this is a nice to have, but if it turns the code into spaghetti to
  address it, we can delete all the old captures and start fresh.

### Dataset compatibility audit (2026-07-12)

Inventory audited from data/ and cache/:

- Data-side config files relevant to this feature: 10
  - *_ArucoBoardConfig.json: 6 files
  - *_SheetArucoConfig.json: 4 files
- Additional puzzle config found: data/sample_puzzle_v2/config.json
- Cache persistence artifacts found:
  - metadata.json: cache root + demo + milano1 + oca
  - matches.json: cache root + oca
  - dataset.db: demo + milano1 + oca

Current config shape observations:

- All ArucoBoardConfig JSON files currently use only marker/grid geometry and
  dictionary fields. No background color field exists.
- SheetArucoConfig files in oca and milano1 do not have metadata_zone.
- SheetArucoConfig files in demo variants include metadata_zone.

Backward compatibility assessment:

- Additive config fields (for example background preset, optional green-mask
  preprocess toggle) are low risk for existing JSON files.
- Renaming or removing existing fields in ArucoBoardConfig or
  SheetArucoConfig is high risk and would break all existing stored configs.
- Changing defaults (for example white to green globally) is medium to high
  risk because existing datasets and cached outputs were produced with white
  board assumptions.
- Existing cache metadata/matches schemas are not directly tied to board color,
  but ingest outputs can drift if preprocess defaults change.

Compatibility policy folded from notes:

- Backward compatibility is preferred but not a blocker.
- If a breaking change is selected, create WARNING.md in impacted dataset
  folders documenting required re-ingest or config updates.

### QR payload scope

- Keep the QR payload stable for Phase 1.
- Do not add background preset to the QR payload unless a later phase proves
  that board_config_id is insufficient to resolve the rendered board config.
- Treat board_config_id as the source of truth for the background preset at
  ingest time.
- If a future phase decides the payload must change, record that as a separate
  compatibility decision because it affects printed artifacts and decode
  assumptions.

### Ingest driver usage pattern (2026-07-12)

Surveyed how configs actually reach SheetAruco today, to shape phase 4.
The rule already in place: drivers own config loading, the library never
touches JSON on disk.

- Webapp: `puzzle_service.py` (and `piece_service.py`) load
  `data/{dataset_tag}/{dataset_tag}_SheetArucoConfig.json` via
  `SheetArucoConfig.model_validate_json`, then `SheetAruco(config)` and
  `load_sheet` per image. The dataset folder carries its own full config.
- Notebook `scratch_space/20_piece_markers/01_print_read_board.ipynb` is the
  existing end-to-end pattern and already uses `BoardImageComposer`:
  - Print time: builds the configs in code, composes and saves the board PNGs
    to `data/aruco_boards/{board_config_id}/`, and saves BOTH
    `{id}_ArucoBoardConfig.json` and the full `{id}_SheetArucoConfig.json`
    next to them.
  - Ingest time: reloads the saved `SheetArucoConfig` JSON from the board
    folder ("this is what an ingest script would do") and runs
    `SheetAruco.load_sheet()` on photos.
- `SheetMetadataDecoder` is usable standalone on a raw photo, before any
  SheetAruco setup, so a driver can decode the QR first and use
  `board_config_id` to pick the folder to load from.

### Photo-ingest notebook inventory (note 1, expanding the phase 4 scope)

`01_print_read_board.ipynb` is not the only driver that loads real photos.
Surveyed every notebook that calls `load_sheet`/constructs `Sheet` on real
images so phase 4 and phase 5 cover all of them, not just the print notebook.

- `scratch_space/aruco_setup/04_load_sheets.ipynb`: the canonical
  reload-and-ingest pattern. Saves `{tag}_SheetArucoConfig.json` once, then
  ("then in other notebooks reload it like this") reloads it by hardcoded
  `sheets_tag`, builds `SheetAruco`, and runs `load_sheet(img_fp)` on real
  photos. It does NOT decode the QR to pick the config.
- `scratch_space/fastapi_scaffold/01_db_ingestion.ipynb`: bulk DB ingestion.
  Loads `SheetArucoConfig` from disk, runs `SheetAruco.load_sheet` over a
  folder into a `SheetManager`, and persists to SQLite. Also reload-by-tag.
- `scratch_space/sheet_manager/02_usage.ipynb`: `SheetManager` + `load_sheet`
  usage sample, reload-by-tag.
- `scratch_space/20_piece_markers/00_sample.ipynb`: the QR/metadata sample.
  This one already exercises `SheetMetadataDecoder`, `board_config_id`, and
  loading `{id}_SheetArucoConfig.json` from disk - the closest thing to the
  decode-then-resolve flow phase 4 formalizes.

The split that matters for phase 4: the reload-by-tag notebooks (04_load_sheets,
db_ingestion, sheet_manager/02_usage) never touch the QR id; they trust the
saved config. So the derivation helper (Q12 auto-enable at save time) is what
makes green work for them for free - the mask is already inside the JSON they
reload. The decode-by-id loader helper is the upgrade for the metadata-aware
notebooks (00_sample style) and any future ingest driver that starts from a
raw photo without knowing which config to load.

Consequence for phase 4: since the saved `SheetArucoConfig` embeds the board
config (with its preset, post phase 1) and, after Q11, the preprocess config
with the nested mask, the green setting travels inside the saved JSON on its
own. The Q12 auto-enable rule belongs at config-build time (a helper the
notebook calls before saving), not inside `SheetAruco.load_sheet()`.
Phase 4 becomes: a loader helper keyed by board_config_id, a derivation
helper applying the Q12 precedence, making the metadata-aware notebook ingest
actually driven by the decoded id, and confirming the reload-by-tag notebooks
inherit the mask through their saved config with no per-notebook green code.

### Gap assessment (2026-07-12, after phases 1-2)

Reviewed the p1/p2 commits (790c57e, a7ffa8a) against the plan and the code.
Phase 1 and 2 implementations match their sub-plans:
additive `background_preset` on ArucoBoardConfig, additive `background_mask` on SheetArucoConfig,
`_colorize_background()` in BoardImageComposer, and 9 regression tests that pass.
The gaps below are in the plan for the remaining phases, not in the delivered work.

- G1: no production entry point exercises the preset.
  `BoardImageComposer` has zero call sites outside tests;
  board PNGs in `data/aruco_boards/` come from notebooks
  (`scratch_space/aruco_setup/03_generate_aruco_board.ipynb`, `scratch_space/20_piece_markers/01_print_read_board.ipynb`).
  No phase says how an operator actually produces a green board end to end.
  ANS: from the existing notebook, one of the config will be the background mode.
- G2: `background_mask` has no plumbing path to where preprocessing runs.
  `Sheet.preprocess()` hardcodes its parameters (threshold 130, kernel sizes)
  and `Sheet.__init__` accepts no preprocess config;
  `SheetAruco.load_sheet()` constructs `Sheet` without passing `background_mask`.
  Phase 3's plan says "add preprocess options per the phase 1 contract" but does not design the config threading,
  and it will collide with the existing REFA comment in `sheet.py` (preprocess params should be a config object).
  ANS: we can think about a broader preprocess config object
- G3: the HSV mask output semantics are unspecified.
  The current pipeline is blur, grayscale, threshold, erode, dilate, `flip_colors_bw`, producing `img_bw`
  with a specific polarity that contour finding depends on.
  Phase 3 does not state whether the mask replaces the whole binary path or only the threshold step,
  nor how erosion/dilation apply to the mask output, nor the required output polarity.
  It also does not document that the HSV bounds use the OpenCV hue scale (0-179),
  and `BackgroundMaskConfig` does not validate ranges.
  ANS: then we need to think about this
- G4: board_config_id resolution is not implemented anywhere.
  D10 names it the source of truth for preset resolution at ingest,
  but no code loads a board config from `data/aruco_boards/{id}/`;
  only the `SheetMetadata` string carries the id.
  As planned, the mask is enabled manually in SheetArucoConfig, so a green board with a sheet config
  that forgot `background_mask.enabled` fails silently.
  Either a phase implements the resolution, or D10 should be downgraded to a naming convention.
  ANS: then we analyze. the idea is that in the qrcode there is a name, the matching json is found on disk, we load that json, in the json we discover that green was set. you should not build the config by hand when reloading the image from a physical picture.
- G5: no plan step produces the green validation data phases 3-4 rely on.
  Phase 3 says "at least one green-background sample set" but nothing creates it
  (print and photograph, or synthesize by compositing piece images onto a green board render).
  ANS: plan it
- G6: detection on green backgrounds is asserted, not tested.
  Phase 2 correctly notes the detector only uses board geometry at setup,
  but real detection runs on photos where the green background has grayscale luminance around 150 versus 255 for white,
  reducing marker contrast.
  Phase 4 should include an explicit cheap test: render a green-preset board, run `ArucoDetector.rectify()`, expect success.
  ANS: do it
- G7 (minor): the "proposed phase sequence" section below lists 6 items while the plan has 5 phases
  (items 1-2 were merged into phase 1); harmless but worth knowing when cross-reading.
  ANS: lol fix it

## decisions

- D1: Take the simplest implementation path first.
  Why: Q1 says no preference on full-board versus inner-only scope.
- D2: Use a named preset for background color selection.
  Why: Q2 explicitly prefers presets over raw BGR or RGB values.
- D3: Start with a simple HSV green-mask override step in preprocessing.
  Why: Q3 prioritizes a focused first implementation over generic scaffolding.
- D4: Keep board generation grayscale-capable but add colorization at the
  board-composition layer first.
  Why: BoardImageComposer already owns BGR composition and overlays.
- D5: Treat generated boards and real photos as the target, allowing green
  variation from print and camera conditions.
  Why: Q4 confirms generated boards are the source and color will vary.
- D6: Backward compatibility is a nice to have, not mandatory.
  Why: Q5 allows breaking changes if complexity becomes too high.
- D7: If a breaking change lands, add WARNING.md in each impacted dataset
  folder and prefer re-ingest over spaghetti compatibility branches.
  Why: aligns with notes under constraints and Q5.
- D8: Validate with real images plus targeted unit tests.
  Why: visual changes can pass unit tests but still fail in real detection.
- D9: Keep ArucoDetector warp border color independent from board background
  semantics.
  Why: current green borderValue is a rectification artifact, not board color.
- D10: Keep the QR payload stable in Phase 1 and treat board_config_id as the
  source of truth for board preset resolution.
  Why: avoids expanding printed metadata unless the feature demonstrably needs
  it.
- D11: The board generation notebook stays the operator entry point;
  background preset becomes one of its configs.
  Why: Q7 and G1 ANS; no script or webapp wiring needed for this feature.
- D12: Introduce a preprocess config object (SheetPreprocessConfig) that owns
  the currently hardcoded Sheet.preprocess parameters, threaded
  SheetArucoConfig -> SheetAruco -> Sheet.
  Why: Q8 chose the refactor; resolves the REFA comment in sheet.py while
  building the plumbing the mask needs anyway.
  Refined per Q11: background_mask nests inside SheetPreprocessConfig,
  amending the phase 1 placement (code-only change, no dataset JSON uses it).
- D13: The HSV mask, when enabled, replaces only the threshold step;
  blur stays before it, erode/dilate/flip stay after it unchanged.
  Why: Q9; cv2.inRange output has the same polarity as apply_threshold
  (background white, pieces black), so the rest of the pipeline is untouched.
  Refined per note 3: this is the "mask-as-threshold" strategy, now one of
  two the preprocess machinery must express. The alternative (D17) repaints
  the masked green pixels to white before grayscale and leaves the existing
  threshold in place. Phase 5 experiments pick the winner per D17.
- D14: Implement board config resolution at ingest as its own phase:
  QR board_config_id -> load the matching JSON from data/aruco_boards/{id}/ ->
  the discovered preset drives the mask automatically.
  Why: G4 ANS - configs must not be rebuilt by hand when ingesting a physical
  photo; this upgrades D10 from naming convention to working code.
  Refined per the driver-level note: the resolution flow lives in the driver
  (notebook or service), not in SheetAruco/Sheet - the preprocessor knows
  nothing about JSON on disk. Phase 4 ships loader and derivation helpers plus
  the notebook wiring; the Q12 precedence (resolved green/blue preset
  auto-enables the mask with default bounds, explicit background_mask always
  wins, no-QR photos fall back to the sheet config alone) is applied when the
  config is built, before SheetAruco ever sees it.
- D15: Validate with both a synthetic set (piece crops composited onto a green
  board render) and real printed-and-photographed captures, and include an
  explicit detector-rectifies-green-board test.
  Why: Q10 and G6 ANS - synth proves the pipeline exists, real images show
  what happens in the real world.
- D16: Recolor the ArucoDetector out-of-warp border fill from green
  (0, 255, 0) to magenta, scheduled inside phase 3.
  Why: note 2. Once the board background is green and an HSV green mask runs on
  the rectified image, the current green border fill (aruco_detector.py:114)
  is indistinguishable from real background and the mask swallows it. Magenta
  keeps D9's border-vs-background independence true at the pixel level. Placed
  in phase 3 because that is where the green mask first makes the collision
  real; it is a small, self-contained detector change.
- D17: The preprocess refactor (D12) introduces a small mask-mode switch so
  the green mask can run as either strategy, and phase 5 experiments choose:
  - "as_threshold" (D13): inRange output is used directly as the binary,
    replacing the threshold step.
  - "flatten_to_white": inRange selects the green pixels, those pixels are
    painted white in the color image, and the existing
    grayscale -> threshold -> erode -> dilate -> flip pipeline runs unchanged
    on the flattened image. This gives the downstream pipeline a clean white
    background instead of rewiring its polarity.
  Why: note 3. The refactor is happening anyway, so expressing the step as a
  mode (not a hardcoded threshold swap) is the neat seam for experimenting
  with added pipeline steps without another rewrite. Machinery stays minimal:
  one enum-like mode field on the mask config, not a generic step framework.
  Experiment outcome (phase 5, greendemo captures): the two modes produce
  byte-identical binaries on all six real photos. The pieces are dark, so
  repainting the background white and thresholding lands on exactly the same
  segmentation as using the mask directly. `as_threshold` stays the default;
  `flatten_to_white` is kept because its advantage is light-colored pieces,
  which this capture set does not contain.
- D18: The default `background_mask.lower_hsv` value floor is 100, not 40.
  Why: measured on the greendemo captures. The board background reads V
  186-212, but pieces lit by reflected board light reach V 42-61 while sharing
  the background hue (70-81), so hue alone cannot separate them - brightness
  is the discriminator. With the original floor of 40 those glare-lit pixels
  were classified as background, which eroded every piece by roughly 60% of
  its area and dropped one piece entirely on the worst capture. Measured safe
  band 60-120; above ~140 dim background regions stop being masked and merge
  into the pieces. 100 sits centered in the verified band.
- D20: Boards are displayed on a screen and photographed. They are never
  printed on paper, so paper stock, ink color, and print gamut are out of
  scope permanently.
  Why: stated by the user on 2026-07-21. This retroactively settles the phase 5
  caveat: the greendemo captures are of a laptop screen, which is not an
  approximation of the real setup, it *is* the real setup. The D18 value floor
  of 100 is therefore tuned on representative data, not provisional.
  Consequences: "print time" in the plan and notebooks means "render and
  display"; a screen background is bright and saturated (V 186-212), which is
  why brightness separates pieces so cleanly; and pieces resting on a lit
  screen will always pick up reflected board light, so D18 is a permanent
  requirement rather than a one-off fix.
- D21: The workflow is scale-first: roughly 100+ boards for a 1500-piece
  puzzle, with the QR and the slot grid used as the manual tracking key.
  Why: stated by the user on 2026-07-21. The operator photographs a board,
  reads the QR for sheet identity, and writes down the slot coordinate (B3)
  plus the photo id when annotating a physical piece. This makes
  `sheet_index` uniqueness across the print run and stable slot labels the
  load-bearing parts of the feature, and it means board generation must be
  run for N sheets, not the demo's 2.
- D19: Keep backward compatibility; no controlled break, so no WARNING.md.
  Why: the phase 5 gate. Every change landed additive - `background_preset`
  defaults to white, `SheetPreprocessConfig` defaults reproduce the previous
  pipeline byte-identically, and the mask only engages when explicitly enabled
  or derived from a green/blue preset. No existing dataset JSON used
  `background_mask`, so nesting it under `preprocess` broke no stored config.
  The D18 bounds change only affects an enabled mask, which no white dataset
  has. Existing sample configs still validate and the full suite passes.

Rejected alternatives:

- R1: Make green background the new default.
  Rejected because it risks breaking current behavior and docs.
- R2: Patch ArucoDetector only.
  Rejected because board generation and piece segmentation are separate
  concerns; detector-only changes do not solve end-to-end ingestion behavior.

## open questions

- Q1: Do we want the green color option on the entire board background, or only
  in the inner puzzle workspace (inside the ArUco ring)?
  ANS: no preference, follow the simplest implementation path first
- Q2: Should the green option be configurable by named preset (for example
  white, green, blue) or by explicit BGR/RGB values?
  ANS: Named preset.
- Q3: For sheet preprocessing, should we start with a simple HSV green-mask
  override step, or first expose generic color-threshold config scaffolding?
  ANS: simple HSV green-mask override step.
- Q4: Is this feature intended for generated boards only, or should we also
  support importing externally designed green boards with equivalent detection
  behavior guarantees?
  ANS: the generated board will be used to take real photos, so we should
  assume it is not value-perfect and allow for some variation in the green
  color. Externally designed boards do not really exist. We use generated
  boards.
- Q5: What level of compatibility do we require with existing saved configs in
  data/*/*_ArucoBoardConfig.json and *_SheetArucoConfig.json?
  ANS: required none. It is nice to have. If we choose a breaking change,
  drop a WARNING.md file in impacted dataset folders. There should not be
  many. Some available datasets are already not compatible.

- Q6: Should the QR payload include background preset information?
  ANS: no for Phase 1. Keep payload stable and resolve background preset from
  board_config_id unless a later phase shows that is insufficient.

Question batch status:

- No additional questions were raised while expanding the work into phase
  sub-plans on 2026-07-12.
- Batch Q7-Q10 added 2026-07-12 from the post-phase-2 gap assessment (G1-G7).

- Q7: Where should the operator-facing entry point for generating a green board live:
  update the existing notebooks, a small script, or wiring BoardImageComposer into the webapp?
  This decides which phase owns G1.
  ANS: notebook.
- Q8: For G2, how should `background_mask` reach `Sheet.preprocess()`:
  minimal (pass just the BackgroundMaskConfig through SheetAruco into Sheet),
  or take the opportunity to introduce the small preprocess config object the REFA comment in sheet.py asks for?
  ANS: refactor.
- Q9: When the mask is enabled, should it replace the whole binary path
  (blur/threshold/erode/dilate applied to the mask instead), or only replace the threshold step
  with the rest of the pipeline unchanged around it?
  ANS: replace only the threshold step.
- Q10: For G5, do we validate with real printed-and-photographed green boards,
  or is a synthetic set (piece crops composited onto a green board render) acceptable for phases 3-4?
  ANS: both. synth to check that the pipeline exist, real images to check what happens in the real world.

- Batch Q11-Q12 added 2026-07-12 while folding in the G1-G7 and Q7-Q10 answers.

- Q11: After the D12 refactor, where does `background_mask` live:
  nested inside the new SheetPreprocessConfig (recommended - it is a preprocess concern,
  and no dataset JSON uses the field yet so moving it costs nothing),
  or staying as a top-level SheetArucoConfig sibling as phase 1 shipped it?
  Nesting slightly amends the phase 1 JSON shape; the change is code-only.
  ANS: ok move it nested.
- Q12: For phase 4 auto-enable, is this precedence correct:
  a resolved board preset of green or blue auto-enables the mask with default HSV bounds,
  and an explicit `background_mask` in the sheet config always wins over the auto rule
  (including an explicit enabled=false to force it off)?
  Photos without decodable QR metadata fall back to the sheet config alone.
  ANS: ok

## proposed phase sequence

Rewritten 2026-07-12 to match the actual phase files (per G7 ANS);
the original list had 6 items for 5 phases because the QR payload decision
was merged into phase 1, and phase 4 (resolution) was added later from G4.

1. Lock the minimal contract: presets, mask toggles, and the QR payload
  decision (board_config_id stays the only lookup key).
2. Implement the background preset path in board composition.
3. Implement the optional HSV mask override in sheet preprocessing, with the
  preprocess config refactor, the D17 mask-mode switch, and the D16 detector
  border recolor to magenta.
4. Resolve the board config from disk at ingest via the QR board_config_id so
  the preset drives the mask automatically, covering every photo-ingest
  notebook (reload-by-tag and decode-by-id) per the note 1 inventory.
5. Validate on synthetic and real green captures plus existing datasets,
  run the D17 mask-mode experiments to pick a strategy, and decide keep-compat
  versus controlled break.
6. Document outcomes and drop WARNING.md in impacted dataset folders only if
  we choose a breaking path.
