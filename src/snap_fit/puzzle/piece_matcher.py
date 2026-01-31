"""Piece matching logic."""

import json
from pathlib import Path

from loguru import logger as lg

from snap_fit.config.types import EdgePos
from snap_fit.data_models.match_result import MatchResult
from snap_fit.data_models.piece_id import PieceId
from snap_fit.data_models.segment_id import SegmentId
from snap_fit.image.segment_matcher import SegmentMatcher
from snap_fit.puzzle.sheet_manager import SheetManager


class PieceMatcher:
    """Matches puzzle pieces and stores results."""

    def __init__(self, manager: SheetManager) -> None:
        """Initialize the piece matcher with a sheet manager."""
        self.manager = manager
        self._results: list[MatchResult] = []
        self._lookup: dict[frozenset[SegmentId], MatchResult] = {}

    @property
    def results(self) -> list[MatchResult]:
        """Get the list of match results."""
        return self._results

    def match_pair(self, id1: SegmentId, id2: SegmentId) -> MatchResult:
        """Match two segments and store the result."""
        pair = frozenset({id1, id2})
        if pair in self._lookup:
            return self._lookup[pair]

        seg1 = self.manager.get_segment(id1)
        seg2 = self.manager.get_segment(id2)

        if seg1 is None or seg2 is None:
            lg.warning(f"Could not find segments for {id1} or {id2}")
            # Return a high similarity (poor match) if segments are missing
            res = MatchResult(seg_id1=id1, seg_id2=id2, similarity=1e6)
        else:
            matcher = SegmentMatcher(seg1, seg2)
            similarity = matcher.compute_similarity()
            res = MatchResult(seg_id1=id1, seg_id2=id2, similarity=float(similarity))

        self._results.append(res)
        self._lookup[pair] = res
        return res

    def match_all(self) -> None:
        """Match all segments against all segments from other pieces."""
        all_ids = self.manager.get_segment_ids_all()
        lg.info(f"Matching {len(all_ids)} segments...")

        for id1 in all_ids:
            # Use the manager's helper to get candidates from other pieces
            other_ids = self.manager.get_segment_ids_other_pieces(id1)
            for id2 in other_ids:
                self.match_pair(id1, id2)

        # Sort results by similarity (lower is better)
        self._results.sort(key=lambda x: x.similarity)
        lg.info(f"Completed {len(self._results)} matches.")

    def get_top_matches(self, n: int = 10) -> list[MatchResult]:
        """Get the top N matches."""
        return self._results[:n]

    def get_matches_for_piece(self, piece_id: PieceId) -> list[MatchResult]:
        """Get all matches involving a specific piece."""
        return [
            res
            for res in self._results
            if piece_id in {res.seg_id1.piece_id, res.seg_id2.piece_id}
        ]

    def get_cached_score(self, seg_a: SegmentId, seg_b: SegmentId) -> float | None:
        """Get cached match score for a segment pair if available.

        Args:
            seg_a: First segment ID.
            seg_b: Second segment ID.

        Returns:
            The similarity score if cached, None otherwise.
        """
        pair = frozenset({seg_a, seg_b})
        if pair in self._lookup:
            return self._lookup[pair].similarity
        return None

    # -------------------------------------------------------------------------
    # Persistence Methods
    # -------------------------------------------------------------------------

    def save_matches_json(self, path: Path) -> None:
        """Save all match results to a JSON file.

        Uses by_alias=True to properly serialize similarity_manual_ field.

        Args:
            path: Output path for the JSON file.
        """
        data = [r.model_dump(mode="json", by_alias=True) for r in self._results]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        lg.info(f"Saved {len(self._results)} matches to {path}")

    def load_matches_json(self, path: Path) -> None:
        """Load match results from a JSON file and rebuild lookup.

        Args:
            path: Path to the JSON file containing match results.

        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        data = json.loads(path.read_text())
        self._results = [MatchResult.model_validate(d) for d in data]
        self._lookup = {r.pair: r for r in self._results}
        lg.info(f"Loaded {len(self._results)} matches from {path}")

    def get_matched_pair_keys(self) -> set[frozenset[SegmentId]]:
        """Get all matched pairs for incremental matching support.

        Returns:
            Set of frozensets, each containing two SegmentIds that have been matched.
        """
        return set(self._lookup.keys())

    def match_incremental(self, new_piece_ids: list[PieceId]) -> int:
        """Match only new pieces against existing ones.

        Useful when adding new sheets—avoids re-matching all existing pairs.

        Args:
            new_piece_ids: Piece IDs from newly added sheets.

        Returns:
            Number of new matches computed.
        """
        existing_keys = self.get_matched_pair_keys()
        new_count = 0

        for piece_id in new_piece_ids:
            for edge_pos in EdgePos:
                new_seg_id = SegmentId(piece_id=piece_id, edge_pos=edge_pos)
                other_ids = self.manager.get_segment_ids_other_pieces(new_seg_id)

                for other_id in other_ids:
                    pair = frozenset({new_seg_id, other_id})
                    if pair not in existing_keys:
                        self.match_pair(new_seg_id, other_id)
                        new_count += 1

        # Re-sort results by similarity (lower is better)
        self._results.sort(key=lambda x: x.similarity)
        lg.info(f"Incremental matching added {new_count} new matches")
        return new_count

    def clear(self) -> None:
        """Clear all match results and lookup cache."""
        self._results.clear()
        self._lookup.clear()
        lg.info("Cleared all match results")
