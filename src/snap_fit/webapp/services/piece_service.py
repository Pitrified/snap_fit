"""Service layer for piece operations.

Integrates with SheetManager for persistence and data access.
"""

from pathlib import Path

from loguru import logger as lg

from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.data_models.sheet_record import SheetRecord
from snap_fit.puzzle.sheet_manager import SheetManager


class PieceService:
    """Service for piece and sheet data operations."""

    def __init__(self, cache_dir: Path) -> None:
        """Initialize service with cache directory.

        Args:
            cache_dir: Directory for metadata and contour cache files.
        """
        self.cache_dir = cache_dir
        self.metadata_path = cache_dir / "metadata.json"
        self.contour_cache_dir = cache_dir / "contours"

    def list_sheets(self) -> list[SheetRecord]:
        """Return all sheet records from cached metadata."""
        if not self.metadata_path.exists():
            return []
        data = SheetManager.load_metadata(self.metadata_path)
        return [SheetRecord.model_validate(s) for s in data.get("sheets", [])]

    def list_pieces(self) -> list[PieceRecord]:
        """Return all piece records from cached metadata."""
        if not self.metadata_path.exists():
            return []
        data = SheetManager.load_metadata(self.metadata_path)
        return [PieceRecord.model_validate(p) for p in data.get("pieces", [])]

    def get_piece(self, piece_id: str) -> PieceRecord | None:
        """Retrieve a single piece by ID.

        Args:
            piece_id: The piece ID (format: sheet_id-piece_idx).

        Returns:
            PieceRecord if found, None otherwise.
        """
        if not self.metadata_path.exists():
            return None
        data = SheetManager.load_metadata(self.metadata_path)
        for p in data.get("pieces", []):
            record = PieceRecord.model_validate(p)
            if str(record.piece_id) == piece_id:
                return record
        return None

    def get_sheet(self, sheet_id: str) -> SheetRecord | None:
        """Retrieve a single sheet by ID.

        Args:
            sheet_id: The sheet ID.

        Returns:
            SheetRecord if found, None otherwise.
        """
        if not self.metadata_path.exists():
            return None
        data = SheetManager.load_metadata(self.metadata_path)
        for s in data.get("sheets", []):
            record = SheetRecord.model_validate(s)
            if record.sheet_id == sheet_id:
                return record
        return None

    def ingest_sheets(
        self,
        sheet_dir: Path,
        threshold: int = 130,
        min_area: int = 80_000,
    ) -> dict:
        """Load sheets from a directory, compute pieces, and persist.

        Args:
            sheet_dir: Path to directory containing sheet images.
            threshold: Threshold for image preprocessing.
            min_area: Minimum contour area for piece detection.

        Returns:
            Summary dict with sheets_ingested, pieces_detected, cache_path.
        """
        manager = SheetManager()

        # Process all PNG images in directory
        img_files = sorted(sheet_dir.glob("*.png"))
        for img_file in img_files:
            lg.info(f"Processing sheet: {img_file.name}")
            manager.add_sheet(img_file, threshold=threshold, min_area=min_area)

        # Persist to cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        manager.save_metadata(self.metadata_path)
        manager.save_contour_cache(self.contour_cache_dir)

        records = manager.to_records()
        return {
            "sheets_ingested": len(records["sheets"]),
            "pieces_detected": len(records["pieces"]),
            "cache_path": str(self.cache_dir),
        }

    def get_pieces_for_sheet(self, sheet_id: str) -> list[PieceRecord]:
        """Get all pieces belonging to a specific sheet.

        Args:
            sheet_id: The sheet ID to filter by.

        Returns:
            List of PieceRecord objects for the sheet.
        """
        pieces = self.list_pieces()
        return [p for p in pieces if p.piece_id.sheet_id == sheet_id]
