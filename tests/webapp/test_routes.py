"""Smoke tests for webapp routes."""

from collections.abc import Iterator
import json
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
        # Create mock metadata matching actual serialization format
        metadata = {
            "sheets": [
                {
                    "sheet_id": "test_sheet",
                    "img_path": "data/test.png",
                    "piece_count": 1,
                    "threshold": 130,
                    "min_area": 80000,
                    "created_at": "2025-01-01T00:00:00",
                }
            ],
            "pieces": [
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
                },
            ],
        }
        metadata_path = tmp_path / "test_tag" / "metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata))

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
