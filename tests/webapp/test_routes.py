"""Smoke tests for webapp routes."""

from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from snap_fit.webapp.main import create_app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    """Create test client with isolated cache."""
    import os

    from snap_fit.webapp.core.settings import get_settings

    os.environ["CACHE_DIR"] = str(tmp_path)
    get_settings.cache_clear()
    app = create_app()
    yield TestClient(app)
    get_settings.cache_clear()
    os.environ.pop("CACHE_DIR", None)


class TestDebugEndpoints:
    """Tests for debug/health check endpoints."""

    def test_ping(self, client: TestClient) -> None:
        """Health endpoint returns ok."""
        response = client.get("/api/v1/debug/ping")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_info(self, client: TestClient) -> None:
        """Info endpoint returns version."""
        response = client.get("/api/v1/debug/info")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "debug" in data


class TestOpenAPI:
    """Tests for OpenAPI documentation."""

    def test_openapi_available(self, client: TestClient) -> None:
        """OpenAPI schema is generated."""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        assert "paths" in response.json()

    def test_swagger_ui(self, client: TestClient) -> None:
        """Swagger UI is accessible."""
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()


class TestPieceEndpoints:
    """Tests for piece-related endpoints."""

    def test_list_pieces_empty(self, client: TestClient) -> None:
        """List pieces returns empty when no cache exists."""
        response = client.get("/api/v1/pieces/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_sheets_empty(self, client: TestClient) -> None:
        """List sheets returns empty when no cache exists."""
        response = client.get("/api/v1/pieces/sheets")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_piece_not_found(self, client: TestClient) -> None:
        """Get piece returns 404 for nonexistent piece."""
        response = client.get("/api/v1/pieces/nonexistent-0")
        assert response.status_code == 404

    def test_ingest_unknown_tag(self, client: TestClient) -> None:
        """Ingest returns 400 for an unknown sheets_tag (config not found)."""
        response = client.post(
            "/api/v1/pieces/ingest",
            json={"sheets_tag": "nonexistent_dataset"},
        )
        assert response.status_code == 400


class TestPuzzleEndpoints:
    """Tests for puzzle-related endpoints."""

    def test_list_matches_empty(self, client: TestClient) -> None:
        """List matches returns empty when no cache exists."""
        response = client.get("/api/v1/puzzle/matches")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_match_count_empty(self, client: TestClient) -> None:
        """Match count returns 0 when no cache exists."""
        response = client.get("/api/v1/puzzle/matches/count")
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_solve_placeholder(self, client: TestClient) -> None:
        """Solve returns placeholder response."""
        response = client.post(
            "/api/v1/puzzle/solve",
            json={"piece_ids": ["test-0", "test-1"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "pending" in data["message"].lower()


class TestUIEndpoints:
    """Tests for HTML UI endpoints."""

    def test_home_page(self, client: TestClient) -> None:
        """Home page renders."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_sheets_page(self, client: TestClient) -> None:
        """Sheets page renders."""
        response = client.get("/sheets")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_pieces_page(self, client: TestClient) -> None:
        """Pieces page renders."""
        response = client.get("/pieces")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_matches_page(self, client: TestClient) -> None:
        """Matches page renders."""
        response = client.get("/matches")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestWithCachedData:
    """Tests with mock cached data."""

    def test_pieces_with_mock_data(self, tmp_path: Path) -> None:
        """List pieces returns data when cache exists."""
        from snap_fit.data_models.piece_record import PieceRecord
        from snap_fit.data_models.sheet_record import SheetRecord
        from snap_fit.persistence.sqlite_store import DatasetStore

        sheet_record = SheetRecord.model_validate(
            {
                "sheet_id": "test_sheet",
                "img_path": "data/test.png",
                "piece_count": 1,
                "threshold": 130,
                "min_area": 80000,
                "created_at": "2025-01-01T00:00:00",
            }
        )
        piece_record = PieceRecord.model_validate(
            {
                "piece_id": {"sheet_id": "test_sheet", "piece_id": 0},
                "corners": {
                    "TL": [0, 0],
                    "TR": [100, 0],
                    "BR": [100, 100],
                    "BL": [0, 100],
                },
                "segment_shapes": {
                    "TOP": "OUT",
                    "RIGHT": "IN",
                    "BOTTOM": "OUT",
                    "LEFT": "IN",
                },
                "oriented_piece_type": {"piece_type": 0, "orientation": 0},
                "flat_edges": [],
                "contour_point_count": 100,
                "contour_region": [0, 0, 100, 100],
            }
        )
        db_path = tmp_path / "test_tag" / "dataset.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with DatasetStore(db_path) as store:
            store.save_sheets([sheet_record])
            store.save_pieces([piece_record])

        # Update settings to use tmp cache
        import os

        os.environ["CACHE_DIR"] = str(tmp_path)
        from snap_fit.webapp.core.settings import get_settings

        get_settings.cache_clear()

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/pieces/")
        assert response.status_code == 200
        pieces = response.json()
        assert len(pieces) == 1
        assert pieces[0]["piece_id"]["sheet_id"] == "test_sheet"

        # Cleanup
        get_settings.cache_clear()
        del os.environ["CACHE_DIR"]

    def test_piece_img_from_processed_sheet(self, tmp_path: Path) -> None:
        """Piece image endpoint crops from the processed sheet image."""
        import os

        import cv2
        import numpy as np

        from snap_fit.data_models.piece_record import PieceRecord
        from snap_fit.data_models.sheet_record import SheetRecord
        from snap_fit.persistence.sqlite_store import DatasetStore

        # Create a synthetic processed sheet image (200x300 BGR)
        sheet_img = np.zeros((200, 300, 3), dtype=np.uint8)
        # Paint a recognizable region at (x0=10, y0=20, w=50, h=40) red
        sheet_img[20:60, 10:60] = (0, 0, 255)

        tag_dir = tmp_path / "test_tag"
        sheets_dir = tag_dir / "sheets"
        sheets_dir.mkdir(parents=True)
        cv2.imwrite(str(sheets_dir / "test_sheet.jpg"), sheet_img)

        sheet_record = SheetRecord.model_validate(
            {
                "sheet_id": "test_sheet",
                "img_path": "data/test.png",
                "piece_count": 1,
                "threshold": 130,
                "min_area": 80000,
                "created_at": "2025-01-01T00:00:00",
            }
        )
        piece_record = PieceRecord.model_validate(
            {
                "piece_id": {"sheet_id": "test_sheet", "piece_id": 0},
                "corners": {
                    "TL": [0, 0],
                    "TR": [100, 0],
                    "BR": [100, 100],
                    "BL": [0, 100],
                },
                "segment_shapes": {
                    "TOP": "OUT",
                    "RIGHT": "IN",
                    "BOTTOM": "OUT",
                    "LEFT": "IN",
                },
                "oriented_piece_type": {"piece_type": 0, "orientation": 0},
                "flat_edges": [],
                "contour_point_count": 100,
                "contour_region": [0, 0, 50, 40],
                "sheet_origin": [10, 20],
                "padded_size": [50, 40],
            }
        )

        db_path = tag_dir / "dataset.db"
        with DatasetStore(db_path) as store:
            store.save_sheets([sheet_record])
            store.save_pieces([piece_record])

        os.environ["CACHE_DIR"] = str(tmp_path)
        from snap_fit.webapp.core.settings import get_settings

        get_settings.cache_clear()

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/pieces/test_sheet:0/img")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

        # Verify PNG header
        assert response.content[:4] == b"\x89PNG"

        # Decode and verify dimensions match padded_size (w=50, h=40)
        img_array = np.frombuffer(response.content, dtype=np.uint8)
        decoded = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        assert decoded is not None
        assert decoded.shape[0] == 40  # height
        assert decoded.shape[1] == 50  # width

        # Verify the crop contains the red region
        # (JPEG lossy compression reduces values)
        assert decoded[0, 0, 2] > 100  # red channel should be high

        # Cleanup
        get_settings.cache_clear()
        del os.environ["CACHE_DIR"]

    def test_piece_img_not_found(self, tmp_path: Path) -> None:
        """Piece image returns 404 for nonexistent piece."""
        import os

        os.environ["CACHE_DIR"] = str(tmp_path)
        from snap_fit.webapp.core.settings import get_settings

        get_settings.cache_clear()

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/pieces/nonexistent:0/img")
        assert response.status_code == 404

        get_settings.cache_clear()
        del os.environ["CACHE_DIR"]


class TestRunMatchingEndpoint:
    """Tests for the run_matching endpoint."""

    def test_run_matching_unknown_tag_returns_400(self, client: TestClient) -> None:
        """run_matching returns 400 when the dataset config is not found."""
        response = client.post(
            "/api/v1/puzzle/run_matching",
            json={"dataset_tag": "nonexistent_dataset"},
        )
        assert response.status_code == 400

    def test_run_matching_skips_when_matches_exist(self, tmp_path: Path) -> None:
        """run_matching with force=False returns existing count without re-running."""
        import os

        from snap_fit.config.types import EdgePos
        from snap_fit.data_models.match_result import MatchResult
        from snap_fit.data_models.piece_id import PieceId
        from snap_fit.data_models.segment_id import SegmentId
        from snap_fit.persistence.sqlite_store import DatasetStore
        from snap_fit.webapp.core.settings import get_settings

        tag_dir = tmp_path / "demo"
        tag_dir.mkdir(parents=True)
        db_path = tag_dir / "dataset.db"

        seg1 = SegmentId(
            piece_id=PieceId(sheet_id="s1", piece_id=0), edge_pos=EdgePos.TOP
        )
        seg2 = SegmentId(
            piece_id=PieceId(sheet_id="s1", piece_id=1), edge_pos=EdgePos.BOTTOM
        )
        match = MatchResult(seg_id1=seg1, seg_id2=seg2, similarity=0.5)
        with DatasetStore(db_path) as store:
            store.save_matches([match])

        os.environ["CACHE_DIR"] = str(tmp_path)
        get_settings.cache_clear()
        app = create_app()
        local_client = TestClient(app)

        response = local_client.post(
            "/api/v1/puzzle/run_matching",
            json={"dataset_tag": "demo", "force": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["match_count"] == 1
        assert data["duration_seconds"] == 0.0

        get_settings.cache_clear()
        del os.environ["CACHE_DIR"]
