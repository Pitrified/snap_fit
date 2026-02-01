"""Service layer for puzzle operations.

Integrates with PieceMatcher for match data access.
"""

from pathlib import Path
from typing import Any

from loguru import logger as lg

from snap_fit.data_models.match_result import MatchResult
from snap_fit.puzzle.piece_matcher import PieceMatcher


class PuzzleService:
    """Service for puzzle solving and match operations."""

    def __init__(self, cache_dir: Path) -> None:
        """Initialize service with cache directory.

        Args:
            cache_dir: Directory for match cache files.
        """
        self.cache_dir = cache_dir
        self.matches_path = cache_dir / "matches.json"

    def list_matches(
        self,
        limit: int = 100,
        min_similarity: float | None = None,
    ) -> list[MatchResult]:
        """Return match results from cached matches.

        Args:
            limit: Maximum number of matches to return.
            min_similarity: Filter to matches with similarity >= this value.

        Returns:
            List of MatchResult objects sorted by similarity (ascending).
        """
        if not self.matches_path.exists():
            return []

        matcher = PieceMatcher(manager=None)
        matcher.load_matches_json(self.matches_path)

        results = list(matcher._results)
        if min_similarity is not None:
            results = [r for r in results if r.similarity >= min_similarity]

        # Sort by similarity ascending (best matches have lowest similarity)
        results.sort(key=lambda r: r.similarity)
        return results[:limit]

    def get_matches_for_piece(
        self,
        piece_id: str,
        limit: int = 10,
    ) -> list[MatchResult]:
        """Return top matches involving a specific piece.

        Args:
            piece_id: The piece ID (format: sheet_id-piece_idx).
            limit: Maximum number of matches to return.

        Returns:
            List of MatchResult objects involving the piece.
        """
        if not self.matches_path.exists():
            return []

        matcher = PieceMatcher(manager=None)
        matcher.load_matches_json(self.matches_path)

        # Filter matches involving this piece
        results = [
            r
            for r in matcher._results
            if str(r.seg_id1.piece_id) == piece_id
            or str(r.seg_id2.piece_id) == piece_id
        ]
        results.sort(key=lambda r: r.similarity)
        return results[:limit]

    def get_matches_for_segment(
        self,
        piece_id: str,
        edge_pos: str,
        limit: int = 5,
    ) -> list[MatchResult]:
        """Return top matches for a specific segment.

        Args:
            piece_id: The piece ID.
            edge_pos: The edge position (TOP, RIGHT, BOTTOM, LEFT).
            limit: Maximum number of matches to return.

        Returns:
            List of MatchResult objects for the segment.
        """
        if not self.matches_path.exists():
            return []

        matcher = PieceMatcher(manager=None)
        matcher.load_matches_json(self.matches_path)

        # Filter matches for this specific segment
        results = []
        for r in matcher._results:
            seg1_match = (
                str(r.seg_id1.piece_id) == piece_id
                and r.seg_id1.edge_pos.value == edge_pos
            )
            seg2_match = (
                str(r.seg_id2.piece_id) == piece_id
                and r.seg_id2.edge_pos.value == edge_pos
            )
            if seg1_match or seg2_match:
                results.append(r)

        results.sort(key=lambda r: r.similarity)
        return results[:limit]

    def solve_puzzle(
        self,
        piece_ids: list[str] | None = None,
        config_path: str | None = None,
    ) -> dict[str, Any]:
        """Attempt to solve a puzzle.

        Args:
            piece_ids: Optional list of piece IDs to include in solve.
            config_path: Optional path to puzzle configuration.

        Returns:
            Dict with success, message, layout, piece_count.
        """
        # Placeholder - will integrate with snap_fit.solver
        count = len(piece_ids) if piece_ids else 0
        lg.info(f"Solve puzzle request: {count} pieces, config={config_path}")
        return {
            "success": False,
            "message": "Solver integration pending",
            "layout": None,
            "piece_count": count,
        }

    def match_count(self) -> int:
        """Return the total number of cached matches."""
        if not self.matches_path.exists():
            return 0
        matcher = PieceMatcher(manager=None)
        matcher.load_matches_json(self.matches_path)
        return len(matcher._results)
