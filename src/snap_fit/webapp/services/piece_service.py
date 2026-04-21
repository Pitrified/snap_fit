"""Service layer for piece operations.

Integrates with SheetManager for persistence and data access.
"""

from functools import lru_cache
from pathlib import Path

import cv2
from loguru import logger as lg
import numpy as np

from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig
from snap_fit.config.types import EDGE_ENDS_TO_CORNER
from snap_fit.config.types import CornerPos
from snap_fit.config.types import EdgePos
from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.data_models.sheet_record import SheetRecord
from snap_fit.persistence.sqlite_store import DatasetStore
from snap_fit.puzzle.sheet_aruco import SheetAruco
from snap_fit.puzzle.sheet_manager import SheetManager

_ROTATE_MAP: dict[int, int] = {
    90: cv2.ROTATE_90_CLOCKWISE,
    180: cv2.ROTATE_180,
    270: cv2.ROTATE_90_COUNTERCLOCKWISE,
}


class PieceService:
    """Service for piece and sheet data operations."""

    def __init__(
        self,
        cache_dir: Path,
        data_dir: Path | None = None,
        dataset_tag: str | None = None,
    ) -> None:
        """Initialize service with cache directory.

        Args:
            cache_dir: Root cache directory.  Each dataset lives under
                ``cache_dir / sheets_tag /`` with its own dataset.db and
                contours/ sub-directory.
            data_dir: Root data directory used to resolve sheet image paths.
            dataset_tag: When set, all queries are scoped to this dataset only.
        """
        self.cache_dir = cache_dir
        self.data_dir = data_dir
        self.dataset_tag = dataset_tag

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _tag_dir(self, sheets_tag: str) -> Path:
        """Return the cache sub-directory for a specific dataset tag."""
        return self.cache_dir / sheets_tag

    def _all_tag_dirs(self) -> list[Path]:
        """Return dataset sub-directories to query.

        When dataset_tag is set, returns only that tag's directory.
        Otherwise returns all existing sub-directories.
        """
        if not self.cache_dir.exists():
            return []
        if self.dataset_tag is not None:
            tag_dir = self.cache_dir / self.dataset_tag
            return [tag_dir] if tag_dir.is_dir() else []
        return [p for p in self.cache_dir.iterdir() if p.is_dir()]

    def _db_path(self, tag_dir: Path) -> Path:
        """Return the SQLite database path for a dataset tag directory."""
        return tag_dir / "dataset.db"

    def list_sheets(self) -> list[SheetRecord]:
        """Return all sheet records aggregated across every cached dataset."""
        records: list[SheetRecord] = []
        for tag_dir in self._all_tag_dirs():
            db_path = self._db_path(tag_dir)
            if not db_path.exists():
                continue
            with DatasetStore(db_path) as store:
                records.extend(store.load_sheets())
        return records

    def list_pieces(self) -> list[PieceRecord]:
        """Return all piece records aggregated across every cached dataset."""
        records: list[PieceRecord] = []
        for tag_dir in self._all_tag_dirs():
            db_path = self._db_path(tag_dir)
            if not db_path.exists():
                continue
            with DatasetStore(db_path) as store:
                records.extend(store.load_pieces())
        return records

    def get_piece(self, piece_id: str) -> PieceRecord | None:
        """Retrieve a single piece by ID, searching all cached datasets.

        Args:
            piece_id: The piece ID (format: sheet_id:piece_idx).

        Returns:
            PieceRecord if found, None otherwise.
        """
        for tag_dir in self._all_tag_dirs():
            db_path = self._db_path(tag_dir)
            if not db_path.exists():
                continue
            with DatasetStore(db_path) as store:
                record = store.load_piece(piece_id)
                if record is not None:
                    return record
        return None

    def get_sheet(self, sheet_id: str) -> SheetRecord | None:
        """Retrieve a single sheet by ID, searching all cached datasets.

        Args:
            sheet_id: The sheet ID.

        Returns:
            SheetRecord if found, None otherwise.
        """
        for tag_dir in self._all_tag_dirs():
            db_path = self._db_path(tag_dir)
            if not db_path.exists():
                continue
            with DatasetStore(db_path) as store:
                record = store.load_sheet(sheet_id)
                if record is not None:
                    return record
        return None

    def ingest_sheets(self, sheets_tag: str, data_dir: Path) -> dict:
        """Load sheets for a named dataset and persist to cache.

        Follows the latest pattern:
        - Config is loaded from
          `data_dir/{sheets_tag}/{sheets_tag}_SheetArucoConfig.json`
        - Images are loaded from `data_dir/{sheets_tag}/sheets/*.jpg`

        Args:
            sheets_tag: Dataset identifier (e.g. "oca", "milano1").
            data_dir: Root data directory (resolved from settings).

        Returns:
            Summary dict with sheets_tag, sheets_ingested, pieces_detected, cache_path.
        """
        sheets_base_fol = data_dir / sheets_tag
        img_fol = sheets_base_fol / "sheets"
        config_fp = sheets_base_fol / f"{sheets_tag}_SheetArucoConfig.json"

        lg.info(f"Ingesting dataset '{sheets_tag}' from {sheets_base_fol}")

        if not config_fp.exists():
            msg = f"SheetArucoConfig not found: {config_fp}"
            raise FileNotFoundError(msg)
        if not img_fol.is_dir():
            msg = f"Image folder not found: {img_fol}"
            raise FileNotFoundError(msg)

        sheet_config = SheetArucoConfig.model_validate_json(config_fp.read_text())
        sheet_aruco = SheetAruco(sheet_config)
        aruco_loader = sheet_aruco.load_sheet

        manager = SheetManager()
        manager.add_sheets(
            folder_path=img_fol, pattern="*.jpg", loader_func=aruco_loader
        )

        # Persist to per-tag cache sub-directory
        tag_dir = self._tag_dir(sheets_tag)
        tag_dir.mkdir(parents=True, exist_ok=True)
        manager.save_metadata(tag_dir / "metadata.json")
        manager.save_metadata_db(tag_dir / "dataset.db")
        manager.save_contour_cache(tag_dir / "contours")
        manager.save_sheet_images(tag_dir / "sheets")

        records = manager.to_records()
        return {
            "sheets_tag": sheets_tag,
            "sheets_ingested": len(records["sheets"]),
            "pieces_detected": len(records["pieces"]),
            "cache_path": str(tag_dir),
        }

    def get_pieces_for_sheet(self, sheet_id: str) -> list[PieceRecord]:
        """Get all pieces belonging to a specific sheet, across all datasets.

        Args:
            sheet_id: The sheet ID to filter by.

        Returns:
            List of PieceRecord objects for the sheet.
        """
        for tag_dir in self._all_tag_dirs():
            db_path = self._db_path(tag_dir)
            if not db_path.exists():
                continue
            with DatasetStore(db_path) as store:
                records = store.load_pieces_for_sheet(sheet_id)
                if records:
                    return records
        return []

    def get_piece_img(
        self,
        piece_id: str,
        size: int | None = None,
        orientation: int = 0,
        label: str | None = None,
    ) -> bytes | None:
        """Load processed sheet image, crop piece region, encode as PNG.

        The processed (rectified + cropped) sheet image is loaded from the
        cache, not the original photo. Piece coordinates (``sheet_origin``,
        ``padded_size``) are in the processed-sheet coordinate space.

        Args:
            piece_id: Piece identifier.
            size: Optional max dimension for resizing (preserves aspect ratio).
            orientation: Rotation in degrees (0, 90, 180, 270).
            label: Optional text label to burn onto the image before rotation.

        Returns:
            PNG bytes, or None if piece or sheet image not found.
        """
        if orientation not in (0, 90, 180, 270):
            msg = "orientation must be 0, 90, 180, or 270"
            raise ValueError(msg)

        piece = self.get_piece(piece_id)
        if piece is None:
            return None

        # Load the processed (rectified + cropped) sheet image from cache.
        sheet_img = self._load_processed_sheet(piece.piece_id.sheet_id)
        if sheet_img is None:
            lg.warning(f"Processed sheet image not found for {piece.piece_id.sheet_id}")
            return None

        x0, y0 = piece.sheet_origin
        pw, ph = piece.padded_size
        if pw > 0 and ph > 0:
            crop = sheet_img[y0 : y0 + ph, x0 : x0 + pw]
        else:
            # Fallback for old data without padded_size
            cx, cy, cw, ch = piece.contour_region
            est_w = 2 * cx + cw
            est_h = 2 * cy + ch
            crop = sheet_img[y0 : y0 + est_h, x0 : x0 + est_w]

        if crop.size == 0:
            lg.warning(f"Empty crop for piece {piece_id}")
            return None

        if label is not None:
            crop = _burn_label(crop, label)

        if orientation != 0:
            crop = cv2.rotate(crop, _ROTATE_MAP[orientation])

        if size is not None and size > 0:
            h_crop, w_crop = crop.shape[:2]
            scale = size / max(h_crop, w_crop)
            new_w = max(1, int(w_crop * scale))
            new_h = max(1, int(h_crop * scale))
            crop = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_AREA)

        ok, buf = cv2.imencode(".png", crop)
        if not ok:
            return None
        return buf.tobytes()

    def get_piece_inspection_img(
        self,
        piece_id: str,
        size: int | None = None,
    ) -> bytes | None:
        """Return a PNG of the piece crop with contour segment and corner overlays.

        Loads the contour from the binary cache and draws each segment in a
        distinct colour, then marks the four corner points with labelled circles
        and prints the shape label (IN/OUT/EDGE/WEIRD) at the midpoint of each
        segment.

        Args:
            piece_id: Piece identifier string (``sheet_id:piece_idx``).
            size: Optional max dimension for resizing (preserves aspect ratio).

        Returns:
            PNG bytes, or None if the piece or its contour cache is not found.
        """
        crop, piece, contour_pts, corner_indices = self._load_inspection_data(piece_id)
        if (
            crop is None
            or piece is None
            or contour_pts is None
            or (corner_indices is None)
        ):
            return None

        crop = _draw_inspection_overlay(crop, contour_pts, corner_indices, piece)

        if size is not None and size > 0:
            h_crop, w_crop = crop.shape[:2]
            scale = size / max(h_crop, w_crop)
            new_w = max(1, int(w_crop * scale))
            new_h = max(1, int(h_crop * scale))
            crop = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_AREA)

        ok, buf = cv2.imencode(".png", crop)
        if not ok:
            return None
        return buf.tobytes()

    def _load_inspection_data(
        self,
        piece_id: str,
    ) -> tuple[
        np.ndarray | None,
        PieceRecord | None,
        np.ndarray | None,
        dict[str, int] | None,
    ]:
        """Load and validate all data needed for the inspection overlay.

        Returns a 4-tuple of (crop, piece, contour_pts, corner_indices).
        Any element is None if the data could not be loaded.
        """
        piece = self.get_piece(piece_id)
        if piece is None:
            return None, None, None, None

        sheet_img = self._load_processed_sheet(piece.piece_id.sheet_id)
        if sheet_img is None:
            lg.warning(f"Processed sheet image not found for {piece.piece_id.sheet_id}")
            return None, None, None, None

        x0, y0 = piece.sheet_origin
        pw, ph = piece.padded_size
        if pw > 0 and ph > 0:
            crop = sheet_img[y0 : y0 + ph, x0 : x0 + pw].copy()
        else:
            cx, cy, cw, ch = piece.contour_region
            est_w = 2 * cx + cw
            est_h = 2 * cy + ch
            crop = sheet_img[y0 : y0 + est_h, x0 : x0 + est_w].copy()

        if crop.size == 0:
            lg.warning(f"Empty crop for piece {piece_id}")
            return None, None, None, None

        tag_dir = self._find_tag_dir_for_piece(piece_id)
        if tag_dir is None:
            lg.warning(f"Cannot locate tag dir for piece {piece_id}")
            return None, None, None, None

        contour_dir = tag_dir / "contours"
        try:
            contour_pts, corner_indices = SheetManager.load_contour_for_piece(
                piece.piece_id, contour_dir
            )
        except (FileNotFoundError, KeyError) as exc:
            lg.warning(f"Contour cache not found for {piece_id}: {exc}")
            return None, None, None, None

        return crop, piece, contour_pts, corner_indices

    def _find_tag_dir_for_piece(self, piece_id: str) -> Path | None:
        """Return the tag directory that contains the given piece.

        Args:
            piece_id: Piece identifier string.

        Returns:
            Path to the tag directory, or None if not found.
        """
        for tag_dir in self._all_tag_dirs():
            db_path = self._db_path(tag_dir)
            if not db_path.exists():
                continue
            with DatasetStore(db_path) as store:
                if store.load_piece(piece_id) is not None:
                    return tag_dir
        return None

    def _load_processed_sheet(self, sheet_id: str) -> np.ndarray | None:
        """Load a processed sheet image from the cache.

        Searches all dataset tag directories for a matching sheet image
        at ``cache/{tag}/sheets/{sheet_id}.jpg``.

        Args:
            sheet_id: The sheet identifier.

        Returns:
            The loaded image array, or None if not found.
        """
        for tag_dir in self._all_tag_dirs():
            img_path = tag_dir / "sheets" / f"{sheet_id}.jpg"
            if img_path.exists():
                return _load_sheet_image(str(img_path))
        return None

    def get_match_preview_img(
        self,
        piece_id_a: str,
        edge_a: str,
        orientation_a: int,
        piece_id_b: str,
        edge_b: str,
        orientation_b: int,
        size: int | None = None,
    ) -> bytes | None:
        """Generate a side-by-side match preview image for two piece edges.

        Draws the facing segment on each piece crop (in its placement
        orientation) and composes them side by side on a dark canvas.

        Args:
            piece_id_a: Placed piece identifier.
            edge_a: ``EdgePos.value`` of piece A's edge that faces piece B.
            orientation_a: Placement orientation of piece A (0/90/180/270).
            piece_id_b: Candidate piece identifier.
            edge_b: ``EdgePos.value`` of piece B's edge that faces piece A.
            orientation_b: Placement orientation of piece B (0/90/180/270).
            size: Optional max dimension for the composite image.

        Returns:
            PNG bytes, or None if data could not be loaded.
        """
        crop_a, _, contour_a, corner_a = self._load_inspection_data(piece_id_a)
        crop_b, _, contour_b, corner_b = self._load_inspection_data(piece_id_b)

        if (
            crop_a is None
            or contour_a is None
            or corner_a is None
            or crop_b is None
            or contour_b is None
            or corner_b is None
        ):
            return None

        img_a = _draw_segment_highlight(crop_a, contour_a, corner_a, edge_a)
        img_b = _draw_segment_highlight(crop_b, contour_b, corner_b, edge_b)

        if orientation_a in _ROTATE_MAP:
            img_a = cv2.rotate(img_a, _ROTATE_MAP[orientation_a])
        if orientation_b in _ROTATE_MAP:
            img_b = cv2.rotate(img_b, _ROTATE_MAP[orientation_b])

        canvas = _compose_preview(
            img_a,
            img_b,
            label_a=f"{piece_id_a} ({edge_a})",
            label_b=f"{piece_id_b} ({edge_b})",
        )

        if size is not None and size > 0:
            h, w = canvas.shape[:2]
            scale = size / max(h, w)
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            canvas = cv2.resize(canvas, (new_w, new_h), interpolation=cv2.INTER_AREA)

        ok, buf = cv2.imencode(".png", canvas)
        if not ok:
            return None
        return buf.tobytes()

    def _resolve_img_path(self, img_path: Path) -> Path | None:
        """Resolve an image path to an existing file.

        Tries in order:
        1. Absolute path - use as-is.
        2. Relative path from cwd (handles paths stored without data_root stripping).
        3. Relative to data_dir (handles paths stored relative to data_dir).
        """
        if img_path.is_absolute():
            return img_path
        if img_path.exists():
            return img_path
        if self.data_dir is not None:
            candidate = self.data_dir / img_path
            if candidate.exists():
                return candidate
        return img_path


