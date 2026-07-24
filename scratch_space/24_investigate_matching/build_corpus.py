"""Ingest the 12 greendemo_small captures into a corpus keyed by physical piece.

Phase 2 of the matching investigation. Every later phase compares the same
physical piece across capture conditions, so pieces must be joinable by
``(sheet_index, label)`` rather than by filename or by ``PieceId.piece_id``,
which is a per-capture ordinal over descending contour area and reorders between
captures.

Writes, under ``cache/gds_corpus/``:

- ``dataset.db``     sheets + pieces, via the normal ``DatasetStore``
- ``sheets/*.jpg``   the processed (rectified, cropped) sheet images
- ``captures.json``  per-capture EXIF condition, the grouping key for phase 5

Run: ``uv run python scratch_space/24_investigate_matching/build_corpus.py``
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Any

import cv2
from PIL import ExifTags
from PIL import Image
from loguru import logger as lg

from snap_fit.aruco.board_config_resolver import load_sheet_config_by_id
from snap_fit.aruco.sheet_metadata import SheetMetadataDecoder
from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.data_models.sheet_record import SheetRecord
from snap_fit.image.utils import load_image
from snap_fit.params.snap_fit_params import get_snap_fit_params
from snap_fit.persistence.sqlite_store import DatasetStore
from snap_fit.puzzle.sheet_aruco import SheetAruco

if TYPE_CHECKING:
    from pathlib import Path

    from snap_fit.puzzle.sheet import Sheet

CORPUS_TAG = "gds_corpus"
EXPECTED_CAPTURES = 12
EXPECTED_LABELS = {"A1", "A2", "B1", "B2"}
# Worst observed centroid spread across a sheet's captures is 4 px (thickness
# parallax, see 00_start.md). 8 leaves room without letting a real mix-up pass.
CENTROID_TOLERANCE_PX = 8


class CorpusAssertionError(RuntimeError):
    """Raised when the ingested corpus violates a structural expectation."""


def read_capture_condition(img_fp: Path) -> dict[str, Any]:
    """Extract the EXIF fields that identify the capture condition.

    Distance, digital zoom and camera app all vary together across these
    captures, so the condition is recorded as a whole rather than reduced to a
    single "zoom" axis that does not exist (D6).
    """
    with Image.open(img_fp) as img:
        exif = img.getexif()
        # TAGS.get falls back to the raw numeric key for tags it does not name,
        # so stringify to keep one key type.
        tags: dict[str, Any] = {
            str(ExifTags.TAGS.get(k, k)): v for k, v in exif.items()
        }
        tags |= {
            str(ExifTags.TAGS.get(k, k)): v
            for k, v in exif.get_ifd(ExifTags.IFD.Exif).items()
        }

    def num(key: str) -> float | None:
        value = tags.get(key)
        return None if value is None else float(value)

    software = tags.get("Software")
    return {
        "zoom_tag": img_fp.stem.rsplit("_x", 1)[-1],
        "app": "google_camera" if software else "open_camera",
        "hdr_plus": bool(software),
        "software": software,
        "focal_length_mm": num("FocalLength"),
        "focal_35mm_equiv": num("FocalLengthIn35mmFilm"),
        "digital_zoom_ratio": num("DigitalZoomRatio"),
        "subject_distance_m": num("SubjectDistance"),
        "iso": tags.get("ISOSpeedRatings"),
        "exposure_time_s": num("ExposureTime"),
    }


def ingest_one(img_fp: Path) -> tuple[Sheet, int]:
    """Load one capture, returning its Sheet and the sheet_index from its QR."""
    metadata = SheetMetadataDecoder().decode(load_image(img_fp))
    if metadata is None:
        msg = f"no QR metadata decoded from {img_fp.name}; cannot resolve a config"
        raise CorpusAssertionError(msg)
    config = load_sheet_config_by_id(metadata.board_config_id)
    sheet = SheetAruco(config).load_sheet(img_fp)
    return sheet, metadata.sheet_index


def check_capture(sheet: Sheet) -> None:
    """Assert one capture yielded the expected pieces and labels."""
    labels = [p.label for p in sheet.pieces]
    if len(sheet.pieces) != len(EXPECTED_LABELS):
        msg = (
            f"{sheet.sheet_id}: expected {len(EXPECTED_LABELS)} pieces, "
            f"got {len(sheet.pieces)} with labels {labels}"
        )
        raise CorpusAssertionError(msg)
    if set(labels) != EXPECTED_LABELS:
        msg = f"{sheet.sheet_id}: expected labels {EXPECTED_LABELS}, got {labels}"
        raise CorpusAssertionError(msg)


def check_centroid_agreement(
    centroids: dict[tuple[int, str], list[tuple[str, int, int]]],
) -> None:
    """Assert each physical piece lands in the same board-space spot everywhere.

    This is what makes ``(sheet_index, label)`` safe to join on. If labelling
    ever regresses, two different pieces silently share a key, and every later
    phase compares the wrong things; catching it here is the whole point.
    """
    for (sheet_index, label), seen in sorted(centroids.items()):
        if len(seen) != 4:  # noqa: PLR2004
            msg = (
                f"s{sheet_index}:{label} appears in {len(seen)} captures, "
                f"expected 4: {[z for z, _x, _y in seen]}"
            )
            raise CorpusAssertionError(msg)
        xs = [x for _z, x, _y in seen]
        ys = [y for _z, _x, y in seen]
        spread = max(max(xs) - min(xs), max(ys) - min(ys))
        if spread > CENTROID_TOLERANCE_PX:
            msg = (
                f"s{sheet_index}:{label} centroid spread {spread} px exceeds "
                f"{CENTROID_TOLERANCE_PX} px across captures: {seen}"
            )
            raise CorpusAssertionError(msg)


def main() -> None:
    """Ingest all captures, persist them, and run the structural checks."""
    paths = get_snap_fit_params().paths
    sheets_fol = paths.data_fol / "greendemo_small" / "sheets"
    corpus_fol = paths.cache_fol / CORPUS_TAG
    img_fol = corpus_fol / "sheets"

    photos = sorted(sheets_fol.glob("*__gds_p*.jpg"))
    if not photos:
        # Without this the run "succeeds" with an empty corpus, and the failure
        # only surfaces later as a confusing error in a downstream script.
        msg = (
            f"no captures matching '*__gds_p*.jpg' in {sheets_fol}. "
            "Copy the 12 renamed photos there; note that greendemo_small.zip "
            "holds them under their original camera names, without the "
            "__gds_pM_xZ suffix this pipeline parses the condition from."
        )
        raise CorpusAssertionError(msg)
    if len(photos) != EXPECTED_CAPTURES:
        lg.warning(f"expected {EXPECTED_CAPTURES} captures, found {len(photos)}")
    lg.info(f"ingesting {len(photos)} captures from {sheets_fol}")
    # Created only once the inputs check out, so a failed run leaves no
    # half-built corpus folder behind to confuse the next one.
    img_fol.mkdir(parents=True, exist_ok=True)

    sheet_records: list[SheetRecord] = []
    piece_records: list[PieceRecord] = []
    captures: dict[str, dict[str, Any]] = {}
    centroids: dict[tuple[int, str], list[tuple[str, int, int]]] = {}

    for img_fp in photos:
        sheet, sheet_index = ingest_one(img_fp)
        check_capture(sheet)

        # The processed sheet, not the original photo: piece coordinates are in
        # cropped-sheet space and cannot be applied to the photo.
        cv2.imwrite(str(img_fol / f"{sheet.sheet_id}.jpg"), sheet.img_orig)

        condition = read_capture_condition(img_fp)
        condition["sheet_index"] = sheet_index
        captures[sheet.sheet_id] = condition

        sheet_records.append(SheetRecord.from_sheet(sheet, data_root=paths.root_fol))
        for piece in sheet.pieces:
            piece_records.append(PieceRecord.from_piece(piece))
            cx, cy = piece.centroid_in_sheet
            key = (sheet_index, piece.label or "?")
            centroids.setdefault(key, []).append(
                (
                    condition["zoom_tag"],
                    cx + sheet.crop_offset,
                    cy + sheet.crop_offset,
                )
            )

        lg.info(
            f"  {img_fp.name}: sheet_index={sheet_index} "
            f"pieces={len(sheet.pieces)} condition={condition['zoom_tag']}"
        )

    check_centroid_agreement(centroids)

    with DatasetStore(corpus_fol / "dataset.db") as store:
        store.save_sheets(sheet_records)
        store.save_pieces(piece_records)
    (corpus_fol / "captures.json").write_text(json.dumps(captures, indent=2))

    lg.success(
        f"corpus written to {corpus_fol}: {len(sheet_records)} captures, "
        f"{len(piece_records)} pieces, {len(centroids)} physical pieces"
    )


if __name__ == "__main__":
    main()
