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
  borderValue=(0, 255, 0) for out-of-warp pixels.
  NOTE: this is an artifact with different meaning, we can change it to another bright color like magenta
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

## proposed phase sequence

1. Lock the minimal contract: named background presets and HSV mask toggles.
2. Confirm the QR payload stays stable and board_config_id is the only lookup
  key needed for preset resolution.
3. Implement the simplest background path in board composition.
4. Implement optional HSV background-mask override in sheet preprocessing.
5. Validate on tests plus real datasets and decide keep-compat versus
  controlled break.
6. Document outcomes and drop WARNING.md in impacted dataset folders only if
  we choose a breaking path.
