"""Render the hand-annotation sheet for the 12 physical pieces.

Phase 2's deliverable and the effort's single hand-off (D12). It comes back
carrying two things:

- the confirmed ``IN``/``OUT``/``EDGE`` per segment (D13), which is phase 3's
  acceptance criterion,
- the true pairs (D15), which become phase 4's truth file.

Both are judgements over the same 12 pieces, so they are collected once.

Each piece is drawn with its four segments in distinct colours and its majority
vote across the four capture conditions pre-filled, so the answer can be written
without going back to the photos. Segments where the four conditions disagree
are flagged: those are the ones actually worth a careful look.

Needs ``build_corpus.py`` to have run first.

Run: ``uv run python scratch_space/24_investigate_matching/build_annotation_sheet.py``
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

import cv2
import numpy as np
from loguru import logger as lg

from snap_fit.aruco.board_config_resolver import load_sheet_config_by_id
from snap_fit.aruco.sheet_metadata import SheetMetadataDecoder
from snap_fit.config.types import EdgePos
from snap_fit.image.utils import load_image
from snap_fit.params.snap_fit_params import get_snap_fit_params
from snap_fit.persistence.sqlite_store import DatasetStore
from snap_fit.puzzle.sheet_aruco import SheetAruco

if TYPE_CHECKING:
    from pathlib import Path

    from snap_fit.puzzle.piece import Piece

CORPUS_TAG = "gds_corpus"
# Crop rendered from x1: it and x5 agree throughout the bbox table, and x1
# carries the least digital upscale of the four conditions.
RENDER_CONDITION = "x1"
SCALE = 4
CELL_PAD = 130
N_CONDITIONS = 4

EDGE_COLOURS: dict[EdgePos, tuple[int, int, int]] = {
    EdgePos.TOP: (60, 60, 235),  # red
    EdgePos.RIGHT: (60, 200, 60),  # green
    EdgePos.BOTTOM: (235, 140, 40),  # blue
    EdgePos.LEFT: (40, 200, 235),  # yellow
}
FONT = cv2.FONT_HERSHEY_SIMPLEX


def majority_shapes(
    db_path: Path,
) -> dict[tuple[int, str], dict[EdgePos, tuple[str, bool, list[str]]]]:
    """Vote each segment's shape across the four capture conditions.

    Returns ``{(sheet_index, label): {edge: (winner, is_split, all_votes)}}``.
    A split means the four conditions did not agree, which is the phase 3
    finding restated per segment: 11 of 48 do not.
    """
    with DatasetStore(db_path) as store:
        sheets = {s.sheet_id: s for s in store.load_sheets()}
        pieces = store.load_pieces()

    votes: dict[tuple[int, str], dict[EdgePos, list[str]]] = {}
    for piece in pieces:
        sheet = sheets[piece.piece_id.sheet_id]
        if sheet.metadata is None or piece.label is None:
            msg = f"{piece.piece_id} lacks metadata or label; rerun build_corpus"
            raise RuntimeError(msg)
        key = (sheet.metadata.sheet_index, piece.label)
        for edge in EdgePos:
            shape = piece.segment_shapes[edge.value]
            votes.setdefault(key, {}).setdefault(edge, []).append(shape)

    result: dict[tuple[int, str], dict[EdgePos, tuple[str, bool, list[str]]]] = {}
    for key, per_edge in votes.items():
        result[key] = {}
        for edge, shapes in per_edge.items():
            counts = Counter(shapes)
            winner, top = counts.most_common(1)[0]
            result[key][edge] = (winner, top < N_CONDITIONS, sorted(shapes))
    return result


def load_render_pieces() -> dict[tuple[int, str], Piece]:
    """Re-ingest the render-condition captures to get drawable Piece objects."""
    paths = get_snap_fit_params().paths
    sheets_fol = paths.data_fol / "greendemo_small" / "sheets"

    pieces: dict[tuple[int, str], Piece] = {}
    for img_fp in sorted(sheets_fol.glob(f"*_{RENDER_CONDITION}.jpg")):
        metadata = SheetMetadataDecoder().decode(load_image(img_fp))
        if metadata is None:
            msg = f"no QR decoded from {img_fp.name}"
            raise RuntimeError(msg)
        config = load_sheet_config_by_id(metadata.board_config_id)
        sheet = SheetAruco(config).load_sheet(img_fp)
        for piece in sheet.pieces:
            pieces[(metadata.sheet_index, piece.label or "?")] = piece
    return pieces


def draw_piece_cell(
    piece: Piece,
    key: tuple[int, str],
    shapes: dict[EdgePos, tuple[str, bool, list[str]]],
) -> np.ndarray:
    """Render one piece with coloured segments and its pre-filled vote."""
    img = cv2.resize(
        piece.img_orig,
        None,
        fx=SCALE,
        fy=SCALE,
        interpolation=cv2.INTER_NEAREST,
    )
    h, w = img.shape[:2]
    cell = np.full((h + 2 * CELL_PAD, w + 2 * CELL_PAD, 3), 250, dtype=np.uint8)
    cell[CELL_PAD : CELL_PAD + h, CELL_PAD : CELL_PAD + w] = img

    # Each segment in its own colour, so a physical knob maps to an EdgePos
    # without the annotator having to guess the orientation convention.
    for edge, segment in piece.segments.items():
        pts = (segment.points * SCALE).astype(np.int32) + CELL_PAD
        cv2.polylines(
            cell, [pts], isClosed=False, color=EDGE_COLOURS[edge], thickness=3
        )

    cv2.putText(
        cell, f"s{key[0]}:{key[1]}", (12, 38), FONT, 1.0, (20, 20, 20), 2, cv2.LINE_AA
    )

    # Vote text placed on the side of the cell matching the edge it describes.
    positions = {
        EdgePos.TOP: (CELL_PAD, CELL_PAD - 46),
        EdgePos.BOTTOM: (CELL_PAD, CELL_PAD + h + 46),
        EdgePos.LEFT: (12, CELL_PAD + h // 2),
        EdgePos.RIGHT: (CELL_PAD + w + 12, CELL_PAD + h // 2),
    }
    for edge, (winner, is_split, all_votes) in shapes.items():
        colour = (0, 0, 200) if is_split else EDGE_COLOURS[edge]
        x, y = positions[edge]
        lines = [f"{edge.name}: {winner.upper()}"]
        if is_split:
            # On its own line: appended inline it ran off the right-hand cells.
            lines.append(f"  SPLIT {'/'.join(v.upper() for v in all_votes)}")
        for i, line in enumerate(lines):
            (tw, _th), _ = cv2.getTextSize(line, FONT, 0.62, 2)
            cv2.putText(
                cell,
                line,
                (min(x, cell.shape[1] - tw - 8), y + i * 26),
                FONT,
                0.62,
                colour,
                2,
                cv2.LINE_AA,
            )
    return cell


def build_stub(
    shapes: dict[tuple[int, str], dict[EdgePos, tuple[str, bool, list[str]]]],
) -> str:
    """Write the fill-in stub, pre-filled with the vote."""
    lines = [
        "# hand annotation - 12 physical pieces, 48 segments",
        "#",
        "# 1. shapes: confirm or correct every line. Pre-filled with the majority",
        "#    vote across the four capture conditions; lines marked SPLIT are the",
        "#    ones where the conditions disagreed, so check those first. The vote",
        "#    is only a starting point, a unanimous wrong answer is exactly what a",
        "#    systematic classifier bug produces (D13).",
        "#",
        "# 2. pairs: list every pair of segments that physically interlock, one per",
        "#    line, as 's0:A1 RIGHT <-> s2:B1 LEFT'. Groups are disjoint (Q11).",
        "#    Two segments should end up with no partner at all (the flat ones).",
        "",
        "shapes:",
    ]
    for key in sorted(shapes):
        lines.append(f"  # --- s{key[0]}:{key[1]} ---")
        for edge in EdgePos:
            winner, is_split, all_votes = shapes[key][edge]
            flag = (
                f"   # SPLIT: {'/'.join(v.upper() for v in all_votes)}"
                if is_split
                else ""
            )
            lines.append(f"  s{key[0]}:{key[1]} {edge.name}: {winner.upper()}{flag}")
    lines += [
        "",
        "pairs:",
        "  # - s0:A1 RIGHT <-> s2:B1 LEFT",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    """Build the annotation image and its fill-in stub."""
    corpus_fol = get_snap_fit_params().paths.cache_fol / CORPUS_TAG
    db_path = corpus_fol / "dataset.db"
    if not db_path.exists():
        msg = f"no corpus at {db_path}; run build_corpus.py first"
        raise FileNotFoundError(msg)

    shapes = majority_shapes(db_path)
    pieces = load_render_pieces()
    missing = set(shapes) - set(pieces)
    if missing:
        msg = f"no render crop for {sorted(missing)}"
        raise RuntimeError(msg)

    n_split = sum(
        1
        for per_edge in shapes.values()
        for _w, is_split, _v in per_edge.values()
        if is_split
    )
    lg.info(f"{n_split} of {4 * len(shapes)} segments split across conditions")

    # One row per sheet, one column per slot, matching the physical board.
    cells = {key: draw_piece_cell(pieces[key], key, shapes[key]) for key in shapes}
    cell_h = max(c.shape[0] for c in cells.values())
    cell_w = max(c.shape[1] for c in cells.values())
    rows = sorted({k[0] for k in cells})
    cols = sorted({k[1] for k in cells})

    grid = np.full((cell_h * len(rows), cell_w * len(cols), 3), 235, dtype=np.uint8)
    for r, sheet_index in enumerate(rows):
        for c, label in enumerate(cols):
            cell = cells[(sheet_index, label)]
            # Pieces have different padded sizes, so centre each cell in its
            # slot rather than leaving ragged gaps on one side.
            y = r * cell_h + (cell_h - cell.shape[0]) // 2
            x = c * cell_w + (cell_w - cell.shape[1]) // 2
            grid[y : y + cell.shape[0], x : x + cell.shape[1]] = cell

    out_img = corpus_fol / "annotation_sheet.png"
    out_stub = corpus_fol / "annotation_stub.yaml"
    cv2.imwrite(str(out_img), grid)
    out_stub.write_text(build_stub(shapes))

    lg.success(f"annotation sheet: {out_img}  ({grid.shape[1]}x{grid.shape[0]})")
    lg.success(f"fill-in stub:     {out_stub}")


if __name__ == "__main__":
    main()
