"""Placement state for tracking piece assignments on the grid."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from snap_fit.data_models.piece_id import PieceId
    from snap_fit.grid.grid_model import GridModel
    from snap_fit.grid.orientation import Orientation
    from snap_fit.grid.types import GridPos


class PlacementState:
    """Mutable container for piece-to-position assignments.

    Maintains bidirectional mappings for efficient lookups:
    - position → (piece_id, orientation)
    - piece_id → position

    Attributes:
        grid: Reference to the GridModel.
    """

    def __init__(self, grid: GridModel) -> None:
        """Initialize placement state for a grid.

        Args:
            grid: The GridModel defining the structure.
        """
        self._grid = grid
        self._placements: dict[GridPos, tuple[PieceId, Orientation]] = {}
        self._positions: dict[PieceId, GridPos] = {}

    @property
    def grid(self) -> GridModel:
        """Get the underlying grid model."""
        return self._grid

    def place(self, piece_id: PieceId, pos: GridPos, orientation: Orientation) -> None:
        """Assign a piece to a grid slot with a specific orientation.

        If the position is already occupied, the existing piece is removed first.
        If the piece is already placed elsewhere, it is moved.

        Args:
            piece_id: The piece to place.
            pos: The grid position.
            orientation: The rotation to apply to the piece.

        Raises:
            KeyError: If position is out of bounds.
        """
        # Validate position by checking if grid knows about it
        try:
            self._grid.get_slot_type(pos)
        except KeyError:
            msg = f"Position {pos} is out of bounds"
            raise KeyError(msg) from None

        # Remove piece from its current position if placed elsewhere
        if piece_id in self._positions:
            old_pos = self._positions[piece_id]
            if old_pos != pos:
                del self._placements[old_pos]

        # Remove any existing piece at the target position
        if pos in self._placements:
            old_piece, _ = self._placements[pos]
            del self._positions[old_piece]

        # Place the piece
        self._placements[pos] = (piece_id, orientation)
        self._positions[piece_id] = pos

    def remove(self, pos: GridPos) -> tuple[PieceId, Orientation] | None:
        """Remove and return the piece at a position.

        Args:
            pos: The grid position.

        Returns:
            Tuple of (piece_id, orientation) if occupied, None otherwise.
        """
        if pos not in self._placements:
            return None

        piece_id, orientation = self._placements[pos]
        del self._placements[pos]
        del self._positions[piece_id]
        return (piece_id, orientation)

    def get_placement(self, pos: GridPos) -> tuple[PieceId, Orientation] | None:
        """Get the piece and orientation at a position.

        Args:
            pos: The grid position.

        Returns:
            Tuple of (piece_id, orientation) if occupied, None otherwise.
        """
        return self._placements.get(pos)

    def get_position(self, piece_id: PieceId) -> GridPos | None:
        """Get the position of a piece.

        Args:
            piece_id: The piece to find.

        Returns:
            GridPos if the piece is placed, None otherwise.
        """
        return self._positions.get(piece_id)

    def is_complete(self) -> bool:
        """Check if all grid cells are filled.

        Returns:
            True if every position has a piece assigned.
        """
        return len(self._placements) == self._grid.total_cells

    def clone(self) -> PlacementState:
        """Create a shallow copy of the placement state.

        Useful for branching during solving.

        Returns:
            A new PlacementState with copied mappings.
        """
        new_state = PlacementState(self._grid)
        new_state._placements = self._placements.copy()
        new_state._positions = self._positions.copy()
        return new_state

    @property
    def placed_count(self) -> int:
        """Number of pieces currently placed."""
        return len(self._placements)

    @property
    def empty_count(self) -> int:
        """Number of empty positions."""
        return self._grid.total_cells - len(self._placements)

    def empty_positions(self) -> list[GridPos]:
        """Get all unoccupied positions.

        Returns:
            List of GridPos that have no piece assigned.
        """
        return [
            pos for pos in self._grid.all_positions() if pos not in self._placements
        ]

    def placed_pieces(self) -> list[PieceId]:
        """Get all placed piece IDs.

        Returns:
            List of PieceId currently on the grid.
        """
        return list(self._positions.keys())

    def __repr__(self) -> str:
        """Detailed repr for debugging."""
        return (
            f"PlacementState(grid={self._grid.rows}x{self._grid.cols}, "
            f"placed={self.placed_count}/{self._grid.total_cells})"
        )
