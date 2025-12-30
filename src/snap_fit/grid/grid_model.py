"""Grid model representing the puzzle structure."""

from __future__ import annotations

from typing import TYPE_CHECKING

from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation import OrientedPieceType
from snap_fit.grid.orientation import PieceType
from snap_fit.grid.types import GridPos

if TYPE_CHECKING:
    from collections.abc import Iterator

# Minimum grid size (must be at least 2x2 for corners to make sense)
_MIN_GRID_SIZE = 2


class GridModel:
    """Represents the puzzle grid structure.

    Stores grid dimensions and computes slot types (corner, edge, inner)
    with their required orientations based on position.

    Canonical orientation conventions:
    - CORNER at (0,0): flats on TOP + LEFT → Orientation.DEG_0
    - CORNER at (0,cols-1): flats on TOP + RIGHT → Orientation.DEG_90
    - CORNER at (rows-1,cols-1): flats on BOTTOM + RIGHT → Orientation.DEG_180
    - CORNER at (rows-1,0): flats on BOTTOM + LEFT → Orientation.DEG_270
    - EDGE on top row: flat on TOP → Orientation.DEG_0
    - EDGE on right col: flat on RIGHT → Orientation.DEG_90
    - EDGE on bottom row: flat on BOTTOM → Orientation.DEG_180
    - EDGE on left col: flat on LEFT → Orientation.DEG_270
    """

    def __init__(self, rows: int, cols: int) -> None:
        """Initialize the grid model.

        Args:
            rows: Number of rows in the grid.
            cols: Number of columns in the grid.

        Raises:
            ValueError: If rows or cols is less than 2.
        """
        if rows < _MIN_GRID_SIZE or cols < _MIN_GRID_SIZE:
            msg = f"Grid must be at least 2x2, got {rows}x{cols}"
            raise ValueError(msg)

        self.rows = rows
        self.cols = cols

        # Pre-compute slot types and position lists
        self._slot_types: dict[GridPos, OrientedPieceType] = {}
        self.corners: list[GridPos] = []
        self.edges: list[GridPos] = []
        self.inners: list[GridPos] = []

        self._build_slot_types()

    def _build_slot_types(self) -> None:
        """Build the mapping of positions to their required OrientedPieceType."""
        for ro in range(self.rows):
            for co in range(self.cols):
                pos = GridPos(ro=ro, co=co)
                oriented_type = self._compute_slot_type(ro, co)
                self._slot_types[pos] = oriented_type

                # Add to appropriate list
                match oriented_type.piece_type:
                    case PieceType.CORNER:
                        self.corners.append(pos)
                    case PieceType.EDGE:
                        self.edges.append(pos)
                    case PieceType.INNER:
                        self.inners.append(pos)

    def _compute_slot_type(self, ro: int, co: int) -> OrientedPieceType:
        """Compute the OrientedPieceType for a given position."""
        is_top = ro == 0
        is_bottom = ro == self.rows - 1
        is_left = co == 0
        is_right = co == self.cols - 1

        # Determine piece type and orientation based on position
        piece_type: PieceType
        orientation: Orientation

        if (is_top or is_bottom) and (is_left or is_right):
            # Corner
            piece_type = PieceType.CORNER
            if is_top and is_left:
                orientation = Orientation.DEG_0
            elif is_top and is_right:
                orientation = Orientation.DEG_90
            elif is_bottom and is_right:
                orientation = Orientation.DEG_180
            else:  # is_bottom and is_left
                orientation = Orientation.DEG_270
        elif is_top or is_bottom or is_left or is_right:
            # Edge
            piece_type = PieceType.EDGE
            if is_top:
                orientation = Orientation.DEG_0
            elif is_right:
                orientation = Orientation.DEG_90
            elif is_bottom:
                orientation = Orientation.DEG_180
            else:  # is_left
                orientation = Orientation.DEG_270
        else:
            # Inner
            piece_type = PieceType.INNER
            orientation = Orientation.DEG_0

        return OrientedPieceType(piece_type=piece_type, orientation=orientation)

    def get_slot_type(self, pos: GridPos) -> OrientedPieceType:
        """Get the required piece type and orientation for a slot.

        Args:
            pos: The grid position.

        Returns:
            OrientedPieceType: The required type and orientation.

        Raises:
            KeyError: If position is out of bounds.
        """
        if pos not in self._slot_types:
            msg = f"Position {pos} is out of bounds for {self.rows}x{self.cols} grid"
            raise KeyError(msg)
        return self._slot_types[pos]

    def neighbors(self, pos: GridPos) -> list[GridPos]:
        """Get adjacent positions (up to 4).

        Args:
            pos: The grid position.

        Returns:
            List of adjacent GridPos (up, right, down, left order).
        """
        result: list[GridPos] = []

        # Up
        if pos.ro > 0:
            result.append(GridPos(ro=pos.ro - 1, co=pos.co))
        # Right
        if pos.co < self.cols - 1:
            result.append(GridPos(ro=pos.ro, co=pos.co + 1))
        # Down
        if pos.ro < self.rows - 1:
            result.append(GridPos(ro=pos.ro + 1, co=pos.co))
        # Left
        if pos.co > 0:
            result.append(GridPos(ro=pos.ro, co=pos.co - 1))

        return result

    def neighbor_pairs(self) -> Iterator[tuple[GridPos, GridPos]]:
        """Iterate over all adjacent position pairs for scoring.

        Each pair is yielded once, with the "earlier" position first
        (by row, then column).

        Yields:
            Tuples of (pos1, pos2) for adjacent positions.
        """
        for ro in range(self.rows):
            for co in range(self.cols):
                pos = GridPos(ro=ro, co=co)
                # Right neighbor
                if co < self.cols - 1:
                    yield (pos, GridPos(ro=ro, co=co + 1))
                # Down neighbor
                if ro < self.rows - 1:
                    yield (pos, GridPos(ro=ro + 1, co=co))

    def all_positions(self) -> Iterator[GridPos]:
        """Iterate over all positions in the grid.

        Yields:
            All GridPos in row-major order.
        """
        for ro in range(self.rows):
            for co in range(self.cols):
                yield GridPos(ro=ro, co=co)

    @property
    def total_cells(self) -> int:
        """Total number of cells in the grid."""
        return self.rows * self.cols

    @property
    def total_edges(self) -> int:
        """Total number of internal edges (adjacencies) for scoring."""
        horizontal = self.rows * (self.cols - 1)
        vertical = (self.rows - 1) * self.cols
        return horizontal + vertical

    def __repr__(self) -> str:
        """Detailed repr for debugging."""
        return (
            f"GridModel(rows={self.rows}, cols={self.cols}, "
            f"corners={len(self.corners)}, edges={len(self.edges)}, "
            f"inners={len(self.inners)})"
        )
