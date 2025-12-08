"""Manager for handling multiple puzzle sheets."""

from collections.abc import Callable
from pathlib import Path

from loguru import logger as lg

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

        files = list(folder.glob(pattern))
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
