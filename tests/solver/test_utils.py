"""Tests for solver utilities."""

from snap_fit.data_models.piece_id import PieceId
from snap_fit.solver.utils import get_factor_pairs
from snap_fit.solver.utils import infer_grid_size


class TestGetFactorPairs:
    """Tests for get_factor_pairs function."""

    def test_returns_empty_for_small_numbers(self) -> None:
        """Test that small numbers return no valid factor pairs."""
        # 9 is 3*3, but min_size=4 means no valid pairs
        assert get_factor_pairs(9, min_size=4) == []

    def test_returns_pairs_for_16(self) -> None:
        """Test factor pairs for 16 (4x4)."""
        pairs = get_factor_pairs(16, min_size=4)
        assert (4, 4) in pairs

    def test_returns_pairs_for_48(self) -> None:
        """Test factor pairs for 48 (6x8)."""
        pairs = get_factor_pairs(48, min_size=4)
        assert (6, 8) in pairs
        assert (4, 12) in pairs

    def test_returns_pairs_for_100(self) -> None:
        """Test factor pairs for 100 (10x10, 5x20, 4x25)."""
        pairs = get_factor_pairs(100, min_size=4)
        assert (10, 10) in pairs
        assert (5, 20) in pairs
        assert (4, 25) in pairs

    def test_custom_min_size(self) -> None:
        """Test that min_size is respected."""
        pairs = get_factor_pairs(12, min_size=3)
        assert (3, 4) in pairs
        # 2x6 should not be included since min_size=3
        assert (2, 6) not in pairs

    def test_large_number_10000(self) -> None:
        """Test factor pairs for 10000 pieces."""
        pairs = get_factor_pairs(10000, min_size=4)
        # Should find 100x100
        assert (100, 100) in pairs
        # Should find other valid pairs
        assert len(pairs) > 0


class TestInferGridSize:
    """Tests for infer_grid_size function."""

    def _make_piece_ids(self, count: int, _prefix: str = "p") -> list[PieceId]:
        """Private func to create piece ID lists."""
        return [PieceId(sheet_id="sheet", piece_id=i) for i in range(count)]

    def test_exact_match_3x3(self) -> None:
        """Test exact match for 3x3 grid (below min_size, returns None)."""
        # 3x3: 4 corners, 4 edges, 1 inner = 9 pieces
        # But min_size=4, so no valid 3x3 pairs
        corners = self._make_piece_ids(4)
        edges = self._make_piece_ids(4)
        inners = self._make_piece_ids(1)

        result = infer_grid_size(corners, edges, inners)
        # 9 has no factor pairs >= 4, so returns None
        assert result is None

    def test_exact_match_4x4(self) -> None:
        """Test exact match for 4x4 grid."""
        # 4x4: 4 corners, 8 edges, 4 inners = 16 pieces
        corners = self._make_piece_ids(4)
        edges = self._make_piece_ids(8)
        inners = self._make_piece_ids(4)

        result = infer_grid_size(corners, edges, inners)
        assert result == (4, 4)

    def test_exact_match_6x8(self) -> None:
        """Test exact match for 6x8 grid."""
        # 6x8: 4 corners, 20 edges, 24 inners = 48 pieces
        corners = self._make_piece_ids(4)
        edges = self._make_piece_ids(20)
        inners = self._make_piece_ids(24)

        result = infer_grid_size(corners, edges, inners)
        assert result == (6, 8)

    def test_tolerance_allows_misclassification(self) -> None:
        """Test that tolerance allows some misclassified pieces."""
        # 4x4 should be: 4 corners, 8 edges, 4 inners
        # But we have 3 corners (one detected as edge)
        corners = self._make_piece_ids(3)
        edges = self._make_piece_ids(9)  # 8 + 1 misclassified corner
        inners = self._make_piece_ids(4)

        result = infer_grid_size(corners, edges, inners, tolerance=2)
        assert result == (4, 4)

    def test_no_match_returns_fallback(self) -> None:
        """Test fallback when type distribution doesn't match."""
        # 16 pieces but wrong distribution - should still find 4x4
        corners = self._make_piece_ids(1)
        edges = self._make_piece_ids(5)
        inners = self._make_piece_ids(10)

        result = infer_grid_size(corners, edges, inners)
        # Should fallback to (4, 4) based on total count
        assert result == (4, 4)

    def test_returns_none_for_prime(self) -> None:
        """Test returns None for prime number of pieces (no valid grid)."""
        # 17 is prime, no valid grid size
        corners = self._make_piece_ids(4)
        edges = self._make_piece_ids(8)
        inners = self._make_piece_ids(5)  # Total: 17

        result = infer_grid_size(corners, edges, inners)
        assert result is None

    def test_large_grid_100x100(self) -> None:
        """Test inference for large 100x100 grid."""
        # 100x100: 4 corners, 392 edges, 9604 inners = 10000 pieces
        corners = self._make_piece_ids(4)
        edges = self._make_piece_ids(392)
        inners = self._make_piece_ids(9604)

        result = infer_grid_size(corners, edges, inners)
        assert result == (100, 100)
