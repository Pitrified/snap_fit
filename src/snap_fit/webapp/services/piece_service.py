"""Service layer for piece operations.

Integrates with SheetManager for persistence and data access.
"""

from functools import lru_cache
from pathlib import Path

import cv2
from loguru import logger as lg
import numpy as np

from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig
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
    ) -> bytes | None:
        """Load processed sheet image, crop piece region, encode as PNG.

        The processed (rectified + cropped) sheet image is loaded from the
        cache, not the original photo. Piece coordinates (``sheet_origin``,
        ``padded_size``) are in the processed-sheet coordinate space.

        Args:
            piece_id: Piece identifier.
            size: Optional max dimension for resizing (preserves aspect ratio).
            orientation: Rotation in degrees (0, 90, 180, 270).

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


@lru_cache(maxsize=8)
def _load_sheet_image(img_path: str) -> np.ndarray | None:
    """Load a sheet image from disk, cached by path."""
    img = cv2.imread(img_path)
    if img is None:
        lg.warning(f"Could not read image: {img_path}")
    return img
