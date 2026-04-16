"""Service layer for interactive solve sessions."""

from datetime import UTC
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from loguru import logger as lg

from snap_fit.data_models.piece_id import PieceId
from snap_fit.grid.grid_model import GridModel
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.placement_state import PlacementState
from snap_fit.grid.types import GridPos
from snap_fit.persistence.sqlite_store import DatasetStore
from snap_fit.solver.utils import get_factor_pairs
from snap_fit.webapp.schemas.interactive import SolveSessionResponse


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
        created_at=data["created_at"],  # type: ignore[arg-type]
        updated_at=data["updated_at"],  # type: ignore[arg-type]
    )


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
