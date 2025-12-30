"""Tests for PlacementState."""

import pytest

from snap_fit.data_models.piece_id import PieceId
from snap_fit.grid.grid_model import GridModel
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.placement_state import PlacementState
from snap_fit.grid.types import GridPos


@pytest.fixture
def grid_3x3() -> GridModel:
    """Create a 3x3 grid for testing."""
    return GridModel(rows=3, cols=3)


@pytest.fixture
def piece_a() -> PieceId:
    """Create a test piece ID."""
    return PieceId(sheet_id="sheet1", piece_id=0)


@pytest.fixture
def piece_b() -> PieceId:
    """Create another test piece ID."""
    return PieceId(sheet_id="sheet1", piece_id=1)


class TestPlacementStateInit:
    """Tests for PlacementState initialization."""

    def test_create_empty(self, grid_3x3: GridModel) -> None:
        """Test creating empty placement state."""
        state = PlacementState(grid_3x3)
        assert state.grid is grid_3x3
        assert state.placed_count == 0
        assert state.empty_count == 9
        assert not state.is_complete()

    def test_empty_positions(self, grid_3x3: GridModel) -> None:
        """Test that all positions are initially empty."""
        state = PlacementState(grid_3x3)
        empty = state.empty_positions()
        assert len(empty) == 9


class TestPlacementStatePlace:
    """Tests for placing pieces."""

    def test_place_piece(self, grid_3x3: GridModel, piece_a: PieceId) -> None:
        """Test placing a piece."""
        state = PlacementState(grid_3x3)
        pos = GridPos(ro=0, co=0)

        state.place(piece_a, pos, Orientation.DEG_0)

        assert state.placed_count == 1
        assert state.get_placement(pos) == (piece_a, Orientation.DEG_0)
        assert state.get_position(piece_a) == pos

    def test_place_out_of_bounds(self, grid_3x3: GridModel, piece_a: PieceId) -> None:
        """Test that placing out of bounds raises KeyError."""
        state = PlacementState(grid_3x3)
        with pytest.raises(KeyError):
            state.place(piece_a, GridPos(ro=10, co=0), Orientation.DEG_0)

    def test_place_overwrites_existing(
        self, grid_3x3: GridModel, piece_a: PieceId, piece_b: PieceId
    ) -> None:
        """Test that placing on occupied position removes existing piece."""
        state = PlacementState(grid_3x3)
        pos = GridPos(ro=0, co=0)

        state.place(piece_a, pos, Orientation.DEG_0)
        state.place(piece_b, pos, Orientation.DEG_90)

        # piece_b should be there now
        assert state.get_placement(pos) == (piece_b, Orientation.DEG_90)
        # piece_a should be gone
        assert state.get_position(piece_a) is None
        assert state.placed_count == 1

    def test_place_moves_piece(self, grid_3x3: GridModel, piece_a: PieceId) -> None:
        """Test that placing a piece already on grid moves it."""
        state = PlacementState(grid_3x3)
        pos1 = GridPos(ro=0, co=0)
        pos2 = GridPos(ro=1, co=1)

        state.place(piece_a, pos1, Orientation.DEG_0)
        state.place(piece_a, pos2, Orientation.DEG_90)

        # Piece should be at new position
        assert state.get_position(piece_a) == pos2
        assert state.get_placement(pos2) == (piece_a, Orientation.DEG_90)
        # Old position should be empty
        assert state.get_placement(pos1) is None
        assert state.placed_count == 1


class TestPlacementStateRemove:
    """Tests for removing pieces."""

    def test_remove_piece(self, grid_3x3: GridModel, piece_a: PieceId) -> None:
        """Test removing a piece."""
        state = PlacementState(grid_3x3)
        pos = GridPos(ro=0, co=0)

        state.place(piece_a, pos, Orientation.DEG_90)
        result = state.remove(pos)

        assert result == (piece_a, Orientation.DEG_90)
        assert state.get_placement(pos) is None
        assert state.get_position(piece_a) is None
        assert state.placed_count == 0

    def test_remove_empty_position(self, grid_3x3: GridModel) -> None:
        """Test that removing from empty position returns None."""
        state = PlacementState(grid_3x3)
        result = state.remove(GridPos(ro=0, co=0))
        assert result is None


class TestPlacementStateQueries:
    """Tests for query methods."""

    def test_is_complete(self, grid_3x3: GridModel) -> None:
        """Test is_complete when all cells are filled."""
        state = PlacementState(grid_3x3)

        # Fill all 9 cells
        for i in range(9):
            piece = PieceId(sheet_id="test", piece_id=i)
            pos = GridPos(ro=i // 3, co=i % 3)
            state.place(piece, pos, Orientation.DEG_0)

        assert state.is_complete()
        assert state.placed_count == 9
        assert state.empty_count == 0

    def test_placed_pieces(
        self, grid_3x3: GridModel, piece_a: PieceId, piece_b: PieceId
    ) -> None:
        """Test getting list of placed pieces."""
        state = PlacementState(grid_3x3)

        state.place(piece_a, GridPos(ro=0, co=0), Orientation.DEG_0)
        state.place(piece_b, GridPos(ro=1, co=1), Orientation.DEG_90)

        placed = state.placed_pieces()
        assert len(placed) == 2
        assert piece_a in placed
        assert piece_b in placed


class TestPlacementStateClone:
    """Tests for clone method."""

    def test_clone_is_independent(
        self, grid_3x3: GridModel, piece_a: PieceId, piece_b: PieceId
    ) -> None:
        """Test that clone creates independent copy."""
        state = PlacementState(grid_3x3)
        pos1 = GridPos(ro=0, co=0)
        pos2 = GridPos(ro=1, co=1)

        state.place(piece_a, pos1, Orientation.DEG_0)

        # Clone and modify
        clone = state.clone()
        clone.place(piece_b, pos2, Orientation.DEG_90)

        # Original should be unchanged
        assert state.placed_count == 1
        assert state.get_placement(pos2) is None

        # Clone should have both
        assert clone.placed_count == 2
        assert clone.get_placement(pos2) == (piece_b, Orientation.DEG_90)

    def test_clone_shares_grid(self, grid_3x3: GridModel) -> None:
        """Test that clone shares the same grid reference."""
        state = PlacementState(grid_3x3)
        clone = state.clone()
        assert clone.grid is state.grid
