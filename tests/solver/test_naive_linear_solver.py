"""Tests for NaiveLinearSolver."""

from unittest.mock import MagicMock
from unittest.mock import patch

from snap_fit.data_models.piece_id import PieceId
from snap_fit.grid.grid_model import GridModel
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.placement_state import PlacementState
from snap_fit.solver.naive_linear_solver import NaiveLinearSolver


class TestNaiveLinearSolverInit:
    """Tests for NaiveLinearSolver initialization."""

    def test_init_stores_grid_and_matcher(self) -> None:
        """Test that __init__ stores grid and matcher references."""
        grid = GridModel(rows=3, cols=3)
        matcher = MagicMock()
        manager = MagicMock()
        corners = [PieceId(sheet_id="s1", piece_id=0)]
        edges = [PieceId(sheet_id="s1", piece_id=1)]
        inners = [PieceId(sheet_id="s1", piece_id=2)]

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=corners,
            edges=edges,
            inners=inners,
        )

        assert solver.grid is grid
        assert solver.matcher is matcher
        assert solver.manager is manager

    def test_init_copies_piece_lists(self) -> None:
        """Test that __init__ creates copies of piece lists."""
        grid = GridModel(rows=3, cols=3)
        matcher = MagicMock()
        manager = MagicMock()
        corners = [PieceId(sheet_id="s1", piece_id=0)]
        edges = [PieceId(sheet_id="s1", piece_id=1)]
        inners = [PieceId(sheet_id="s1", piece_id=2)]

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=corners,
            edges=edges,
            inners=inners,
        )

        # Internal lists should be copies, not same objects
        assert solver._corners is not corners
        assert solver._edges is not edges
        assert solver._inners is not inners

        # But content should match
        assert solver._corners == corners
        assert solver._edges == edges
        assert solver._inners == inners

    def test_init_creates_placement_state(self) -> None:
        """Test that __init__ creates a PlacementState."""
        grid = GridModel(rows=3, cols=3)
        matcher = MagicMock()
        manager = MagicMock()

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=[],
            edges=[],
            inners=[],
        )

        assert isinstance(solver.state, PlacementState)
        assert solver.state.grid is grid


class TestNaiveLinearSolverHelpers:
    """Tests for helper methods."""

    def test_get_all_available(self) -> None:
        """Test _get_all_available returns all pieces."""
        grid = GridModel(rows=3, cols=3)
        matcher = MagicMock()
        manager = MagicMock()
        corners = [PieceId(sheet_id="s1", piece_id=0)]
        edges = [PieceId(sheet_id="s1", piece_id=1), PieceId(sheet_id="s1", piece_id=2)]
        inners = [PieceId(sheet_id="s1", piece_id=3)]

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=corners,
            edges=edges,
            inners=inners,
        )

        all_available = solver._get_all_available()
        assert len(all_available) == 4
        assert set(all_available) == set(corners + edges + inners)

    def test_remove_from_pool_corner(self) -> None:
        """Test removing a corner piece from pool."""
        grid = GridModel(rows=3, cols=3)
        matcher = MagicMock()
        manager = MagicMock()
        corner = PieceId(sheet_id="s1", piece_id=0)
        corners = [corner]

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=corners,
            edges=[],
            inners=[],
        )

        solver._remove_from_pool(corner)
        assert corner not in solver._corners
        assert len(solver._corners) == 0

    def test_remove_from_pool_edge(self) -> None:
        """Test removing an edge piece from pool."""
        grid = GridModel(rows=3, cols=3)
        matcher = MagicMock()
        manager = MagicMock()
        edge = PieceId(sheet_id="s1", piece_id=1)
        edges = [edge]

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=[],
            edges=edges,
            inners=[],
        )

        solver._remove_from_pool(edge)
        assert edge not in solver._edges
        assert len(solver._edges) == 0

    def test_remove_from_pool_inner(self) -> None:
        """Test removing an inner piece from pool."""
        grid = GridModel(rows=3, cols=3)
        matcher = MagicMock()
        manager = MagicMock()
        inner = PieceId(sheet_id="s1", piece_id=2)
        inners = [inner]

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=[],
            edges=[],
            inners=inners,
        )

        solver._remove_from_pool(inner)
        assert inner not in solver._inners
        assert len(solver._inners) == 0

    def test_get_candidates_with_fallback_primary_available(self) -> None:
        """Test fallback returns primary when available."""
        grid = GridModel(rows=3, cols=3)
        matcher = MagicMock()
        manager = MagicMock()
        corners = [PieceId(sheet_id="s1", piece_id=0)]

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=corners,
            edges=[],
            inners=[],
        )

        candidates = solver._get_candidates_with_fallback(solver._corners, "corner")
        assert candidates == solver._corners

    def test_get_candidates_with_fallback_uses_all_when_empty(self) -> None:
        """Test fallback returns all available when primary is empty."""
        grid = GridModel(rows=3, cols=3)
        matcher = MagicMock()
        manager = MagicMock()
        edges = [PieceId(sheet_id="s1", piece_id=1)]

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=[],
            edges=edges,
            inners=[],
        )

        # Ask for corners (empty), should fall back to edges
        candidates = solver._get_candidates_with_fallback([], "corner")
        assert candidates == edges


