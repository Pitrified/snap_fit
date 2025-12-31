"""Tests for GridModel."""

import pytest

from snap_fit.grid.grid_model import GridModel
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation import PieceType
from snap_fit.grid.types import GridPos


class TestGridModelInit:
    """Tests for GridModel initialization."""

    def test_create_2x2(self) -> None:
        """Test creating minimal 2x2 grid."""
        grid = GridModel(rows=2, cols=2)
        assert grid.rows == 2
        assert grid.cols == 2
        assert grid.total_cells == 4

    def test_create_3x4(self) -> None:
        """Test creating 3x4 grid."""
        grid = GridModel(rows=3, cols=4)
        assert grid.rows == 3
        assert grid.cols == 4
        assert grid.total_cells == 12

    def test_invalid_size(self) -> None:
        """Test that grids smaller than 2x2 raise ValueError."""
        with pytest.raises(ValueError, match="at least 2x2"):
            GridModel(rows=1, cols=2)
        with pytest.raises(ValueError, match="at least 2x2"):
            GridModel(rows=2, cols=1)
        with pytest.raises(ValueError, match="at least 2x2"):
            GridModel(rows=0, cols=0)


class TestGridModelSlotTypes:
    """Tests for slot type computation."""

    def test_2x2_all_corners(self) -> None:
        """Test that 2x2 grid has all corners."""
        grid = GridModel(rows=2, cols=2)
        assert len(grid.corners) == 4
        assert len(grid.edges) == 0
        assert len(grid.inners) == 0

    def test_3x3_slot_counts(self) -> None:
        """Test slot type counts for 3x3 grid."""
        grid = GridModel(rows=3, cols=3)
        assert len(grid.corners) == 4
        assert len(grid.edges) == 4  # One per side (excluding corners)
        assert len(grid.inners) == 1  # Center only

    def test_4x5_slot_counts(self) -> None:
        """Test slot type counts for 4x5 grid."""
        grid = GridModel(rows=4, cols=5)
        assert len(grid.corners) == 4
        # Top: 3, Right: 2, Bottom: 3, Left: 2 = 10 edges
        assert len(grid.edges) == 10
        # Inner: (4-2) * (5-2) = 2 * 3 = 6
        assert len(grid.inners) == 6

    def test_corner_orientations(self) -> None:
        """Test that corners have correct orientations."""
        grid = GridModel(rows=3, cols=3)

        # Top-left: canonical (flat TOP + LEFT)
        tl = grid.get_slot_type(GridPos(ro=0, co=0))
        assert tl.piece_type == PieceType.CORNER
        assert tl.orientation == Orientation.DEG_0

        # Top-right: 90° (flat TOP + RIGHT)
        tr = grid.get_slot_type(GridPos(ro=0, co=2))
        assert tr.piece_type == PieceType.CORNER
        assert tr.orientation == Orientation.DEG_90

        # Bottom-right: 180° (flat BOTTOM + RIGHT)
        br = grid.get_slot_type(GridPos(ro=2, co=2))
        assert br.piece_type == PieceType.CORNER
        assert br.orientation == Orientation.DEG_180

        # Bottom-left: 270° (flat BOTTOM + LEFT)
        bl = grid.get_slot_type(GridPos(ro=2, co=0))
        assert bl.piece_type == PieceType.CORNER
        assert bl.orientation == Orientation.DEG_270

    def test_edge_orientations(self) -> None:
        """Test that edges have correct orientations."""
        grid = GridModel(rows=3, cols=3)

        # Top edge: 0° (flat on TOP)
        top = grid.get_slot_type(GridPos(ro=0, co=1))
        assert top.piece_type == PieceType.EDGE
        assert top.orientation == Orientation.DEG_0

        # Right edge: 90° (flat on RIGHT)
        right = grid.get_slot_type(GridPos(ro=1, co=2))
        assert right.piece_type == PieceType.EDGE
        assert right.orientation == Orientation.DEG_90

        # Bottom edge: 180° (flat on BOTTOM)
        bottom = grid.get_slot_type(GridPos(ro=2, co=1))
        assert bottom.piece_type == PieceType.EDGE
        assert bottom.orientation == Orientation.DEG_180

        # Left edge: 270° (flat on LEFT)
        left = grid.get_slot_type(GridPos(ro=1, co=0))
        assert left.piece_type == PieceType.EDGE
        assert left.orientation == Orientation.DEG_270

    def test_inner_orientation(self) -> None:
        """Test that inner pieces have DEG_0 orientation."""
        grid = GridModel(rows=3, cols=3)
        inner = grid.get_slot_type(GridPos(ro=1, co=1))
        assert inner.piece_type == PieceType.INNER
        assert inner.orientation == Orientation.DEG_0

    def test_get_slot_type_out_of_bounds(self) -> None:
        """Test that out-of-bounds position raises KeyError."""
        grid = GridModel(rows=3, cols=3)
        with pytest.raises(KeyError):
            grid.get_slot_type(GridPos(ro=3, co=0))
        with pytest.raises(KeyError):
            grid.get_slot_type(GridPos(ro=0, co=3))


