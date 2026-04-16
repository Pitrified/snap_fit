"""Service layer for interactive solve sessions."""

from datetime import UTC
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from loguru import logger as lg

from snap_fit.data_models.piece_id import PieceId
from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.grid.grid_model import GridModel
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation import PieceType
from snap_fit.grid.placement_state import PlacementState
from snap_fit.grid.suggestion import get_scored_segment_pairs
from snap_fit.grid.suggestion import pick_next_slot
from snap_fit.grid.suggestion import score_candidates
from snap_fit.grid.types import GridPos
from snap_fit.persistence.sqlite_store import DatasetStore
from snap_fit.puzzle.piece_matcher import PieceMatcher
from snap_fit.solver.utils import get_factor_pairs
from snap_fit.webapp.schemas.interactive import SolveSessionResponse
from snap_fit.webapp.schemas.interactive import SuggestionBundle
from snap_fit.webapp.schemas.interactive import SuggestionCandidate

# Module-level matcher cache - keeps loaded match data alive across requests
# (the service is created per-request, so instance-level caching is useless).
_matcher_cache: dict[str, PieceMatcher] = {}


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _parse_pos(pos_str: str) -> GridPos:
    """Parse ``"ro,co"`` into a ``GridPos``."""
    ro_str, co_str = pos_str.split(",")
    return GridPos(ro=int(ro_str), co=int(co_str))


def _response_from_data(data: dict[str, object]) -> SolveSessionResponse:
    """Build a ``SolveSessionResponse`` from a raw session dict."""
    placement: dict[str, tuple[str, int]] = data.get("placement", {})  # type: ignore[assignment]
    rows: int = data["grid_rows"]  # type: ignore[assignment]
    cols: int = data["grid_cols"]  # type: ignore[assignment]
    ps_raw = data.get("pending_suggestion")
    pending = SuggestionBundle.model_validate(ps_raw) if ps_raw is not None else None
    return SolveSessionResponse(
        session_id=data["session_id"],  # type: ignore[arg-type]
        dataset_tag=data["dataset_tag"],  # type: ignore[arg-type]
        grid_rows=rows,
        grid_cols=cols,
        placement=placement,
        rejected=data.get("rejected", {}),  # type: ignore[arg-type]
        undo_stack=data.get("undo_stack", []),  # type: ignore[arg-type]
        placed_count=len(placement),
        total_cells=rows * cols,
        complete=bool(data.get("complete", False)),
        score=data.get("score"),  # type: ignore[arg-type]
        pending_suggestion=pending,
        created_at=data["created_at"],  # type: ignore[arg-type]
        updated_at=data["updated_at"],  # type: ignore[arg-type]
    )


def _partition_from_records(
    records: list[PieceRecord],
) -> tuple[list[PieceId], list[PieceId], list[PieceId]]:
    """Partition piece records into corners, edges, and inners."""
    corners: list[PieceId] = []
    edges: list[PieceId] = []
    inners: list[PieceId] = []
    for r in records:
        if r.oriented_piece_type is None:
            inners.append(r.piece_id)
        elif r.oriented_piece_type.piece_type == PieceType.CORNER:
            corners.append(r.piece_id)
        elif r.oriented_piece_type.piece_type == PieceType.EDGE:
            edges.append(r.piece_id)
        else:
            inners.append(r.piece_id)
    return corners, edges, inners


