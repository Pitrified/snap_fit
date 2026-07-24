# implementation tracking

Investigation into piece matching on the `greendemo_small` dataset: 12 photos of
3 board sheets under 4 capture conditions. Started from three tasks (a clipped
piece, a capture-quality comparison, a matching ground truth) and grew a fourth
that outranks them: segment shape classification is unstable across captures and
gates the matcher before any score is computed. Analysis, decisions and the full
Q1-Q19 record are in [`00_start.md`](00_start.md).

## Key decisions

Full list with rejected alternatives in [`00_start.md`](00_start.md#decisions).
The ones that shape more than one phase:

- **D2**: `(sheet_index, slot_label)` is the physical-piece identity key across
  captures. `PieceId.piece_id` is a per-capture ordinal and must never be used
  to join.
- **D3**: ground truth is stated in `(sheet_index, label, edge_pos)` terms, so it
  survives the phase 6 rescale that a pixel-space truth would not.
- **D6**: task 2 is reported over four named capture conditions, not a zoom
  axis. All 12 shots share one lens; app, distance and digital upscale move
  together.
- **D12 / D15**: the pairs and the per-segment shapes are hand-authored, and
  collected as one hand-off produced at the end of phase 2.
- **D14**: shape stability precedes ground truth. It is a correctness problem,
  not a quality metric.
- **D16**: shape incompatibility becomes a score penalty rather than a hard
  gate. Mechanism in phase 3, number measured in phase 4, default fixed in
  phase 7.
- **D9**: everything stays scratch-local. No `pipelines/` entry from this
  effort.

## Phases

| #   | Phase                          | Plan                                                             | Status  |
| --- | ------------------------------ | ---------------------------------------------------------------- | ------- |
| 1   | Fix the interior over-crop     | [`01_fix_interior_overcrop.md`](01_fix_interior_overcrop.md)      | done    |
| 2   | Corpus and annotation hand-off | [`02_capture_corpus.md`](02_capture_corpus.md)                    | done    |
| 3   | Segment shape stability        | [`03_shape_stability.md`](03_shape_stability.md)                  | planned |
| 4   | Ground-truth edge pairs        | [`04_match_ground_truth.md`](04_match_ground_truth.md)            | planned |
| 5   | Capture condition comparison   | [`05_capture_quality.md`](05_capture_quality.md)                  | draft   |
| 6   | Rectification scale experiment | [`06_rectify_scale_experiment.md`](06_rectify_scale_experiment.md)| draft   |
| 7   | Matching and preprocess tuning | [`07_matching_tuning.md`](07_matching_tuning.md)                  | draft   |

Status values: draft / planned / in progress / done / superseded / discarded.

Phases 5-7 stay `draft` until phase 3 lands; their shape depends on how much of
the shape instability turns out to be fixable.

## External dependency

Phase 2 ends by handing over an annotation sheet. Phase 4 cannot complete until
it comes back, and phase 3's acceptance number depends on it too. Everything
else runs regardless; phases 5 and 6 carry secondary metrics that need no truth
at all.

## Log

Append-only. Newest at the bottom.

- 2026-07-23 : bootstrapped `00_start.md` from the three-task draft. Probed
  `p1_x1`, `p1_x4`, `p2_x1`: found the cropped sheet is 280x300 where the piece
  area is 320x340, root-caused to `crop_margin` double-counting `board.margin`.
  Ruled out undetected markers (all 14 printed ring markers detected every
  time; the 6 interior ids are never printed).
- 2026-07-23 : ran the ingest over all 12 photos keyed by `(sheet_index, label)`.
  Confirmed label stability (centroids agree within 4 px across each sheet's 4
  captures), so `(sheet_index, label)` is the join key. Found only sheet 0's B2
  is clipped, on all 4 captures, and nothing else in the dataset. Found `x4`
  shrinks every piece bounding box, up to 25 px in one axis.
- 2026-07-23 : pulled EXIF across all 12. All shots are one lens (6.81 mm
  f/1.85, main sensor); the 5x telephoto is never used. Subject distance runs
  0.19 m to 0.79 m, HDR+ on all PXL and absent on IMG, `x5` carries a 2.5x
  digital upscale. Concluded there is no zoom axis, so task 2 is reported over
  capture conditions (D6). Corrected an earlier wrong claim that zoom changed
  the downsampling ratio: the board fills the frame everywhere, so the ~5.8x
  discard is uniform.
- 2026-07-24 : ran a `SegmentShape` census over all 48 segments x 4 conditions.
  10 of 48 disagree, including sign inversions and one segment with three
  different answers. Sheet 2 accounts for 7. This gates `compute_similarity`
  before any score, so it became phase 3 ahead of ground truth (D14). Also
  found the flat-edge census cannot recover the group structure: majority vote
  leaves only 2 flat segments in 48, far too few for any rectangular assembly,
  so the pieces are interior fragments and the grouping must be hand-authored.
- 2026-07-24 : all of Q1-Q19 answered and folded in. Derived `tracking.md` and
  the seven sub-plans from the phase list.
- 2026-07-24 : phase 1 done. Changed one line: the computed `crop_margin`
  default drops `board.margin`. Learned that `crop_offset` was **not** wrong and
  the phase plan was wrong to say so, its formula is the correct general
  relation for any `crop_margin` and hardcoding it to `ring_start` would have
  broken explicit-`crop_margin` configs; it corrected itself to 120 once the
  margin was fixed. Extracted it to a `SheetAruco.crop_offset` property because
  it was inline in `load_sheet` and untestable. Added
  `tests/puzzle/test_sheet_aruco.py` (6 tests, 5 fail on revert). Sliver check
  clean, so no ring buffer knob was added and D5 is settled in favour of the
  direct fix. Clipped pieces across the dataset: 4 -> 0; board-space centroids
  unchanged within 1 px, confirming the offset compensated the crop exactly.
  Docs updated, and fixed a pre-existing error in `coordinate_spaces.md` that
  sized the rectified image from board rather than object dimensions.
- 2026-07-24 : phase 2 done. `build_corpus.py` ingests all 12 into
  `cache/gds_corpus/` via `DatasetStore` (48 pieces, 12 physical), assertions
  green first run. `build_annotation_sheet.py` renders the hand-off sheet with
  coloured segments and the majority vote pre-filled, plus a YAML stub. Nothing
  in `src` needed changing; the capture condition went to a `captures.json`
  sidecar rather than growing `SheetRecord`.
- 2026-07-24 : two findings while validating the sheet. (a) The phase 1 crop fix
  moved the shape baseline from 10 to 11 disagreements, changed the membership,
  and flipped `s0:A1 TOP` from OUT to IN, with only the image border changing.
  That is phase 3's corner-placement hypothesis demonstrated ahead of phase 3,
  and it means shape counts are only comparable within one pipeline config.
  (b) Checked IN/OUT against an independent chord-deviation sign: 0 mismatches
  in 48, so the convention is sound and there is no sign bug to chase. Deviation
  magnitude turns out to be a confidence measure, four of the five lowest are in
  the disagreement list.
- 2026-07-24 : hand annotation returned with all 48 shapes confirmed (pairs
  still pending). Copied it into the repo as `annotation.yaml`, since `cache/`
  is gitignored and this is irreplaceable hand-authored data. Baseline against
  truth: x1 41/48, x2 42/48, x4 40/48, x5 42/48, majority vote 43/48. One of the
  five vote errors (`s2:A1 LEFT`) is unanimous across all four conditions, which
  confirms D13's rejected alternative: trusting the vote for unanimous segments
  would have put a wrong label into the truth file with nothing flagging it.
- 2026-07-24 : walked back the phase 2 claim that chord deviation is a
  confidence measure. It tracks instability but not correctness (median 19.7 px
  right vs 11.9 px wrong, but only 1 of 5 errors is in the 5 lowest). Not usable
  as a gate.
- 2026-07-24 : blur sweep against truth is flat from ksize 21 to 3 (43/48 ->
  42/48) with piece counts stable, so contour fidelity does not drive shape
  accuracy; corner placement does, which matches the annotator's own comments on
  `s0:A1` and `s2:B1`. Blur is still worth ~30% of contour area (4138 vs 6043
  px^2 on s2:A1) and should be a phase 7 lever for the *score*, because an
  inward shift adds rather than cancels between a tab and its socket. Also
  corrected the annotator's "high erosion" diagnosis: on the mask path the
  binary is background=255, so erode grows pieces and dilate shrinks them,
  measured erosion-only 71x105 vs dilation-only 64x86.
- 2026-07-24 : found an unrelated pre-existing flake,
  `test_printed_at_defaults_to_today` compares `date.today()` (local) against
  `datetime.now(tz=UTC).date()`, so it fails nightly between local and UTC
  midnight. Left alone as out of scope; needs a decision.
