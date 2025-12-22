"""Configuration models for puzzle generation."""

import math

from pydantic import BaseModel
from pydantic import Field
from pydantic import computed_field

# Constants for label generation
ALPHABET_SIZE = 26
SINGLE_DIGIT_MAX = 9


class PieceStyle(BaseModel):
    """Style configuration for puzzle piece rendering."""

    fill: str = Field(default="white", description="Fill color for the piece")
    stroke: str = Field(default="black", description="Stroke color for piece outline")
    stroke_width: float = Field(default=0.2, description="Stroke width in mm")
    label_color: str = Field(default="black", description="Color for the piece label")


class PuzzleConfig(BaseModel):
    """Configuration for puzzle generation."""

    # Puzzle dimensions in mm
    width: float = Field(default=300.0, description="Puzzle width in mm")
    height: float = Field(default=200.0, description="Puzzle height in mm")

    # Grid size
    tiles_x: int = Field(default=15, ge=2, description="Number of columns")
    tiles_y: int = Field(default=10, ge=2, description="Number of rows")

    # Tab parameters
    tab_size: float = Field(
        default=0.2, ge=0.1, le=0.3, description="Tab size as fraction of piece"
    )
    jitter: float = Field(
        default=0.04, ge=0.0, le=0.25, description="Random jitter amount"
    )

    # Border
    corner_radius: float = Field(default=2.0, ge=0.0, description="Corner radius in mm")

    # Randomization
    seed: int = Field(default=42, description="Random seed for generation")

    # Label config
    font_size: float | None = Field(
        default=None, description="Font size in mm, auto-scale if None"
    )
    font_family: str = Field(default="monospace", description="Font family for labels")

    # Style config
    piece_style: PieceStyle = Field(
        default_factory=PieceStyle, description="Style for piece rendering"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def piece_width(self) -> float:
        """Width of a single piece in mm."""
        return self.width / self.tiles_x

    @computed_field  # type: ignore[prop-decorator]
    @property
    def piece_height(self) -> float:
        """Height of a single piece in mm."""
        return self.height / self.tiles_y

    @computed_field  # type: ignore[prop-decorator]
    @property
    def letter_digits(self) -> int:
        """Number of letter digits needed for column labels."""
        # A-Z = 26, AA-AZ = 26, BA-BZ = 26, etc.
        # For n columns, we need ceil(log26(n)) digits
        if self.tiles_x <= ALPHABET_SIZE:
            return 1
        return math.ceil(math.log(self.tiles_x) / math.log(ALPHABET_SIZE))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def number_digits(self) -> int:
        """Number of digits needed for row labels."""
        if self.tiles_y <= SINGLE_DIGIT_MAX:
            return 1
        return len(str(self.tiles_y))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def auto_font_size(self) -> float:
        """Calculate automatic font size based on piece dimensions."""
        if self.font_size is not None:
            return self.font_size
        # Font size should be about 1/3 of the smaller piece dimension
        min_dim = min(self.piece_width, self.piece_height)
        # Account for label length
        label_len = self.letter_digits + self.number_digits
        return min(min_dim * 0.3, min_dim * 0.8 / label_len)


class SheetLayout(BaseModel):
    """Configuration for sheet layout with ArUco markers."""

    # Sheet dimensions in mm
    sheet_width: float = Field(default=297.0, description="Sheet width in mm (A4)")
    sheet_height: float = Field(default=210.0, description="Sheet height in mm (A4)")

    # Margins for ArUco markers
    margin: float = Field(default=20.0, description="Margin for ArUco markers in mm")

    # Piece spacing
    piece_spacing: float = Field(default=5.0, description="Gap between pieces in mm")

    # DPI for rasterization
    dpi: int = Field(default=300, description="DPI for rasterization")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def usable_width(self) -> float:
        """Usable width after margins."""
        return self.sheet_width - 2 * self.margin

    @computed_field  # type: ignore[prop-decorator]
    @property
    def usable_height(self) -> float:
        """Usable height after margins."""
        return self.sheet_height - 2 * self.margin

    def pieces_per_sheet(
        self, piece_width: float, piece_height: float
    ) -> tuple[int, int]:
        """Calculate how many pieces fit per sheet.

        Args:
            piece_width: Width of a single piece in mm.
            piece_height: Height of a single piece in mm.

        Returns:
            Tuple of (pieces_per_row, pieces_per_col).
        """
        pieces_per_row = int(self.usable_width / (piece_width + self.piece_spacing))
        pieces_per_col = int(self.usable_height / (piece_height + self.piece_spacing))
        return max(1, pieces_per_row), max(1, pieces_per_col)