class InteractiveService:
    """Manages interactive solve sessions with SQLite persistence."""

    def __init__(self, cache_path: Path, data_path: Path) -> None:
        """Initialize with cache and data directories."""
        self._cache_path = cache_path
        self._data_path = data_path

    def _store(self, tag: str) -> DatasetStore:
        return DatasetStore(self._cache_path / tag / "dataset.db")

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def create_session(
        self,
        dataset_tag: str,
        grid_rows: int | None = None,
        grid_cols: int | None = None,
    ) -> SolveSessionResponse:
        """Create a new solve session.

        If ``grid_rows`` / ``grid_cols`` are ``None``, the grid size is
        inferred from the piece count using ``get_factor_pairs()``.
        """
        store = self._store(dataset_tag)
        pieces = store.load_pieces()

        if grid_rows is None or grid_cols is None:
            pairs = get_factor_pairs(len(pieces), min_size=2)
            if not pairs:
                msg = (
                    f"Cannot infer grid size from {len(pieces)} pieces. "
                    "Provide grid_rows and grid_cols explicitly."
                )
                raise ValueError(msg)
            grid_rows, grid_cols = pairs[0]

        session_id = str(uuid4())
        now = _now_iso()
        data: dict[str, object] = {
            "session_id": session_id,
            "dataset_tag": dataset_tag,
            "grid_rows": grid_rows,
            "grid_cols": grid_cols,
            "placement": {},
            "rejected": {},
            "undo_stack": [],
            "complete": False,
            "score": None,
            "created_at": now,
            "updated_at": now,
        }
        store.save_session(data)
        lg.info(
            f"Created session {session_id}"
            f" for dataset '{dataset_tag}' ({grid_rows}x{grid_cols})",
        )
        return _response_from_data(data)

    def get_session(
        self,
        dataset_tag: str,
        session_id: str,
    ) -> SolveSessionResponse | None:
        """Load a session by ID, or return ``None``."""
        data = self._store(dataset_tag).load_session(session_id)
        if data is None:
            return None
        return _response_from_data(data)

    def list_sessions(self, dataset_tag: str) -> list[SolveSessionResponse]:
        """Return all sessions for a dataset, newest first."""
        rows = self._store(dataset_tag).load_sessions()
        return [_response_from_data(r) for r in rows]

    def delete_session(self, dataset_tag: str, session_id: str) -> bool:
        """Delete a session. Returns ``True`` if it existed."""
        deleted = self._store(dataset_tag).delete_session(session_id)
        if deleted:
            lg.info(f"Deleted session {session_id}")
        return deleted

    # ------------------------------------------------------------------
    # Placement operations
    # ------------------------------------------------------------------

    def place_piece(
        self,
        dataset_tag: str,
        session_id: str,
        piece_id: str,
        position: str,
        orientation: int,
    ) -> SolveSessionResponse:
        """Place a piece on the grid.

        Validates that the orientation is legal and that the position is
        within grid bounds by reconstructing a ``PlacementState``.
        """
        store = self._store(dataset_tag)
        data = store.load_session(session_id)
        if data is None:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        rows: int = data["grid_rows"]  # type: ignore[assignment]
        cols: int = data["grid_cols"]  # type: ignore[assignment]
        grid = GridModel(rows, cols)

        # Validate orientation
        orient = Orientation(orientation)

        # Rebuild current state and apply the new placement
        placement: dict[str, tuple[str, int]] = data["placement"]  # type: ignore[assignment]
        state = PlacementState.from_dict(grid, placement)

        pos = _parse_pos(position)
        pid = PieceId.from_str(piece_id)
        state.place(pid, pos, orient)

        # Update session data
        data["placement"] = state.to_dict()
        undo_stack: list[str] = data.get("undo_stack", [])  # type: ignore[assignment]
        undo_stack.append(position)
        data["undo_stack"] = undo_stack
        data["complete"] = state.is_complete()
        data["updated_at"] = _now_iso()

        store.save_session(data)
        lg.info(
            f"Placed {piece_id} at {position}"
            f" (orient={orientation}) in session {session_id}",
        )
        return _response_from_data(data)

    def undo(
        self,
        dataset_tag: str,
        session_id: str,
    ) -> SolveSessionResponse:
        """Remove the last placed piece (undo stack)."""
        store = self._store(dataset_tag)
        data = store.load_session(session_id)
        if data is None:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        undo_stack: list[str] = data.get("undo_stack", [])  # type: ignore[assignment]
        if not undo_stack:
            msg = "Nothing to undo"
            raise ValueError(msg)

        last_pos_str = undo_stack.pop()

        rows: int = data["grid_rows"]  # type: ignore[assignment]
        cols: int = data["grid_cols"]  # type: ignore[assignment]
        grid = GridModel(rows, cols)

        placement: dict[str, tuple[str, int]] = data["placement"]  # type: ignore[assignment]
        state = PlacementState.from_dict(grid, placement)

        pos = _parse_pos(last_pos_str)
        removed = state.remove(pos)

        data["placement"] = state.to_dict()
        data["undo_stack"] = undo_stack
        data["complete"] = False
        data["updated_at"] = _now_iso()

        store.save_session(data)
        if removed:
            pid, _orient = removed
            lg.info(
                f"Undid placement of {pid} at {last_pos_str} in session {session_id}",
            )
        return _response_from_data(data)

    # ------------------------------------------------------------------
    # Suggestion engine
    # ------------------------------------------------------------------

    def _load_matcher(self, dataset_tag: str) -> PieceMatcher:
        """Return a score-only PieceMatcher loaded from the dataset DB.

        Results are cached in the module-level ``_matcher_cache`` so the
        (potentially large) match table is only read once per process.
        """
        if dataset_tag not in _matcher_cache:
            db_path = self._cache_path / dataset_tag / "dataset.db"
            if not db_path.exists():
                msg = f"No database found for dataset '{dataset_tag}'"
                raise ValueError(msg)
            matcher = PieceMatcher(manager=None)
            matcher.load_matches_db(db_path)
            _matcher_cache[dataset_tag] = matcher
            lg.info(
                f"Loaded matcher for '{dataset_tag}'"
                f" ({len(matcher.results)} matches cached)",
            )
        return _matcher_cache[dataset_tag]

    def _invalidate_matcher_cache(self, dataset_tag: str) -> None:
        """Remove the cached matcher so the next call reloads from DB."""
        _matcher_cache.pop(dataset_tag, None)

    def suggest_next(
        self,
        dataset_tag: str,
        session_id: str,
        override_pos: str | None = None,
        top_k: int = 5,
    ) -> SuggestionBundle:
        """Generate ranked candidates for the next open slot.

        Uses the most-constrained-first strategy: the empty slot with the
        most already-placed neighbors is scored first.  The resulting
        ``SuggestionBundle`` is saved as ``pending_suggestion`` in the
        session so :meth:`accept` and :meth:`reject` can act on it.

        Args:
            dataset_tag: Dataset the session belongs to.
            session_id: Session identifier.
            override_pos: If given (``"ro,co"`` string), force this slot
                instead of auto-picking.
            top_k: Maximum number of candidates to return.

        Returns:
            ``SuggestionBundle`` with ranked candidates (empty if the grid
            is already complete).

        Raises:
            ValueError: If the session does not exist.
        """
        store = self._store(dataset_tag)
        data = store.load_session(session_id)
        if data is None:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        rows: int = data["grid_rows"]  # type: ignore[assignment]
        cols: int = data["grid_cols"]  # type: ignore[assignment]
        grid = GridModel(rows, cols)
        placement: dict[str, tuple[str, int]] = data["placement"]  # type: ignore[assignment]
        state = PlacementState.from_dict(grid, placement)

        override = _parse_pos(override_pos) if override_pos is not None else None
        target_pos = pick_next_slot(state, override_pos=override)

        if target_pos is None:
            # Grid is complete - return empty bundle
            bundle = SuggestionBundle(slot="", candidates=[], current_index=0)
            data["pending_suggestion"] = None
            data["updated_at"] = _now_iso()
            store.save_session(data)
            return bundle

        slot_key = f"{target_pos.ro},{target_pos.co}"
        all_pieces = store.load_pieces()
        placed_ids = set(state.placed_pieces())
        corners, edges, inners = _partition_from_records(all_pieces)
        slot_type = grid.get_slot_type(target_pos)

        if slot_type.piece_type == PieceType.CORNER:
            type_pool = corners
        elif slot_type.piece_type == PieceType.EDGE:
            type_pool = edges
        else:
            type_pool = inners

        available = [pid for pid in type_pool if pid not in placed_ids]

        rejected_raw: dict[str, list[str]] = data.get("rejected", {})  # type: ignore[assignment]
        rejected_set = {PieceId.from_str(s) for s in rejected_raw.get(slot_key, [])}

        matcher = self._load_matcher(dataset_tag)
        raw_candidates = score_candidates(
            state, target_pos, matcher, available, rejected_set, top_k
        )

        labels = {r.piece_id: r.label for r in all_pieces}
        candidates = [
            SuggestionCandidate(
                piece_id=str(c.piece_id),
                piece_label=labels.get(c.piece_id),
                orientation=c.orientation.value,
                score=c.score,
                neighbor_scores=c.neighbor_scores,
            )
            for c in raw_candidates
        ]
        bundle = SuggestionBundle(slot=slot_key, candidates=candidates, current_index=0)

        data["pending_suggestion"] = bundle.model_dump()
        data["updated_at"] = _now_iso()
        store.save_session(data)

        lg.info(
            f"Suggest {len(candidates)} candidates for slot {slot_key}"
            f" in session {session_id}",
        )
        return bundle

    def accept(
        self,
        dataset_tag: str,
        session_id: str,
    ) -> SolveSessionResponse:
        """Accept the current pending suggestion candidate.

        Places the piece at ``pending_suggestion.candidates[current_index]``,
        updates ``similarity_manual`` to ``0`` for the scored edge pairs
        (marking them as confirmed matches), clears ``pending_suggestion``,
        and persists the session.

        Args:
            dataset_tag: Dataset the session belongs to.
            session_id: Session identifier.

        Returns:
            Updated ``SolveSessionResponse`` with the piece placed.

        Raises:
            ValueError: If the session does not exist or has no pending
                suggestion.
        """
        store = self._store(dataset_tag)
        data = store.load_session(session_id)
        if data is None:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        ps_raw = data.get("pending_suggestion")
        if ps_raw is None:
            msg = "No pending suggestion to accept"
            raise ValueError(msg)

        bundle = SuggestionBundle.model_validate(ps_raw)
        if bundle.current_index >= len(bundle.candidates):
            msg = "No candidate at current index"
            raise ValueError(msg)

        candidate = bundle.candidates[bundle.current_index]

        rows: int = data["grid_rows"]  # type: ignore[assignment]
        cols: int = data["grid_cols"]  # type: ignore[assignment]
        grid = GridModel(rows, cols)
        placement: dict[str, tuple[str, int]] = data["placement"]  # type: ignore[assignment]
        state = PlacementState.from_dict(grid, placement)

        pos = _parse_pos(bundle.slot)
        pid = PieceId.from_str(candidate.piece_id)
        orient = Orientation(candidate.orientation)

        # Compute segment pairs before placing so neighbors are unambiguous
        pairs = get_scored_segment_pairs(state, pos, pid, orient)

        state.place(pid, pos, orient)

        # Mark each scored edge pair as confirmed (similarity_manual = 0)
        for seg_a, seg_b in pairs:
            store.update_match_manual_score(seg_a, seg_b, 0.0)

        # Invalidate cached matcher so updated scores are picked up next suggest
        self._invalidate_matcher_cache(dataset_tag)

        undo_stack: list[str] = data.get("undo_stack", [])  # type: ignore[assignment]
        undo_stack.append(bundle.slot)
        data["placement"] = state.to_dict()
        data["undo_stack"] = undo_stack
        data["pending_suggestion"] = None
        data["complete"] = state.is_complete()
        data["updated_at"] = _now_iso()

        store.save_session(data)
        lg.info(
            f"Accepted {candidate.piece_id} at {bundle.slot}"
            f" (orient={candidate.orientation}) in session {session_id}",
        )
        return _response_from_data(data)

    def reject(
        self,
        dataset_tag: str,
        session_id: str,
    ) -> SuggestionBundle:
        """Reject the current pending suggestion candidate.

        Adds the rejected piece to ``session.rejected[slot]``, updates
        ``similarity_manual`` to ``1e6`` for its scored edge pairs, and
        advances ``current_index``.  When all pre-generated candidates are
        exhausted, :meth:`suggest_next` is called for the same slot to
        generate a fresh bundle (which excludes all previously rejected pieces).

        Args:
            dataset_tag: Dataset the session belongs to.
            session_id: Session identifier.

        Returns:
            Updated ``SuggestionBundle`` (same slot with next candidate, or
            a fresh bundle if all candidates were exhausted).

        Raises:
            ValueError: If the session does not exist or has no pending
                suggestion.
        """
        store = self._store(dataset_tag)
        data = store.load_session(session_id)
        if data is None:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        ps_raw = data.get("pending_suggestion")
        if ps_raw is None:
            msg = "No pending suggestion to reject"
            raise ValueError(msg)

        bundle = SuggestionBundle.model_validate(ps_raw)
        if bundle.current_index >= len(bundle.candidates):
            msg = "No candidate at current index"
            raise ValueError(msg)

        candidate = bundle.candidates[bundle.current_index]
        slot_key = bundle.slot

        # Add to rejected set for this slot
        rejected_raw: dict[str, list[str]] = data.get("rejected", {})  # type: ignore[assignment]
        slot_rejected = rejected_raw.get(slot_key, [])
        if candidate.piece_id not in slot_rejected:
            slot_rejected = [*slot_rejected, candidate.piece_id]
        rejected_raw[slot_key] = slot_rejected
        data["rejected"] = rejected_raw

        # Mark each scored pair as rejected (similarity_manual = 1e6)
        rows: int = data["grid_rows"]  # type: ignore[assignment]
        cols: int = data["grid_cols"]  # type: ignore[assignment]
        grid = GridModel(rows, cols)
        placement: dict[str, tuple[str, int]] = data["placement"]  # type: ignore[assignment]
        state = PlacementState.from_dict(grid, placement)
        pos = _parse_pos(slot_key)
        pid = PieceId.from_str(candidate.piece_id)
        orient = Orientation(candidate.orientation)
        for seg_a, seg_b in get_scored_segment_pairs(state, pos, pid, orient):
            store.update_match_manual_score(seg_a, seg_b, 1e6)

        self._invalidate_matcher_cache(dataset_tag)

        new_index = bundle.current_index + 1
        data["updated_at"] = _now_iso()

        if new_index < len(bundle.candidates):
            # More pre-generated candidates remain - advance the index
            updated_bundle = SuggestionBundle(
                slot=slot_key,
                candidates=bundle.candidates,
                current_index=new_index,
            )
            data["pending_suggestion"] = updated_bundle.model_dump()
            store.save_session(data)
            lg.info(
                f"Rejected {candidate.piece_id} for slot {slot_key}"
                f" in session {session_id}; showing candidate {new_index}",
            )
            return updated_bundle

        # All candidates exhausted - regenerate for the same slot
        data["pending_suggestion"] = None
        store.save_session(data)
        lg.info(
            f"Rejected {candidate.piece_id} for slot {slot_key}"
            f" in session {session_id}; regenerating candidates",
        )
        return self.suggest_next(
            dataset_tag, session_id, override_pos=slot_key, top_k=5
        )