# Segment colours in BGR: TOP, RIGHT, BOTTOM, LEFT
_SEGMENT_COLORS: dict[str, tuple[int, int, int]] = {
    EdgePos.TOP.value: (0, 0, 255),  # red
    EdgePos.RIGHT.value: (0, 255, 0),  # green
    EdgePos.BOTTOM.value: (255, 0, 0),  # blue
    EdgePos.LEFT.value: (255, 255, 0),  # cyan
}
_CORNER_COLOR: tuple[int, int, int] = (255, 255, 255)
_CORNER_RADIUS = 6
_CORNER_LABEL_ABBREV: dict[str, str] = {
    CornerPos.TOP_LEFT.value: "TL",
    CornerPos.TOP_RIGHT.value: "TR",
    CornerPos.BOTTOM_LEFT.value: "BL",
    CornerPos.BOTTOM_RIGHT.value: "BR",
}


def _draw_inspection_overlay(
    img: np.ndarray,
    contour_pts: np.ndarray,
    corner_indices: dict[str, int],
    piece: PieceRecord,
) -> np.ndarray:
    """Draw coloured segment overlays and labelled corner circles on a piece crop.

    Each segment (TOP/RIGHT/BOTTOM/LEFT) is drawn in its own colour.  Corner
    points are drawn as filled circles with TL/TR/BL/BR labels.  The shape
    label (IN/OUT/EDGE/WEIRD) is printed at the midpoint of each segment.

    The contour points loaded from the .npz cache are in the same piece-local
    coordinate space as the crop image - no translation is needed.

    Args:
        img: Piece crop image (BGR). Modified in place via cv2 calls on a copy.
        contour_pts: Contour array of shape (N, 1, 2) in piece-local coordinates.
        corner_indices: Mapping from CornerPos.value to contour index.
        piece: PieceRecord supplying segment_shapes.

    Returns:
        A new image with the overlay drawn.
    """
    out = img.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    n = len(contour_pts)

    # Draw each segment
    for edge_pos, (start_corner, end_corner) in EDGE_ENDS_TO_CORNER.items():
        edge_key = edge_pos.value
        color = _SEGMENT_COLORS[edge_key]
        start_idx = corner_indices.get(start_corner.value, 0)
        end_idx = corner_indices.get(end_corner.value, 0)

        # Extract segment points (handle wrap-around)
        if start_idx <= end_idx:
            seg_pts = contour_pts[start_idx : end_idx + 1]
        else:
            seg_pts = np.vstack((contour_pts[start_idx:], contour_pts[: end_idx + 1]))

        if len(seg_pts) > 0:
            cv2.polylines(out, [seg_pts], isClosed=False, color=color, thickness=2)

            # Shape label at segment midpoint
            mid = seg_pts[len(seg_pts) // 2][0]
            shape_label = piece.segment_shapes.get(edge_key, "?").upper()
            cv2.putText(
                out,
                shape_label,
                (int(mid[0]) + 4, int(mid[1]) - 4),
                font,
                0.4,
                color,
                1,
                cv2.LINE_AA,
            )

    # Draw corner circles and labels
    for corner_pos in CornerPos:
        idx = corner_indices.get(corner_pos.value)
        if idx is None or idx >= n:
            continue
        pt = tuple(int(v) for v in contour_pts[idx][0])
        cv2.circle(out, pt, _CORNER_RADIUS, _CORNER_COLOR, -1)
        cv2.circle(out, pt, _CORNER_RADIUS, (0, 0, 0), 1)
        abbrev = _CORNER_LABEL_ABBREV.get(corner_pos.value, "?")
        cv2.putText(
            out,
            abbrev,
            (pt[0] + _CORNER_RADIUS + 2, pt[1] - 2),
            font,
            0.35,
            _CORNER_COLOR,
            1,
            cv2.LINE_AA,
        )

    return out


def _burn_label(img: np.ndarray, label: str) -> np.ndarray:
    """Burn a text label onto the top-left corner of an image.

    Draws a semi-transparent dark rectangle behind the text for readability.
    The label is drawn before any rotation so it rotates with the piece.

    Args:
        img: Source image (BGR, uint8). Not modified in place.
        label: Text to draw.

    Returns:
        A copy of the image with the label burned in.
    """
    out = img.copy()
    h, w = out.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.3, min(w, h) / 200.0)
    thickness = max(1, int(font_scale * 1.5))
    margin = max(4, int(min(w, h) * 0.04))
    (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)
    rect_x2 = margin + text_w + margin
    rect_y2 = margin + text_h + baseline + margin
    overlay = out.copy()
    cv2.rectangle(overlay, (0, 0), (rect_x2, rect_y2), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, out, 0.45, 0, out)
    cv2.putText(
        out,
        label,
        (margin, margin + text_h),
        font,
        font_scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )
    return out


