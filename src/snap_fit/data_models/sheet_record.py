"""Sheet record model for database persistence."""

from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import Field

if TYPE_CHECKING:
    from snap_fit.puzzle.sheet import Sheet


class SheetRecord(BaseModel):
    """DB-friendly representation of a Sheet.

    Stores metadata only—images remain on disk as file references.

    Attributes:
        sheet_id: Unique identifier for the sheet.
        img_path: Path to the image file (relative to data root).
        piece_count: Number of pieces detected in this sheet.
        threshold: Threshold value used for image preprocessing.
        min_area: Minimum contour area for piece detection.
        created_at: Timestamp when the record was created.
    """

    sheet_id: str
    img_path: Path
    piece_count: int
    threshold: int = 130
    min_area: int = 80_000
    created_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_sheet(cls, sheet: "Sheet", data_root: Path | None = None) -> "SheetRecord":
        """Create a SheetRecord from a Sheet object.

        Args:
            sheet: The Sheet object to convert.
            data_root: Base path for making img_path relative.
                If None, uses absolute path.

        Returns:
            A SheetRecord with metadata from the Sheet.
        """
        img_path = sheet.img_fp
        if data_root is not None:
            with suppress(ValueError):
                img_path = sheet.img_fp.relative_to(data_root)

        return cls(
            sheet_id=sheet.sheet_id,
            img_path=img_path,
            piece_count=len(sheet.pieces),
            threshold=sheet.threshold,
            min_area=sheet.min_area,
        )
