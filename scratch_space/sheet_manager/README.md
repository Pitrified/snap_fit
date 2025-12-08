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
from typing import List, Dict, Callable, Optional
from pathlib import Path
from snap_fit.puzzle.sheet import Sheet
from snap_fit.puzzle.piece import Piece

class SheetManager:
    def __init__(self):
        self.sheets: Dict[str, Sheet] = {}

    def add_sheet(self, sheet: Sheet, sheet_id: str) -> None:
        """Add a single sheet to the manager with a specific ID."""
        self.sheets[sheet_id] = sheet

    def add_sheets(self, folder_path: Path, pattern: str = "*", loader_func: Optional[Callable[[Path], Sheet]] = None) -> None:
        """
        Glob a folder for files matching the pattern.

        Args:
            folder_path: Root directory to search.
            pattern: Glob pattern (e.g., "*.jpg", "*.json").
            loader_func: Function to convert a file Path into a Sheet object.
                         If None, use standard Sheet loading logic.

        Side Effects:
            - Generates an ID for each sheet (e.g., relative path from folder_path).
            - Populates self.sheets.
        """
        pass

    def get_sheet(self, sheet_id: str) -> Sheet | None:
        """Retrieve a sheet by its ID."""
        return self.sheets.get(sheet_id)

    def get_sheets_ls(self) -> List[Sheet]:
        """Return a list of all managed sheets."""
        return list(self.sheets.values())

    def get_pieces_ls(self) -> List[Piece]:
        """Return a flat list of all pieces across all sheets."""
        # return [p for s in self.sheets.values() for p in s.pieces]
        pass
```

## Usage Example

```python
from snap_fit.puzzle.sheet_aruco import SheetAruco
from snap_fit.scratch_space.sheet_manager import SheetManager

manager = SheetManager()

# 1. Define a loader adapter
def aruco_loader(path: Path) -> Sheet:
    # SheetAruco processes the image and extracts the Sheet
    return SheetAruco(path).sheet

# 2. Batch load images
manager.add_sheets(
    folder_path=Path("./data/scans"),
    pattern="*.jpg",
    loader_func=aruco_loader
)

# 3. Access aggregated data
all_pieces = manager.get_pieces_ls()
print(f"Loaded {len(manager.sheets)} sheets with {len(all_pieces)} total pieces.")
```

## Tasks

- [ ] **Core Class**: Define `SheetManager` in `src/snap_fit/puzzle/sheet_manager.py` (or similar).
- [ ] **Single Add**: Implement `add_sheet` with ID enforcement.
- [ ] **Batch Add**: Implement `add_sheets` with `glob` and `loader_func` support.
- [ ] **ID Strategy**: Implement logic to generate unique IDs from file paths (e.g., `folder_path` relative path).
- [ ] **Accessors**: Implement `get_sheets_ls` and `get_pieces_ls`.
- [ ] **Testing**: Create unit tests for adding/retrieving sheets.
- [ ] **Integration**: Create a notebook `scratch_space/sheet_manager/01_prototype.ipynb` demonstrating `SheetAruco` integration.

## Decisions

- **Name**: `SheetManager` is the chosen name.
- **Scope**: Only `Sheet` objects are stored. `SheetAruco` is a transient loader.
- **IDs**: We will need a strategy to ensure unique IDs for sheets (e.g., filename or internal UUID) -> relative path from load location.