class TestGridModelNeighbors:
    """Tests for neighbor computation."""

    def test_corner_neighbors(self) -> None:
        """Test that corners have 2 neighbors."""
        grid = GridModel(rows=3, cols=3)
        neighbors = grid.neighbors(GridPos(ro=0, co=0))
        assert len(neighbors) == 2
        assert GridPos(ro=0, co=1) in neighbors  # right
        assert GridPos(ro=1, co=0) in neighbors  # down

    def test_edge_neighbors(self) -> None:
        """Test that edge pieces have 3 neighbors."""
        grid = GridModel(rows=3, cols=3)
        neighbors = grid.neighbors(GridPos(ro=0, co=1))
        assert len(neighbors) == 3

    def test_inner_neighbors(self) -> None:
        """Test that inner pieces have 4 neighbors."""
        grid = GridModel(rows=3, cols=3)
        neighbors = grid.neighbors(GridPos(ro=1, co=1))
        assert len(neighbors) == 4
        assert GridPos(ro=0, co=1) in neighbors  # up
        assert GridPos(ro=1, co=2) in neighbors  # right
        assert GridPos(ro=2, co=1) in neighbors  # down
        assert GridPos(ro=1, co=0) in neighbors  # left


class TestGridModelNeighborPairs:
    """Tests for neighbor pair iteration."""

    def test_2x2_pairs(self) -> None:
        """Test neighbor pairs for 2x2 grid."""
        grid = GridModel(rows=2, cols=2)
        pairs = list(grid.neighbor_pairs())
        # 2x2 has 4 edges: 2 horizontal + 2 vertical
        assert len(pairs) == 4

    def test_3x3_pairs(self) -> None:
        """Test neighbor pairs for 3x3 grid."""
        grid = GridModel(rows=3, cols=3)
        pairs = list(grid.neighbor_pairs())
        # 3x3: horizontal = 3 rows * 2 = 6, vertical = 2 * 3 cols = 6
        assert len(pairs) == 12
        assert grid.total_edges == 12

    def test_pair_positions_are_adjacent(self) -> None:
        """Test that all pairs are actually adjacent."""
        grid = GridModel(rows=4, cols=4)
        for pos1, pos2 in grid.neighbor_pairs():
            # Adjacent means differ by 1 in exactly one dimension
            dr = abs(pos1.ro - pos2.ro)
            dc = abs(pos1.co - pos2.co)
            assert (dr == 1 and dc == 0) or (dr == 0 and dc == 1)


class TestGridModelAllPositions:
    """Tests for all_positions iterator."""

    def test_all_positions_count(self) -> None:
        """Test that all_positions yields correct number of positions."""
        grid = GridModel(rows=3, cols=4)
        positions = list(grid.all_positions())
        assert len(positions) == 12

    def test_all_positions_unique(self) -> None:
        """Test that all_positions yields unique positions."""
        grid = GridModel(rows=3, cols=4)
        positions = list(grid.all_positions())
        assert len(set(positions)) == len(positions)
