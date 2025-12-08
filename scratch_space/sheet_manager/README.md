# Sheet Manager Feature Plan

## Goal

Implement a mechanism to cleanly hold and manage a collection of `Sheet` objects. This feature aims to facilitate batch processing, serialization, and organization of multiple puzzle sheets.

## Objectives

1.  **Containerization**: Create a `SheetManager` class to hold multiple `Sheet` instances.
2.  **Management**: Provide methods to add single sheets or batch load from directories.
3.  **Scope**: The manager tracks `Sheet` objects. `SheetAruco` is used only during the loading/creation phase to generate `Sheet` instances, but the manager itself is agnostic to the creation method.
4.  **Persistence**: (Optional for now) Plan for saving/loading collections.

## Proposed Structure

```python
from typing import List, Dict
from pathlib import Path
from snap_fit.puzzle.sheet import Sheet
from snap_fit.puzzle.piece import Piece

class SheetManager:
    def __init__(self):
        self.sheets: Dict[str, Sheet] = {}

    def add_sheet(self, sheet: Sheet) -> None:
        """Add a single sheet to the manager."""

    def add_sheets(self, folder_path: Path, pattern: str = "*") -> None:
        """Load all sheets from a folder.

        Glob a folder for files matching the pattern, load them as Sheets,
        and add them to the manager.
        """

    def get_sheet(self, sheet_id: str) -> Sheet | None:
        """Retrieve a sheet by its ID."""

    def get_sheets_ls(self) -> List[Sheet]:
        """Return a list of all managed sheets."""

    def get_pieces_ls(self) -> List[Piece]:
        """Return a flat list of all pieces across all sheets."""
```

## Tasks

- [ ] Define `SheetManager` class structure.
- [ ] Implement `add_sheet` and `get_sheet`.
- [ ] Implement `add_sheets` to glob and load multiple sheets.
- [ ] Implement `get_sheets_ls` and `get_pieces_ls`.
- [ ] Prototype usage in a notebook (loading via `SheetAruco` then storing in `SheetManager`).

## Decisions

- **Name**: `SheetManager` is the chosen name.
- **Scope**: Only `Sheet` objects are stored. `SheetAruco` is a transient loader.
- **IDs**: We will need a strategy to ensure unique IDs for sheets (e.g., filename or internal UUID) -> relative path from load location.