class TestNaiveLinearSolverComputeOrientation:
    """Tests for piece orientation computation."""

    def test_compute_orientation_with_no_piece_found(self) -> None:
        """Test orientation falls back to slot orientation when piece not found."""
        grid = GridModel(rows=3, cols=3)
        matcher = MagicMock()
        manager = MagicMock()
        manager.get_piece.return_value = None

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=[],
            edges=[],
            inners=[],
        )

        piece_id = PieceId(sheet_id="s1", piece_id=0)
        result = solver._compute_piece_orientation(piece_id, Orientation.DEG_90)

        assert result == Orientation.DEG_90

    def test_compute_orientation_subtracts_base(self) -> None:
        """Test orientation is computed as slot - base."""
        grid = GridModel(rows=3, cols=3)
        matcher = MagicMock()
        manager = MagicMock()

        # Mock piece with base orientation DEG_90
        mock_piece = MagicMock()
        mock_piece.oriented_piece_type.orientation = Orientation.DEG_90
        manager.get_piece.return_value = mock_piece

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=[],
            edges=[],
            inners=[],
        )

        piece_id = PieceId(sheet_id="s1", piece_id=0)
        # slot_orientation=DEG_180, base=DEG_90 => result should be DEG_90
        result = solver._compute_piece_orientation(piece_id, Orientation.DEG_180)

        assert result == Orientation.DEG_90


class TestNaiveLinearSolverSolve:
    """Tests for the solve method."""

    def test_solve_returns_placement_state(self) -> None:
        """Test that solve returns a PlacementState."""
        grid = GridModel(rows=2, cols=2)
        matcher = MagicMock()
        manager = MagicMock()

        # Create 4 corners for a 2x2 grid (all corners)
        corners = [PieceId(sheet_id="s1", piece_id=i) for i in range(4)]

        # Mock piece lookup to return pieces with base orientation DEG_0
        mock_piece = MagicMock()
        mock_piece.oriented_piece_type.orientation = Orientation.DEG_0
        manager.get_piece.return_value = mock_piece

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=corners,
            edges=[],
            inners=[],
        )

        # Patch score_edge to return 0 for all calls
        with patch("snap_fit.solver.naive_linear_solver.score_edge", return_value=0.0):
            result = solver.solve()

        assert isinstance(result, PlacementState)

    def test_solve_places_all_pieces_2x2(self) -> None:
        """Test that solve places all pieces in a 2x2 grid."""
        grid = GridModel(rows=2, cols=2)
        matcher = MagicMock()
        manager = MagicMock()

        corners = [PieceId(sheet_id="s1", piece_id=i) for i in range(4)]

        mock_piece = MagicMock()
        mock_piece.oriented_piece_type.orientation = Orientation.DEG_0
        manager.get_piece.return_value = mock_piece

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=corners,
            edges=[],
            inners=[],
        )

        with patch("snap_fit.solver.naive_linear_solver.score_edge", return_value=0.0):
            result = solver.solve()

        assert result.placed_count == 4

    def test_solve_empties_piece_pools(self) -> None:
        """Test that solve uses up all pieces from pools."""
        grid = GridModel(rows=2, cols=2)
        matcher = MagicMock()
        manager = MagicMock()

        corners = [PieceId(sheet_id="s1", piece_id=i) for i in range(4)]

        mock_piece = MagicMock()
        mock_piece.oriented_piece_type.orientation = Orientation.DEG_0
        manager.get_piece.return_value = mock_piece

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=corners,
            edges=[],
            inners=[],
        )

        with patch("snap_fit.solver.naive_linear_solver.score_edge", return_value=0.0):
            solver.solve()

        # All corners should be used
        assert len(solver._corners) == 0


class TestNaiveLinearSolverScoring:
    """Tests for solution scoring."""

    def test_score_solution_calls_score_grid_with_details(self) -> None:
        """Test that score_solution uses score_grid_with_details."""
        grid = GridModel(rows=2, cols=2)
        matcher = MagicMock()
        manager = MagicMock()

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=[],
            edges=[],
            inners=[],
        )

        with patch(
            "snap_fit.solver.naive_linear_solver.score_grid_with_details",
            return_value=(100.0, {}),
        ) as mock_score:
            score = solver.score_solution()

        assert score == 100.0
        mock_score.assert_called_once()

    def test_score_solution_uses_provided_state(self) -> None:
        """Test that score_solution can score a provided state."""
        grid = GridModel(rows=2, cols=2)
        matcher = MagicMock()
        manager = MagicMock()

        solver = NaiveLinearSolver(
            grid=grid,
            matcher=matcher,
            manager=manager,
            corners=[],
            edges=[],
            inners=[],
        )

        custom_state = PlacementState(grid)

        with patch(
            "snap_fit.solver.naive_linear_solver.score_grid_with_details",
            return_value=(50.0, {}),
        ) as mock_score:
            score = solver.score_solution(custom_state)

        assert score == 50.0
        # Should be called with custom_state
        mock_score.assert_called_once_with(custom_state, solver.matcher)
