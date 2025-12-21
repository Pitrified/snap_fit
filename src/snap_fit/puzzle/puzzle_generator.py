"""Jigsaw puzzle generator.

Port of the JavaScript jigsaw generator from libs/jigsaw/jigsaw.html.
Generates puzzle geometry as SVG with optional rasterization.
"""

from enum import Enum
import math

from loguru import logger as lg
from pydantic import BaseModel
from pydantic import Field

from snap_fit.puzzle.puzzle_config import ALPHABET_SIZE
from snap_fit.puzzle.puzzle_config import PuzzleConfig

# Threshold for random boolean generation
_RBOOL_THRESHOLD = 0.5


class EdgeType(str, Enum):
    """Type of puzzle edge."""

    FLAT = "flat"  # Border edge
    TAB_IN = "tab_in"  # Tab pointing inward
    TAB_OUT = "tab_out"  # Tab pointing outward


class BezierSegment(BaseModel):
    """A single cubic Bézier segment with 4 control points."""

    p0: tuple[float, float] = Field(description="Start point")
    p1: tuple[float, float] = Field(description="First control point")
    p2: tuple[float, float] = Field(description="Second control point")
    p3: tuple[float, float] = Field(description="End point")

    def to_svg_curve(self) -> str:
        """Generate SVG cubic Bézier curve command (C)."""
        return (
            f"C {self.p1[0]:.2f} {self.p1[1]:.2f} "
            f"{self.p2[0]:.2f} {self.p2[1]:.2f} "
            f"{self.p3[0]:.2f} {self.p3[1]:.2f}"
        )


class BezierEdge(BaseModel):
    """A puzzle edge composed of multiple Bézier segments."""

    segments: list[BezierSegment] = Field(default_factory=list)
    edge_type: EdgeType = Field(default=EdgeType.FLAT)
    start: tuple[float, float] = Field(default=(0.0, 0.0))

    def to_svg_path(self) -> str:
        """Generate SVG path data for this edge."""
        if self.edge_type == EdgeType.FLAT or not self.segments:
            # For flat edges, just draw a line to the end
            if self.segments:
                end = self.segments[-1].p3
                return f"L {end[0]:.2f} {end[1]:.2f}"
            return ""

        parts = [f"M {self.start[0]:.2f} {self.start[1]:.2f}"]
        parts.extend(segment.to_svg_curve() for segment in self.segments)
        return " ".join(parts)


class PuzzlePiece(BaseModel):
    """A single puzzle piece with its edges and label."""

    row: int = Field(description="Row index (0-based)")
    col: int = Field(description="Column index (0-based)")
    label: str = Field(description="Piece label (e.g., 'A1', 'BC12')")

    # Edges: None means border (flat edge)
    top: BezierEdge | None = Field(default=None)
    right: BezierEdge | None = Field(default=None)
    bottom: BezierEdge | None = Field(default=None)
    left: BezierEdge | None = Field(default=None)

    # Bounds in mm
    x: float = Field(description="X position in mm")
    y: float = Field(description="Y position in mm")
    width: float = Field(description="Width in mm")
    height: float = Field(description="Height in mm")


class SeededRandom:
    """Deterministic random number generator matching the JS implementation."""

    def __init__(self, seed: int) -> None:
        """Initialize with a seed."""
        self.seed = seed

    def random(self) -> float:
        """Generate a random number in [0, 1)."""
        x = math.sin(self.seed) * 10000
        self.seed += 1
        return x - math.floor(x)

    def uniform(self, min_val: float, max_val: float) -> float:
        """Generate a random number in [min_val, max_val)."""
        r = self.random()
        return min_val + r * (max_val - min_val)

    def rbool(self) -> bool:
        """Generate a random boolean."""
        return self.random() > _RBOOL_THRESHOLD


def generate_label(col: int, row: int, letter_digits: int, number_digits: int) -> str:
    """Generate a label in LLNN format.

    Args:
        col: Column index (0-based).
        row: Row index (0-based).
        letter_digits: Number of letter digits.
        number_digits: Number of number digits.

    Returns:
        Label string like "A1", "BC12", etc.
    """
    # Generate letter part (A-Z, AA-AZ, BA-BZ, ...)
    letters = ""
    c = col
    for _ in range(letter_digits):
        letters = chr(ord("A") + (c % ALPHABET_SIZE)) + letters
        c //= ALPHABET_SIZE

    # Generate number part (1-based, zero-padded)
    number = str(row + 1).zfill(number_digits)

    return letters + number


