"""Tests for InteractiveService and interactive router endpoints."""

from collections.abc import Iterator
from datetime import UTC
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from snap_fit.data_models.piece_id import PieceId
from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.data_models.sheet_record import SheetRecord
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation import OrientedPieceType
from snap_fit.grid.orientation import PieceType
from snap_fit.persistence.sqlite_store import DatasetStore
from snap_fit.webapp.services.interactive_service import InteractiveService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TAG = "test_ds"

_CORNERS = {
    "top_left": (10, 20),
    "bottom_left": (10, 80),
    "bottom_right": (90, 80),
    "top_right": (90, 20),
}

_SEGMENT_SHAPES = {
    "left": "out",
    "bottom": "in",
    "right": "out",
    "top": "edge",
}


def _seed_dataset(cache_dir: Path, *, tag: str = _TAG, n_pieces: int = 4) -> None:
    """Create a dataset.db with a sheet and ``n_pieces`` pieces."""
    db_path = cache_dir / tag / "dataset.db"
    store = DatasetStore(db_path)
    store.save_sheets(
        [
            SheetRecord(
                sheet_id="s.jpg",
                img_path=Path("data/s.jpg"),
                piece_count=n_pieces,
                threshold=130,
                min_area=80_000,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
        ]
    )
    pieces = [
        PieceRecord(
            piece_id=PieceId(sheet_id="s.jpg", piece_id=i),
            corners=_CORNERS,
            segment_shapes=_SEGMENT_SHAPES,
            oriented_piece_type=OrientedPieceType(
                piece_type=PieceType.CORNER,
                orientation=Orientation.DEG_0,
            ),
            flat_edges=["top", "left"],
            contour_point_count=500,
            contour_region=(10, 20, 80, 60),
        )
        for i in range(n_pieces)
    ]
    store.save_pieces(pieces)
    store.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    """Return a temporary cache directory."""
    return tmp_path / "cache"


@pytest.fixture
def service(cache_dir: Path) -> InteractiveService:
    """Return an InteractiveService backed by a seeded test dataset."""
    _seed_dataset(cache_dir)
    return InteractiveService(cache_dir, data_path=cache_dir)


# ---------------------------------------------------------------------------
# InteractiveService unit tests
# ---------------------------------------------------------------------------


class TestCreateSession:
    """Tests for InteractiveService.create_session."""

    def test_create_with_explicit_grid(self, service: InteractiveService) -> None:
        """Create session with explicit grid dimensions."""
        resp = service.create_session(_TAG, grid_rows=2, grid_cols=2)
        assert resp.session_id
        assert resp.dataset_tag == _TAG
        assert resp.grid_rows == 2
        assert resp.grid_cols == 2
        assert resp.placed_count == 0
        assert resp.total_cells == 4
        assert resp.complete is False

    def test_create_with_inferred_grid(self, service: InteractiveService) -> None:
        """Create session with grid inferred from piece count."""
        resp = service.create_session(_TAG)
        assert resp.grid_rows * resp.grid_cols == 4

    def test_create_cannot_infer_prime_count(self, cache_dir: Path) -> None:
        """Cannot infer grid from a prime piece count."""
        _seed_dataset(cache_dir, tag="prime", n_pieces=7)
        svc = InteractiveService(cache_dir, data_path=cache_dir)
        with pytest.raises(ValueError, match="Cannot infer"):
            svc.create_session("prime")


class TestGetSession:
    """Tests for InteractiveService.get_session."""

    def test_get_existing(self, service: InteractiveService) -> None:
        """Load a session that exists."""
        created = service.create_session(_TAG, 2, 2)
        loaded = service.get_session(_TAG, created.session_id)
        assert loaded is not None
        assert loaded.session_id == created.session_id

    def test_get_missing(self, service: InteractiveService) -> None:
        """Return None for unknown session."""
        assert service.get_session(_TAG, "nonexistent") is None


class TestListSessions:
    """Tests for InteractiveService.list_sessions."""

    def test_list_empty(self, service: InteractiveService) -> None:
        """Empty list when no sessions exist."""
        assert service.list_sessions(_TAG) == []

    def test_list_after_create(self, service: InteractiveService) -> None:
        """Both sessions appear after creation."""
        service.create_session(_TAG, 2, 2)
        service.create_session(_TAG, 2, 2)
        assert len(service.list_sessions(_TAG)) == 2


class TestDeleteSession:
    """Tests for InteractiveService.delete_session."""

    def test_delete_existing(self, service: InteractiveService) -> None:
        """Delete an existing session."""
        created = service.create_session(_TAG, 2, 2)
        assert service.delete_session(_TAG, created.session_id) is True
        assert service.get_session(_TAG, created.session_id) is None

    def test_delete_missing(self, service: InteractiveService) -> None:
        """Deleting a nonexistent session returns False."""
        assert service.delete_session(_TAG, "nonexistent") is False


class TestPlacePiece:
    """Tests for InteractiveService.place_piece."""

    def test_place_piece(self, service: InteractiveService) -> None:
        """Place one piece and verify state."""
        sess = service.create_session(_TAG, 2, 2)
        resp = service.place_piece(_TAG, sess.session_id, "s.jpg:0", "0,0", 0)
        assert resp.placed_count == 1
        assert "0,0" in resp.placement
        assert resp.undo_stack == ["0,0"]

    def test_place_invalid_position(self, service: InteractiveService) -> None:
        """Out-of-bounds placement raises."""
        sess = service.create_session(_TAG, 2, 2)
        with pytest.raises((ValueError, KeyError)):
            service.place_piece(_TAG, sess.session_id, "s.jpg:0", "10,10", 0)

    def test_place_invalid_orientation(self, service: InteractiveService) -> None:
        """Non-standard orientation raises."""
        sess = service.create_session(_TAG, 2, 2)
        with pytest.raises(ValueError, match="not a valid"):
            service.place_piece(_TAG, sess.session_id, "s.jpg:0", "0,0", 45)

    def test_place_on_missing_session(self, service: InteractiveService) -> None:
        """Placing on nonexistent session raises."""
        with pytest.raises(ValueError, match="not found"):
            service.place_piece(_TAG, "nonexistent", "s.jpg:0", "0,0", 0)

    def test_complete_after_fill(self, service: InteractiveService) -> None:
        """Session marked complete when all cells filled."""
        sess = service.create_session(_TAG, 2, 2)
        service.place_piece(_TAG, sess.session_id, "s.jpg:0", "0,0", 0)
        service.place_piece(_TAG, sess.session_id, "s.jpg:1", "0,1", 0)
        service.place_piece(_TAG, sess.session_id, "s.jpg:2", "1,0", 0)
        resp = service.place_piece(_TAG, sess.session_id, "s.jpg:3", "1,1", 0)
        assert resp.complete is True
        assert resp.placed_count == 4


class TestUndo:
    """Tests for InteractiveService.undo."""

    def test_undo_removes_last(self, service: InteractiveService) -> None:
        """Undo removes the most recently placed piece."""
        sess = service.create_session(_TAG, 2, 2)
        service.place_piece(_TAG, sess.session_id, "s.jpg:0", "0,0", 0)
        service.place_piece(_TAG, sess.session_id, "s.jpg:1", "1,1", 90)
        resp = service.undo(_TAG, sess.session_id)
        assert resp.placed_count == 1
        assert "1,1" not in resp.placement
        assert resp.undo_stack == ["0,0"]

    def test_undo_empty_raises(self, service: InteractiveService) -> None:
        """Undo on empty session raises."""
        sess = service.create_session(_TAG, 2, 2)
        with pytest.raises(ValueError, match="Nothing to undo"):
            service.undo(_TAG, sess.session_id)


# ---------------------------------------------------------------------------
# HTTP route integration tests
# ---------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    """Create test client with isolated cache and a seeded dataset."""
    import os

    from snap_fit.webapp.core.settings import get_settings

    cache_dir = tmp_path / "cache"
    _seed_dataset(cache_dir)

    os.environ["CACHE_DIR"] = str(cache_dir)
    os.environ["DATA_DIR"] = str(cache_dir)
    get_settings.cache_clear()

    from snap_fit.webapp.main import create_app

    app = create_app()
    yield TestClient(app)

    get_settings.cache_clear()
    os.environ.pop("CACHE_DIR", None)
    os.environ.pop("DATA_DIR", None)


class TestInteractiveRoutes:
    """Integration tests for interactive session HTTP endpoints."""

    def test_create_session(self, client: TestClient) -> None:
        """POST create returns a valid session."""
        resp = client.post(
            "/api/v1/interactive/sessions",
            json={"dataset_tag": _TAG, "grid_rows": 2, "grid_cols": 2},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"]
        assert data["grid_rows"] == 2
        assert data["placed_count"] == 0

    def test_list_sessions(self, client: TestClient) -> None:
        """GET list returns created sessions."""
        client.post(
            "/api/v1/interactive/sessions",
            json={"dataset_tag": _TAG, "grid_rows": 2, "grid_cols": 2},
        )
        resp = client.get(
            "/api/v1/interactive/sessions",
            params={"dataset_tag": _TAG},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_session(self, client: TestClient) -> None:
        """GET session by ID returns correct data."""
        create_resp = client.post(
            "/api/v1/interactive/sessions",
            json={"dataset_tag": _TAG, "grid_rows": 2, "grid_cols": 2},
        )
        sid = create_resp.json()["session_id"]
        resp = client.get(
            f"/api/v1/interactive/sessions/{sid}",
            params={"dataset_tag": _TAG},
        )
        assert resp.status_code == 200
        assert resp.json()["session_id"] == sid

    def test_get_session_not_found(self, client: TestClient) -> None:
        """GET unknown session returns 404."""
        resp = client.get(
            "/api/v1/interactive/sessions/nonexistent",
            params={"dataset_tag": _TAG},
        )
        assert resp.status_code == 404

    def test_place_piece(self, client: TestClient) -> None:
        """POST place returns updated state."""
        create_resp = client.post(
            "/api/v1/interactive/sessions",
            json={"dataset_tag": _TAG, "grid_rows": 2, "grid_cols": 2},
        )
        sid = create_resp.json()["session_id"]
        resp = client.post(
            f"/api/v1/interactive/sessions/{sid}/place",
            json={"piece_id": "s.jpg:0", "position": "0,0", "orientation": 0},
            params={"dataset_tag": _TAG},
        )
        assert resp.status_code == 200
        assert resp.json()["placed_count"] == 1

    def test_undo(self, client: TestClient) -> None:
        """POST undo reverts last placement."""
        create_resp = client.post(
            "/api/v1/interactive/sessions",
            json={"dataset_tag": _TAG, "grid_rows": 2, "grid_cols": 2},
        )
        sid = create_resp.json()["session_id"]
        client.post(
            f"/api/v1/interactive/sessions/{sid}/place",
            json={"piece_id": "s.jpg:0", "position": "0,0", "orientation": 0},
            params={"dataset_tag": _TAG},
        )
        resp = client.post(
            f"/api/v1/interactive/sessions/{sid}/undo",
            params={"dataset_tag": _TAG},
        )
        assert resp.status_code == 200
        assert resp.json()["placed_count"] == 0

    def test_delete_session(self, client: TestClient) -> None:
        """DELETE session removes it."""
        create_resp = client.post(
            "/api/v1/interactive/sessions",
            json={"dataset_tag": _TAG, "grid_rows": 2, "grid_cols": 2},
        )
        sid = create_resp.json()["session_id"]
        resp = client.delete(
            f"/api/v1/interactive/sessions/{sid}",
            params={"dataset_tag": _TAG},
        )
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_delete_session_not_found(self, client: TestClient) -> None:
        """DELETE unknown session returns 404."""
        resp = client.delete(
            "/api/v1/interactive/sessions/nonexistent",
            params={"dataset_tag": _TAG},
        )
        assert resp.status_code == 404

    def test_create_session_bad_grid(self, client: TestClient) -> None:
        """Create with bad dataset returns 400."""
        resp = client.post(
            "/api/v1/interactive/sessions",
            json={"dataset_tag": "nonexistent"},
        )
        assert resp.status_code == 400

    def test_requires_dataset_tag(self, client: TestClient) -> None:
        """List sessions without dataset_tag returns 400."""
        resp = client.get("/api/v1/interactive/sessions")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Suggestion engine service tests
# ---------------------------------------------------------------------------


def _seed_with_matches(
    cache_dir: Path,
    *,
    tag: str = _TAG,
    n_pieces: int = 4,
) -> None:
    """Seed a dataset with pieces AND an empty matches table so suggest_next works."""
    _seed_dataset(cache_dir, tag=tag, n_pieces=n_pieces)
    # The matches table is created by _ensure_schema but has no rows.
    # suggest_next still works - uncached pairs get score 1e6.


class TestSuggestNext:
    """Tests for InteractiveService.suggest_next."""

    def test_suggest_no_pieces_placed_returns_bundle(self, cache_dir: Path) -> None:
        """suggest_next on an empty grid returns a bundle for a corner slot."""
        _seed_with_matches(cache_dir)
        svc = InteractiveService(cache_dir, data_path=cache_dir)
        sess = svc.create_session(_TAG, 2, 2)
        # Place one piece so the solver has a neighbor to score against
        svc.place_piece(_TAG, sess.session_id, "s.jpg:0", "0,0", 0)

        bundle = svc.suggest_next(_TAG, sess.session_id)
        assert bundle.slot != ""
        assert isinstance(bundle.candidates, list)
        assert bundle.current_index == 0

    def test_suggest_stores_pending_in_session(self, cache_dir: Path) -> None:
        """suggest_next persists pending_suggestion in the session."""
        _seed_with_matches(cache_dir)
        svc = InteractiveService(cache_dir, data_path=cache_dir)
        sess = svc.create_session(_TAG, 2, 2)
        svc.place_piece(_TAG, sess.session_id, "s.jpg:0", "0,0", 0)

        svc.suggest_next(_TAG, sess.session_id)
        reloaded = svc.get_session(_TAG, sess.session_id)
        assert reloaded is not None
        assert reloaded.pending_suggestion is not None

    def test_suggest_complete_grid_returns_empty_bundle(self, cache_dir: Path) -> None:
        """suggest_next on a filled grid returns an empty bundle."""
        _seed_with_matches(cache_dir)
        svc = InteractiveService(cache_dir, data_path=cache_dir)
        sess = svc.create_session(_TAG, 2, 2)
        for i, pos in enumerate(["0,0", "0,1", "1,0", "1,1"]):
            svc.place_piece(_TAG, sess.session_id, f"s.jpg:{i}", pos, 0)

        bundle = svc.suggest_next(_TAG, sess.session_id)
        assert bundle.slot == ""
        assert bundle.candidates == []

    def test_suggest_missing_session_raises(self, cache_dir: Path) -> None:
        """suggest_next raises for unknown session."""
        _seed_with_matches(cache_dir)
        svc = InteractiveService(cache_dir, data_path=cache_dir)
        with pytest.raises(ValueError, match="not found"):
            svc.suggest_next(_TAG, "nonexistent")

    def test_suggest_override_pos(self, cache_dir: Path) -> None:
        """suggest_next with override_pos targets the requested slot."""
        _seed_with_matches(cache_dir)
        svc = InteractiveService(cache_dir, data_path=cache_dir)
        sess = svc.create_session(_TAG, 2, 2)
        svc.place_piece(_TAG, sess.session_id, "s.jpg:0", "0,0", 0)

        bundle = svc.suggest_next(_TAG, sess.session_id, override_pos="1,0")
        assert bundle.slot == "1,0"


class TestAcceptSuggestion:
    """Tests for InteractiveService.accept."""

    def test_accept_places_piece(self, cache_dir: Path) -> None:
        """Accept places the top candidate and clears pending_suggestion."""
        _seed_with_matches(cache_dir)
        svc = InteractiveService(cache_dir, data_path=cache_dir)
        sess = svc.create_session(_TAG, 2, 2)
        svc.place_piece(_TAG, sess.session_id, "s.jpg:0", "0,0", 0)
        bundle = svc.suggest_next(_TAG, sess.session_id)

        if not bundle.candidates:
            pytest.skip("No candidates generated (no matches in DB)")

        resp = svc.accept(_TAG, sess.session_id)
        assert resp.placed_count == 2
        assert resp.pending_suggestion is None
        assert bundle.slot in resp.placement

    def test_accept_no_pending_raises(self, cache_dir: Path) -> None:
        """Accept without a pending suggestion raises ValueError."""
        _seed_with_matches(cache_dir)
        svc = InteractiveService(cache_dir, data_path=cache_dir)
        sess = svc.create_session(_TAG, 2, 2)
        with pytest.raises(ValueError, match="No pending suggestion"):
            svc.accept(_TAG, sess.session_id)

    def test_accept_missing_session_raises(self, cache_dir: Path) -> None:
        """Accept on unknown session raises ValueError."""
        _seed_with_matches(cache_dir)
        svc = InteractiveService(cache_dir, data_path=cache_dir)
        with pytest.raises(ValueError, match="not found"):
            svc.accept(_TAG, "nonexistent")


class TestRejectSuggestion:
    """Tests for InteractiveService.reject."""

    def test_reject_advances_index(self, cache_dir: Path) -> None:
        """Reject moves current_index forward when candidates remain."""
        _seed_with_matches(cache_dir)
        svc = InteractiveService(cache_dir, data_path=cache_dir)
        sess = svc.create_session(_TAG, 2, 2)
        svc.place_piece(_TAG, sess.session_id, "s.jpg:0", "0,0", 0)
        bundle = svc.suggest_next(_TAG, sess.session_id, top_k=3)

        if len(bundle.candidates) < 2:
            pytest.skip("Fewer than 2 candidates - cannot test index advance")

        updated = svc.reject(_TAG, sess.session_id)
        assert updated.slot == bundle.slot
        assert updated.current_index == 1

    def test_reject_adds_to_rejected_set(self, cache_dir: Path) -> None:
        """Reject records the piece in the session's rejected dict."""
        _seed_with_matches(cache_dir)
        svc = InteractiveService(cache_dir, data_path=cache_dir)
        sess = svc.create_session(_TAG, 2, 2)
        svc.place_piece(_TAG, sess.session_id, "s.jpg:0", "0,0", 0)
        bundle = svc.suggest_next(_TAG, sess.session_id, top_k=2)

        if not bundle.candidates:
            pytest.skip("No candidates generated")

        rejected_piece_id = bundle.candidates[0].piece_id
        svc.reject(_TAG, sess.session_id)
        reloaded = svc.get_session(_TAG, sess.session_id)
        assert reloaded is not None
        slot_rejected = reloaded.rejected.get(bundle.slot, [])
        assert rejected_piece_id in slot_rejected

    def test_reject_no_pending_raises(self, cache_dir: Path) -> None:
        """Reject without a pending suggestion raises ValueError."""
        _seed_with_matches(cache_dir)
        svc = InteractiveService(cache_dir, data_path=cache_dir)
        sess = svc.create_session(_TAG, 2, 2)
        with pytest.raises(ValueError, match="No pending suggestion"):
            svc.reject(_TAG, sess.session_id)


# ---------------------------------------------------------------------------
# Suggestion HTTP route integration tests
# ---------------------------------------------------------------------------


class TestSuggestionRoutes:
    """HTTP integration tests for suggestion endpoints."""

    def test_next_suggestion_returns_bundle(self, client: TestClient) -> None:
        """POST next_suggestion returns a SuggestionBundle."""
        create_resp = client.post(
            "/api/v1/interactive/sessions",
            json={"dataset_tag": _TAG, "grid_rows": 2, "grid_cols": 2},
        )
        sid = create_resp.json()["session_id"]
        # Place a seed piece first
        client.post(
            f"/api/v1/interactive/sessions/{sid}/place",
            json={"piece_id": "s.jpg:0", "position": "0,0", "orientation": 0},
            params={"dataset_tag": _TAG},
        )
        resp = client.post(
            f"/api/v1/interactive/sessions/{sid}/next_suggestion",
            json={},
            params={"dataset_tag": _TAG},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "slot" in data
        assert "candidates" in data
        assert "current_index" in data

    def test_accept_without_pending_returns_400(self, client: TestClient) -> None:
        """POST accept without pending suggestion returns 400."""
        create_resp = client.post(
            "/api/v1/interactive/sessions",
            json={"dataset_tag": _TAG, "grid_rows": 2, "grid_cols": 2},
        )
        sid = create_resp.json()["session_id"]
        resp = client.post(
            f"/api/v1/interactive/sessions/{sid}/accept",
            params={"dataset_tag": _TAG},
        )
        assert resp.status_code == 400

    def test_reject_without_pending_returns_400(self, client: TestClient) -> None:
        """POST reject without pending suggestion returns 400."""
        create_resp = client.post(
            "/api/v1/interactive/sessions",
            json={"dataset_tag": _TAG, "grid_rows": 2, "grid_cols": 2},
        )
        sid = create_resp.json()["session_id"]
        resp = client.post(
            f"/api/v1/interactive/sessions/{sid}/reject",
            params={"dataset_tag": _TAG},
        )
        assert resp.status_code == 400
