"""Score the shape classifier against the hand-confirmed truth.

Phase 3's baseline. Answers three things the majority vote alone could not:

- how accurate each capture condition is, per segment,
- how accurate the majority vote is, and crucially how often it is
  *confidently* wrong (all four conditions agree on the wrong answer, so
  nothing flags it),
- whether chord deviation magnitude predicts error, which would make it a
  usable confidence signal to replace ``flat_th = 1.5 * std``.

Needs ``build_corpus.py`` to have run and ``annotation.yaml`` to carry shapes.

Run: ``uv run python scratch_space/24_investigate_matching/shape_baseline.py``
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import yaml
from loguru import logger as lg

from snap_fit.aruco.board_config_resolver import load_sheet_config_by_id
from snap_fit.aruco.sheet_metadata import SheetMetadataDecoder
from snap_fit.config.types import EdgePos
from snap_fit.image.utils import load_image
from snap_fit.params.snap_fit_params import get_snap_fit_params
from snap_fit.persistence.sqlite_store import DatasetStore
from snap_fit.puzzle.sheet_aruco import SheetAruco

CORPUS_TAG = "gds_corpus"
ANNOTATION = Path(__file__).parent / "annotation.yaml"
DEVIATION_CONDITION = "x1"
CONDITIONS = ["1", "2", "4", "5"]


def load_truth() -> dict[tuple[int, str, EdgePos], str]:
    """Parse the hand-confirmed shape per segment."""
    raw = yaml.safe_load(ANNOTATION.read_text())["shapes"]
    truth: dict[tuple[int, str, EdgePos], str] = {}
    for key, shape in raw.items():
        piece, edge_name = key.rsplit(" ", 1)
        sheet_index, label = piece.split(":")
        truth[(int(sheet_index[1:]), label, EdgePos[edge_name])] = shape.upper()
    return truth


def require_corpus() -> Path:
    """Return the corpus folder, or explain how to build it."""
    corpus_fol = get_snap_fit_params().paths.cache_fol / CORPUS_TAG
    missing = [
        name
        for name in ("captures.json", "dataset.db")
        if not (corpus_fol / name).is_file()
    ]
    if missing:
        msg = (
            f"corpus incomplete at {corpus_fol} (missing {', '.join(missing)}). "
            "Run build_corpus.py first; cache/ is gitignored, so a fresh clone "
            "has to rebuild it from the photos."
        )
        raise FileNotFoundError(msg)
    return corpus_fol


def load_predictions() -> dict[tuple[int, str, EdgePos], dict[str, str]]:
    """Per-segment shape from each capture condition."""
    corpus_fol = require_corpus()
    captures = json.loads((corpus_fol / "captures.json").read_text())
    with DatasetStore(corpus_fol / "dataset.db") as store:
        sheets = {s.sheet_id: s for s in store.load_sheets()}
        pieces = store.load_pieces()

    preds: dict[tuple[int, str, EdgePos], dict[str, str]] = {}
    for piece in pieces:
        sheet_id = piece.piece_id.sheet_id
        sheet = sheets[sheet_id]
        if sheet.metadata is None or piece.label is None:
            continue
        zoom = captures[sheet_id]["zoom_tag"]
        for edge in EdgePos:
            key = (sheet.metadata.sheet_index, piece.label, edge)
            shape = piece.segment_shapes[edge.value].upper()
            preds.setdefault(key, {})[zoom] = shape
    return preds


def chord_deviations() -> dict[tuple[int, str, EdgePos], float]:
    """Largest perpendicular deviation from the chord, signed outward."""
    sheets_fol = get_snap_fit_params().paths.data_fol / "greendemo_small" / "sheets"
    out: dict[tuple[int, str, EdgePos], float] = {}
    for img_fp in sorted(sheets_fol.glob(f"*_{DEVIATION_CONDITION}.jpg")):
        metadata = SheetMetadataDecoder().decode(load_image(img_fp))
        if metadata is None:
            continue
        config = load_sheet_config_by_id(metadata.board_config_id)
        sheet = SheetAruco(config).load_sheet(img_fp)
        for piece in sheet.pieces:
            centre = np.array(piece.contour.centroid, dtype=float)
            for edge, segment in piece.segments.items():
                pts = segment.points.reshape(-1, 2).astype(float)
                a, b = pts[0], pts[-1]
                chord = b - a
                norm = float(np.linalg.norm(chord))
                if norm == 0:
                    continue
                normal = np.array([-chord[1], chord[0]]) / norm
                if np.dot(normal, (a + b) / 2 - centre) < 0:
                    normal = -normal
                offs = (pts - a) @ normal
                key = (metadata.sheet_index, piece.label or "?", edge)
                out[key] = float(offs[np.argmax(np.abs(offs))])
    return out


def main() -> None:
    """Report per-condition and majority-vote accuracy against truth."""
    truth = load_truth()
    preds = load_predictions()
    devs = chord_deviations()

    # --- per condition -----------------------------------------------------
    print("accuracy per capture condition, against hand-confirmed truth")
    for zoom in CONDITIONS:
        wrong = [k for k, t in truth.items() if preds[k].get(zoom) != t]
        n = len(truth)
        print(
            f"  x{zoom}: {n - len(wrong):>2}/{n}  ({100 * (n - len(wrong)) / n:.0f}%)"
        )

    # --- majority vote -----------------------------------------------------
    majority: dict[tuple[int, str, EdgePos], tuple[str, bool]] = {}
    for key, per_zoom in preds.items():
        votes = [per_zoom[z] for z in CONDITIONS if z in per_zoom]
        winner, top = Counter(votes).most_common(1)[0]
        majority[key] = (winner, top == len(votes))

    wrong = [(k, majority[k][0], t) for k, t in truth.items() if majority[k][0] != t]
    unanimous_wrong = [(k, w, t) for k, w, t in wrong if majority[k][1]]
    n = len(truth)
    print(f"\nmajority vote: {n - len(wrong)}/{n} ({100 * (n - len(wrong)) / n:.0f}%)")
    print(f"  of the {len(wrong)} wrong, {len(unanimous_wrong)} were unanimous,")
    print("  i.e. all four conditions agreed on the wrong answer and nothing")
    print("  flagged them for review.\n")

    print(f"{'segment':<18} {'truth':<6} {'vote':<6} {'votes':<22} {'dev px':>7} flag")
    for key, winner, t in sorted(wrong, key=lambda r: str(r[0])):
        sheet_index, label, edge = key
        votes = "/".join(preds[key][z] for z in CONDITIONS if z in preds[key])
        flag = "UNANIMOUS" if majority[key][1] else "split"
        print(
            f"s{sheet_index}:{label} {edge.name:<8} {t:<6} {winner:<6} "
            f"{votes:<22} {devs.get(key, float('nan')):>7.1f} {flag}"
        )

    # --- is deviation a usable confidence signal? --------------------------
    ok_devs = [abs(devs[k]) for k in truth if k in devs and majority[k][0] == truth[k]]
    bad_devs = [abs(devs[k]) for k in truth if k in devs and majority[k][0] != truth[k]]
    print(
        f"\nmedian |deviation|: correct {np.median(ok_devs):.1f} px, "
        f"wrong {np.median(bad_devs):.1f} px"
    )
    low = sorted(truth, key=lambda k: abs(devs.get(k, 1e9)))[: len(wrong)]
    hits = sum(1 for k in low if majority[k][0] != truth[k])
    print(
        f"the {len(wrong)} lowest-deviation segments contain {hits} of the "
        f"{len(wrong)} vote errors"
    )
    lg.info("baseline complete")


if __name__ == "__main__":
    main()