@lru_cache(maxsize=8)
def _load_sheet_image(img_path: str) -> np.ndarray | None:
    """Load a sheet image from disk, cached by path."""
    img = cv2.imread(img_path)
    if img is None:
        lg.warning(f"Could not read image: {img_path}")
    return img


def _draw_segment_highlight(
    img: np.ndarray,
    contour_pts: np.ndarray,
    corner_indices: dict[str, int],
    edge_pos_val: str,
) -> np.ndarray:
    """Draw a single segment on the crop image with its canonical colour.

    All other contour points are also drawn in a dim grey so the piece
    silhouette is visible.  The highlighted segment is drawn on top in
    its full colour at thickness 3.

    Args:
        img: Piece crop image (BGR). Not modified in place.
        contour_pts: Contour array of shape (N, 1, 2) in piece-local coords.
        corner_indices: Mapping from ``CornerPos.value`` to contour index.
        edge_pos_val: ``EdgePos.value`` string selecting the segment to highlight.

    Returns:
        A new image with the segment overlay drawn.
    """
    edge_pos = EdgePos(edge_pos_val)
    start_corner, end_corner = EDGE_ENDS_TO_CORNER[edge_pos]
    color = _SEGMENT_COLORS.get(edge_pos_val, (255, 255, 255))

    start_idx = corner_indices.get(start_corner.value, 0)
    end_idx = corner_indices.get(end_corner.value, 0)

    out = img.copy()

    # Dim full contour for context
    cv2.polylines(out, [contour_pts], isClosed=True, color=(80, 80, 80), thickness=1)

    # Highlighted segment
    if start_idx <= end_idx:
        seg_pts = contour_pts[start_idx : end_idx + 1]
    else:
        seg_pts = np.vstack((contour_pts[start_idx:], contour_pts[: end_idx + 1]))

    if len(seg_pts) > 0:
        cv2.polylines(out, [seg_pts], isClosed=False, color=color, thickness=3)

    return out


