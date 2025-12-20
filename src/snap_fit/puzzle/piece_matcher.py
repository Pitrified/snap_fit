"""Piece matching logic."""

from loguru import logger as lg

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