class PuzzleGenerator:
    """Generates jigsaw puzzle geometry."""

    def __init__(self, config: PuzzleConfig) -> None:
        """Initialize the puzzle generator.

        Args:
            config: Puzzle configuration.
        """
        self.config = config
        self.rng = SeededRandom(config.seed)
        self._pieces: list[PuzzlePiece] | None = None
        self._horizontal_edges: list[list[BezierEdge]] | None = None
        self._vertical_edges: list[list[BezierEdge]] | None = None

    def _reset_rng(self) -> None:
        """Reset the RNG to ensure deterministic output."""
        self.rng = SeededRandom(self.config.seed)

    def generate(self) -> list[PuzzlePiece]:
        """Generate all puzzle pieces.

        Returns:
            List of PuzzlePiece objects.
        """
        if self._pieces is not None:
            return self._pieces

        self._reset_rng()
        lg.info(
            f"Generating {self.config.tiles_x}x{self.config.tiles_y} puzzle "
            f"({self.config.width}x{self.config.height} mm)"
        )

        # Generate all internal edges
        self._generate_edges()

        # Create pieces
        pieces = []
        for row in range(self.config.tiles_y):
            for col in range(self.config.tiles_x):
                piece = self._create_piece(row, col)
                pieces.append(piece)

        self._pieces = pieces
        lg.info(f"Generated {len(pieces)} pieces")
        return pieces

    def _generate_edges(self) -> None:
        """Generate all internal edges for the puzzle."""
        t = self.config.tab_size / 2.0
        j = self.config.jitter

        # Horizontal edges (between rows)
        # We have (tiles_y - 1) rows of horizontal edges
        # Each row has tiles_x edges
        self._horizontal_edges = []
        for yi in range(1, self.config.tiles_y):
            row_edges = []
            # Reset edge state for this row
            flip = self.rng.rbool()
            e = self.rng.uniform(-j, j)

            for xi in range(self.config.tiles_x):
                edge = self._generate_single_edge(
                    xi, yi, t, j, e, flip=flip, vertical=False
                )
                row_edges.append(edge)
                # Update for next edge
                flip_old = flip
                flip = self.rng.rbool()
                a = -e if flip == flip_old else e
                e = self.rng.uniform(-j, j)
                # Store a for continuity (not used in simplified version)
                _ = a

            self._horizontal_edges.append(row_edges)

        # Vertical edges (between columns)
        # We have (tiles_x - 1) columns of vertical edges
        # Each column has tiles_y edges
        self._vertical_edges = []
        for xi in range(1, self.config.tiles_x):
            col_edges = []
            # Reset edge state for this column
            flip = self.rng.rbool()
            e = self.rng.uniform(-j, j)

            for yi in range(self.config.tiles_y):
                edge = self._generate_single_edge(
                    xi, yi, t, j, e, flip=flip, vertical=True
                )
                col_edges.append(edge)
                # Update for next edge
                flip_old = flip
                flip = self.rng.rbool()
                a = -e if flip == flip_old else e
                e = self.rng.uniform(-j, j)
                _ = a

            self._vertical_edges.append(col_edges)

    def _generate_single_edge(
        self,
        xi: int,
        yi: int,
        t: float,
        j: float,
        e: float,
        *,
        flip: bool,
        vertical: bool,
    ) -> BezierEdge:
        """Generate a single edge with tab.

        This follows the JS implementation's control point generation.
        """
        # Generate random offsets
        a = self.rng.uniform(-j, j)
        b = self.rng.uniform(-j, j)
        c = self.rng.uniform(-j, j)
        d = self.rng.uniform(-j, j)

        # Calculate piece dimensions
        if vertical:
            sl = self.config.height / self.config.tiles_y  # length along edge
            sw = self.config.width / self.config.tiles_x  # width perpendicular
            ol = yi * sl  # offset along length
            ow = xi * sw  # offset along width
        else:
            sl = self.config.width / self.config.tiles_x
            sw = self.config.height / self.config.tiles_y
            ol = xi * sl
            ow = yi * sw

        # Helper to calculate position along edge
        def along(v: float) -> float:
            return ol + sl * v

        # Helper to calculate position perpendicular to edge
        def perp(v: float) -> float:
            sign = -1.0 if flip else 1.0
            return ow + sw * v * sign

        # Generate control points (following JS p0-p9)
        # The edge goes from (0,0) to (1,0) in normalized coords
        # with a tab shape in the middle

        if vertical:
            # Vertical edge: swap x/y
            p0 = (perp(0.0), along(0.0))
            p1 = (perp(a), along(0.2))
            p2 = (perp(-t + c), along(0.5 + b + d))
            p3 = (perp(t + c), along(0.5 - t + b))
            p4 = (perp(3.0 * t + c), along(0.5 - 2.0 * t + b - d))
            p5 = (perp(3.0 * t + c), along(0.5 + 2.0 * t + b - d))
            p6 = (perp(t + c), along(0.5 + t + b))
            p7 = (perp(-t + c), along(0.5 + b + d))
            p8 = (perp(e), along(0.8))
            p9 = (perp(0.0), along(1.0))
        else:
            # Horizontal edge
            p0 = (along(0.0), perp(0.0))
            p1 = (along(0.2), perp(a))
            p2 = (along(0.5 + b + d), perp(-t + c))
            p3 = (along(0.5 - t + b), perp(t + c))
            p4 = (along(0.5 - 2.0 * t + b - d), perp(3.0 * t + c))
            p5 = (along(0.5 + 2.0 * t + b - d), perp(3.0 * t + c))
            p6 = (along(0.5 + t + b), perp(t + c))
            p7 = (along(0.5 + b + d), perp(-t + c))
            p8 = (along(0.8), perp(e))
            p9 = (along(1.0), perp(0.0))

        # Create three cubic Bézier segments
        segments = [
            BezierSegment(p0=p0, p1=p1, p2=p2, p3=p3),
            BezierSegment(p0=p3, p1=p4, p2=p5, p3=p6),
            BezierSegment(p0=p6, p1=p7, p2=p8, p3=p9),
        ]

        edge_type = EdgeType.TAB_OUT if flip else EdgeType.TAB_IN
        return BezierEdge(segments=segments, edge_type=edge_type, start=p0)

    def _create_piece(self, row: int, col: int) -> PuzzlePiece:
        """Create a single puzzle piece."""
        # Calculate bounds
        x = col * self.config.piece_width
        y = row * self.config.piece_height

        # Generate label
        label = generate_label(
            col, row, self.config.letter_digits, self.config.number_digits
        )

        # Get edges (None for border edges)
        top = None
        if row > 0 and self._horizontal_edges is not None:
            top = self._horizontal_edges[row - 1][col]

        bottom = None
        if row < self.config.tiles_y - 1 and self._horizontal_edges is not None:
            bottom = self._horizontal_edges[row][col]

        left = None
        if col > 0 and self._vertical_edges is not None:
            left = self._vertical_edges[col - 1][row]

        right = None
        if col < self.config.tiles_x - 1 and self._vertical_edges is not None:
            right = self._vertical_edges[col][row]

        return PuzzlePiece(
            row=row,
            col=col,
            label=label,
            top=top,
            right=right,
            bottom=bottom,
            left=left,
            x=x,
            y=y,
            width=self.config.piece_width,
            height=self.config.piece_height,
        )

    def to_svg(self, *, include_labels: bool = True) -> str:
        """Generate SVG representation of the full puzzle.

        Args:
            include_labels: Whether to include piece labels.

        Returns:
            SVG string.
        """
        pieces = self.generate()

        width = self.config.width
        height = self.config.height
        radius = self.config.corner_radius

        svg_parts = [
            '<svg xmlns="http://www.w3.org/2000/svg" version="1.0" ',
            f'width="{width}mm" height="{height}mm" ',
            f'viewBox="0 0 {width} {height}">',
        ]

        # Draw horizontal edges
        if self._horizontal_edges:
            h_path = self._edges_to_path(self._horizontal_edges)
            svg_parts.append(
                f'<path fill="none" stroke="DarkBlue" stroke-width="0.1" d="{h_path}"/>'
            )

        # Draw vertical edges
        if self._vertical_edges:
            v_path = self._edges_to_path(self._vertical_edges)
            svg_parts.append(
                f'<path fill="none" stroke="DarkRed" stroke-width="0.1" d="{v_path}"/>'
            )

        # Draw border
        border_path = self._generate_border_path(width, height, radius)
        svg_parts.append(
            f'<path fill="none" stroke="Black" stroke-width="0.1" d="{border_path}"/>'
        )

        # Add labels
        if include_labels:
            font_size = self.config.auto_font_size
            for piece in pieces:
                cx = piece.x + piece.width / 2
                cy = piece.y + piece.height / 2
                svg_parts.append(
                    f'<text x="{cx:.2f}" y="{cy:.2f}" '
                    f'font-family="{self.config.font_family}" '
                    f'font-size="{font_size:.2f}" '
                    f'text-anchor="middle" dominant-baseline="middle" '
                    f'fill="gray">{piece.label}</text>'
                )

        svg_parts.append("</svg>")
        return "".join(svg_parts)

    def _edges_to_path(self, edges: list[list[BezierEdge]]) -> str:
        """Convert edge grid to SVG path string."""
        path_parts: list[str] = []

        for row_or_col in edges:
            for edge in row_or_col:
                if edge.segments:
                    # Start new subpath
                    start = edge.start
                    path_parts.append(f"M {start[0]:.2f} {start[1]:.2f}")
                    path_parts.extend(
                        segment.to_svg_curve() for segment in edge.segments
                    )

        return " ".join(path_parts)

    def _generate_border_path(self, width: float, height: float, radius: float) -> str:
        """Generate rounded rectangle border path."""
        r = radius
        return (
            f"M {r} 0 "
            f"L {width - r} 0 "
            f"A {r} {r} 0 0 1 {width} {r} "
            f"L {width} {height - r} "
            f"A {r} {r} 0 0 1 {width - r} {height} "
            f"L {r} {height} "
            f"A {r} {r} 0 0 1 0 {height - r} "
            f"L 0 {r} "
            f"A {r} {r} 0 0 1 {r} 0"
        )

    def _edge_to_path_forward(
        self, edge: BezierEdge | None, fallback_end: tuple[float, float]
    ) -> list[str]:
        """Convert edge segments to path parts (forward direction)."""
        if edge and edge.segments:
            return [segment.to_svg_curve() for segment in edge.segments]
        return [f"L {fallback_end[0]:.2f} {fallback_end[1]:.2f}"]

    def _edge_to_path_reversed(
        self, edge: BezierEdge | None, fallback_end: tuple[float, float]
    ) -> list[str]:
        """Convert edge segments to path parts (reversed direction)."""
        if edge and edge.segments:
            return [
                f"C {s.p2[0]:.2f} {s.p2[1]:.2f} "
                f"{s.p1[0]:.2f} {s.p1[1]:.2f} "
                f"{s.p0[0]:.2f} {s.p0[1]:.2f}"
                for s in reversed(edge.segments)
            ]
        return [f"L {fallback_end[0]:.2f} {fallback_end[1]:.2f}"]

    def piece_to_svg(
        self,
        row: int,
        col: int,
        *,
        include_label: bool = True,
        padding: float = 0.0,
    ) -> str:
        """Generate SVG for a single piece.

        Args:
            row: Row index.
            col: Column index.
            include_label: Whether to include the label.
            padding: Extra padding around the piece.

        Returns:
            SVG string for the piece.
        """
        pieces = self.generate()
        piece = next(p for p in pieces if p.row == row and p.col == col)

        # Calculate viewBox with padding
        # The piece might extend beyond its bounds due to tabs
        tab_extend = self.config.piece_width * self.config.tab_size * 1.5
        vb_x = piece.x - tab_extend - padding
        vb_y = piece.y - tab_extend - padding
        vb_w = piece.width + 2 * tab_extend + 2 * padding
        vb_h = piece.height + 2 * tab_extend + 2 * padding

        svg_parts = [
            '<svg xmlns="http://www.w3.org/2000/svg" version="1.0" ',
            f'width="{vb_w}mm" height="{vb_h}mm" ',
            f'viewBox="{vb_x:.2f} {vb_y:.2f} {vb_w:.2f} {vb_h:.2f}">',
        ]

        # Build piece outline path
        path_parts = [f"M {piece.x:.2f} {piece.y:.2f}"]

        # Top edge (forward)
        path_parts.extend(
            self._edge_to_path_forward(piece.top, (piece.x + piece.width, piece.y))
        )

        # Right edge (forward)
        path_parts.extend(
            self._edge_to_path_forward(
                piece.right, (piece.x + piece.width, piece.y + piece.height)
            )
        )

        # Bottom edge (reversed)
        path_parts.extend(
            self._edge_to_path_reversed(piece.bottom, (piece.x, piece.y + piece.height))
        )

        # Left edge (reversed)
        path_parts.extend(self._edge_to_path_reversed(piece.left, (piece.x, piece.y)))

        path_parts.append("Z")
        path_d = " ".join(path_parts)

        svg_parts.append(
            f'<path fill="white" stroke="black" stroke-width="0.2" d="{path_d}"/>'
        )

        # Add label
        if include_label:
            font_size = self.config.auto_font_size
            cx = piece.x + piece.width / 2
            cy = piece.y + piece.height / 2
            svg_parts.append(
                f'<text x="{cx:.2f}" y="{cy:.2f}" '
                f'font-family="{self.config.font_family}" '
                f'font-size="{font_size:.2f}" '
                f'text-anchor="middle" dominant-baseline="middle" '
                f'fill="black">{piece.label}</text>'
            )

        svg_parts.append("</svg>")
        return "".join(svg_parts)
