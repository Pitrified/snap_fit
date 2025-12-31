"""Manager for handling multiple puzzle sheets."""

from collections.abc import Callable
from pathlib import Path

from loguru import logger as lg

from snap_fit.config.types import EdgePos
from snap_fit.data_models.piece_id import PieceId
from snap_fit.data_models.segment_id import SegmentId
from snap_fit.image.segment import Segment
from snap_fit.puzzle.piece import Piece
from snap_fit.puzzle.sheet import Sheet


class SheetManager:
    """Manages a collection of puzzle sheets."""

    def __init__(self) -> None:
        """Initialize the SheetManager."""
        self.sheets: dict[str, Sheet] = {}

    def add_sheet(self, sheet: Sheet, sheet_id: str) -> None:
        """Add a single sheet to the manager with a specific ID.

        Args:
            sheet: The Sheet object to add.
            sheet_id: A unique identifier for the sheet.
        """
        if sheet_id in self.sheets:
            lg.warning(f"Overwriting sheet with ID: {sheet_id}")

        # Ensure the sheet knows its ID
        sheet.sheet_id = sheet_id
        # Ensure all pieces in the sheet have the correct sheet_id in their PieceId
        for piece in sheet.pieces:
            if piece.piece_id.sheet_id != sheet_id:
                piece.piece_id = PieceId(
                    sheet_id=sheet_id, piece_id=piece.piece_id.piece_id
                )

        self.sheets[sheet_id] = sheet
        lg.info(f"Added sheet: {sheet_id}")

    def add_sheets(
        self,
        folder_path: Path,
        pattern: str = "*",
        loader_func: Callable[[Path], Sheet] | None = None,
    ) -> None:
        """Glob a folder for files matching the pattern and add them.

        Args:
            folder_path: Root directory to search.
            pattern: Glob pattern (e.g., "*.jpg", "*.json").
            loader_func: Function to convert a file Path into a Sheet object.
                TODO: make it mandatory in the future.

        Side Effects:
            - Generates an ID for each sheet (e.g., relative path from folder_path).
            - Populates self.sheets.
        """
        folder = Path(folder_path)
        if not folder.exists():
            lg.error(f"Folder not found: {folder}")
            return

        files = sorted(folder.glob(pattern))
        lg.info(f"Found {len(files)} files matching '{pattern}' in {folder}")

        for file_path in files:
            # Generate ID: relative path from the search folder
            # This ensures uniqueness within the context of this load
            sheet_id = str(file_path.relative_to(folder))

            if loader_func:
                sheet = loader_func(file_path)
                self.add_sheet(sheet, sheet_id)
            else:
                lg.warning(f"No loader_func provided, skipping {file_path}")
                # TODO: make loader_func mandatory in the future

    def get_sheet(self, sheet_id: str) -> Sheet | None:
        """Retrieve a sheet by its ID.

        Args:
            sheet_id: The ID of the sheet to retrieve.

        Returns:
            The Sheet object if found, else None.
        """
        return self.sheets.get(sheet_id)

    def get_sheets_ls(self) -> list[Sheet]:
        """Return a list of all managed sheets.

        Returns:
            A list of all Sheet objects in the manager.
        """
        return list(self.sheets.values())

    def get_pieces_ls(self) -> list[Piece]:
        """Return a flat list of all pieces across all sheets.

        Returns:
            A list of all Piece objects from all managed sheets.
        """
        all_pieces: list[Piece] = []
        for sheet in self.sheets.values():
            if hasattr(sheet, "pieces"):
                all_pieces.extend(sheet.pieces)
            else:
                lg.warning(f"Sheet {sheet} has no 'pieces' attribute")
        return all_pieces

    def get_segment_ids_all(self) -> list[SegmentId]:
        """Get all segment IDs from all sheets in this manager.

        Returns:
            A list of all SegmentId objects across all sheets/pieces/edges.
        """
        segment_ids: list[SegmentId] = []
        for sheet in self.sheets.values():
            for piece in sheet.pieces:
                segment_ids.extend(
                    SegmentId(
                        piece_id=piece.piece_id,
                        edge_pos=edge_pos,
                    )
                    for edge_pos in EdgePos
                )
        return segment_ids

    def get_segment_ids_other_pieces(self, seg_id: SegmentId) -> list[SegmentId]:
        """Get segment IDs from all pieces except the one referenced by seg_id.

        Args:
            seg_id: The segment ID whose piece should be excluded.

        Returns:
            A list of SegmentId objects from all other pieces.
        """
        all_ids = self.get_segment_ids_all()
        return [sid for sid in all_ids if sid.piece_id != seg_id.piece_id]

    def get_segment(self, seg_id: SegmentId) -> Segment | None:
        """Retrieve a segment by its SegmentId.

        Args:
            seg_id: The SegmentId identifying the segment.

        Returns:
            The Segment object if found, else None.
        """
        piece = self.get_piece_by_segment_id(seg_id)
        if piece is None:
            return None
        return piece.segments.get(seg_id.edge_pos)

    def get_piece_by_segment_id(self, seg_id: SegmentId) -> Piece | None:
        """Retrieve a piece by a SegmentId.

        Args:
            seg_id: The SegmentId containing the piece_id.

        Returns:
            The Piece object if found, else None.
        """
        return self.get_piece(seg_id.piece_id)

    def get_piece(self, piece_id: PieceId) -> Piece | None:
        """Retrieve a piece by its PieceId.

        Args:
            piece_id: The PieceId identifying the piece.

        Returns:
            The Piece object if found, else None.
        """
        sheet = self.sheets.get(piece_id.sheet_id)
        if sheet is None:
            lg.warning(f"Sheet not found: {piece_id.sheet_id}")
            return None
        for piece in sheet.pieces:
            if piece.piece_id == piece_id:
                return piece
        lg.warning(f"Piece not found: {piece_id}")
        return None

    def get_sheet_by_segment_id(self, seg_id: SegmentId) -> Sheet | None:
        """Retrieve a sheet by a SegmentId.

        Args:
            seg_id: The SegmentId containing sheet_id.

        Returns:
            The Sheet object if found, else None.
        """
        return self.sheets.get(seg_id.piece_id.sheet_id)
