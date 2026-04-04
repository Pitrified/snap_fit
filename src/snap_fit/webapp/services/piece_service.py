"""Service layer for piece operations.

Integrates with SheetManager for persistence and data access.
"""

from pathlib import Path

from loguru import logger as lg

from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig
from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.data_models.sheet_record import SheetRecord
from snap_fit.puzzle.sheet_aruco import SheetAruco
from snap_fit.puzzle.sheet_manager import SheetManager


class PieceService:
    """Service for piece and sheet data operations."""

    def __init__(self, cache_dir: Path) -> None:
        """Initialize service with cache directory.

        Args:
            cache_dir: Root cache directory.  Each dataset lives under
                ``cache_dir / sheets_tag /`` with its own metadata.json,
                matches.json and contours/ sub-directory.
        """
        self.cache_dir = cache_dir

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _tag_dir(self, sheets_tag: str) -> Path:
        """Return the cache sub-directory for a specific dataset tag."""
        return self.cache_dir / sheets_tag

    def _all_tag_dirs(self) -> list[Path]:
        """Return all existing dataset sub-directories inside cache_dir."""
        if not self.cache_dir.exists():
            return []
        return [p for p in self.cache_dir.iterdir() if p.is_dir()]

    def list_sheets(self) -> list[SheetRecord]:
        """Return all sheet records aggregated across every cached dataset."""
        records: list[SheetRecord] = []
        for tag_dir in self._all_tag_dirs():
            meta = tag_dir / "metadata.json"
            if not meta.exists():
                continue
            data = SheetManager.load_metadata(meta)
            records.extend(
                SheetRecord.model_validate(s) for s in data.get("sheets", [])
            )
        return records

    def list_pieces(self) -> list[PieceRecord]:
        """Return all piece records aggregated across every cached dataset."""
        records: list[PieceRecord] = []
        for tag_dir in self._all_tag_dirs():
            meta = tag_dir / "metadata.json"
            if not meta.exists():
                continue
            data = SheetManager.load_metadata(meta)
            records.extend(
                PieceRecord.model_validate(p) for p in data.get("pieces", [])
            )
        return records

    def get_piece(self, piece_id: str) -> PieceRecord | None:
        """Retrieve a single piece by ID, searching all cached datasets.

        Args:
            piece_id: The piece ID (format: sheet_id-piece_idx).

        Returns:
            PieceRecord if found, None otherwise.
        """
        for tag_dir in self._all_tag_dirs():
            meta = tag_dir / "metadata.json"
            if not meta.exists():
                continue
            data = SheetManager.load_metadata(meta)
            for p in data.get("pieces", []):
                record = PieceRecord.model_validate(p)
                if str(record.piece_id) == piece_id:
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
            meta = tag_dir / "metadata.json"
            if not meta.exists():
                continue
            data = SheetManager.load_metadata(meta)
            for s in data.get("sheets", []):
                record = SheetRecord.model_validate(s)
                if record.sheet_id == sheet_id:
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
        manager.save_contour_cache(tag_dir / "contours")

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
        return [p for p in self.list_pieces() if p.piece_id.sheet_id == sheet_id]