def _compose_preview(
    img_a: np.ndarray,
    img_b: np.ndarray,
    label_a: str = "",
    label_b: str = "",
    gap: int = 8,
) -> np.ndarray:
    """Place two images side-by-side on a dark canvas with text labels.

    Args:
        img_a: Left image (BGR).
        img_b: Right image (BGR).
        label_a: Label drawn along the bottom of the left image.
        label_b: Label drawn along the bottom of the right image.
        gap: Pixel gap between the two images.

    Returns:
        Composite image array (BGR).
    """
    ha, wa = img_a.shape[:2]
    hb, wb = img_b.shape[:2]
    h = max(ha, hb)
    w = wa + gap + wb
    canvas = np.full((h, w, 3), 40, dtype=np.uint8)

    y_a = (h - ha) // 2
    canvas[y_a : y_a + ha, :wa] = img_a

    y_b = (h - hb) // 2
    canvas[y_b : y_b + hb, wa + gap :] = img_b

    font = cv2.FONT_HERSHEY_SIMPLEX
    label_color = (200, 200, 200)
    if label_a:
        cv2.putText(
            canvas, label_a, (4, h - 4), font, 0.35, label_color, 1, cv2.LINE_AA
        )
    if label_b:
        cv2.putText(
            canvas,
            label_b,
            (wa + gap + 2, h - 4),
            font,
            0.35,
            label_color,
            1,
            cv2.LINE_AA,
        )
    return canvas
