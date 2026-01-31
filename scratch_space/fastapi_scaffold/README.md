# FastAPI Scaffold — Feature Plan

> **Status:** ✅ Phase 0 complete (Data Layer); Phase 1 ready  
> **Branch:** `feat/fastapi-scaffold`  
> **Author:** dev_plan_agent  
> **Last updated:** 2025-01-12

---

## Overview

Add a production-ready FastAPI application to the `snap_fit` repository. The web layer will expose puzzle-solving capabilities via a REST API while maintaining clean separation from the existing domain logic in `src/snap_fit/`.

### Evaluated Approaches

| Option                  | Summary                                                                     | Trade-offs                            |
| ----------------------- | --------------------------------------------------------------------------- | ------------------------------------- |
| **A — Minimal Starter** | Single app, modular routers, settings via `pydantic-settings`, CORS, Docker | Fast to ship; extend later for scale  |
| **B — Sub-apps + DI**   | Versioned sub-applications, full dependency injection                       | Better isolation; more boilerplate    |
| **C — Container-First** | Gunicorn workers, Nginx reverse proxy, health probes                        | Production-hardened; overkill for MVP |

**Decision:** Proceed with **Option A** — minimal starter with quality-of-life conveniences (hot reload, Swagger UI, typed settings, path utilities).

---

## Implementation Plan

### Phase 0 — Data Layer (✅ COMPLETE)

> **See:** [01_ingestion_db.md](01_ingestion_db.md) for full design rationale

The persistence layer is implemented and tested. The API will leverage:

| Component                  | Location                                   | Purpose                                                                                                   |
| -------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `SheetRecord`              | `src/snap_fit/data_models/sheet_record.py` | Pydantic model for sheet metadata                                                                         |
| `PieceRecord`              | `src/snap_fit/data_models/piece_record.py` | Pydantic model for piece geometry metadata                                                                |
| `SheetManager` persistence | `src/snap_fit/puzzle/sheet_manager.py`     | `to_records()`, `save_metadata()`, `save_contour_cache()`, `load_metadata()`, `load_contour_for_piece()`  |
| `PieceMatcher` persistence | `src/snap_fit/puzzle/piece_matcher.py`     | `save_matches_json()`, `load_matches_json()`, `get_matched_pair_keys()`, `match_incremental()`, `clear()` |

**Storage Strategy:**

- **Metadata:** JSON files for sheets/pieces (small, human-readable)
- **Contours:** Binary `.npz` files per sheet (efficient, ~12 MB total for 1,500 pieces)
- **Matches:** JSON for small scale; SQLite planned for Phase 2+ (4.5M matches)

### Phase 1 — Scaffold Structure

| #   | Task                                    | Status | Artifact                                |
| --- | --------------------------------------- | ------ | --------------------------------------- |
| 1   | Create feature branch                   | ⬜     | `git checkout -b feat/fastapi-scaffold` |
| 2   | Scaffold `src/snap_fit/webapp/` package | ⬜     | Directory tree below                    |
| 3   | Add `webapp_resources/` at repo root    | ⬜     | Templates + static assets               |
| 4   | Wire up `main.py` entrypoint            | ⬜     | App factory, middleware, router mounts  |

### Phase 2 — Configuration & Infra

| #   | Task                        | Status | Artifact                      |
| --- | --------------------------- | ------ | ----------------------------- |
| 5   | Add `.env.example`          | ⬜     | Environment variable template |
| 6   | Add `Dockerfile` (uv-based) | ⬜     | Multi-stage build             |
| 7   | Add `docker-compose.yml`    | ⬜     | Local dev orchestration       |

### Phase 3 — Docs & Tests

| #   | Task                     | Status | Artifact                    |
| --- | ------------------------ | ------ | --------------------------- |
| 8   | Create `docs/fastapi.md` | ⬜     | Install, run, extend guide  |
| 9   | Add `tests/webapp/`      | ⬜     | Smoke tests for each router |

---

## Data Flow Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                            FastAPI Layer                               │
├────────────────────────────────────────────────────────────────────────┤
│  Routers           │  Services              │  Schemas                 │
│  ────────          │  ────────              │  ────────                │
│  piece_ingestion   │  piece_service         │  SheetRecord (response)  │
│  puzzle_solve      │  puzzle_service        │  PieceRecord (response)  │
│  interactive       │                        │  MatchResult  (response) │
│  debug             │                        │                          │
└────────────────────┴────────────────────────┴──────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         Data Layer (✅ Complete)                       │
├────────────────────────────────────────────────────────────────────────┤
│  SheetManager                    │  PieceMatcher                       │
│  ─────────────                   │  ────────────                       │
│  to_records()                    │  save_matches_json()                │
│  save_metadata(path)             │  load_matches_json()                │
│  save_contour_cache(dir)         │  get_matched_pair_keys()            │
│  load_metadata(path)             │  match_incremental()                │
│  load_contour_for_piece()        │  clear()                            │
└──────────────────────────────────┴─────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           Storage Layer                                │
├────────────────────────────────────────────────────────────────────────┤
│  JSON Files                      │  Binary Cache         │  (Future)   │
│  ──────────                      │  ────────────         │  ────────   │
│  metadata.json                   │  {sheet_id}.npz       │  SQLite     │
│    └─ sheets: SheetRecord[]      │    └─ contour_{id}    │    └─ match │
│    └─ pieces: PieceRecord[]      │  {sheet_id}_corners   │      results│
│  matches.json (small scale)      │      .json            │             │
└──────────────────────────────────┴───────────────────────┴─────────────┘
```

---

## Directory Structure

```text
snap_fit/                           # repo root
├── webapp_resources/               # outside src — static assets & templates
│   ├── static/
│   │   └── css/
│   │       └── styles.css
│   └── templates/
│       └── index.html
│
├── src/snap_fit/webapp/            # FastAPI application package
│   ├── __init__.py
│   ├── main.py                     # app factory & uvicorn entrypoint
│   │
│   ├── core/                       # cross-cutting concerns
│   │   ├── __init__.py
│   │   ├── settings.py             # pydantic-settings config
│   │   └── logging_config.py
│   │
│   ├── api/                        # reserved for future versioned sub-apps
│   │   └── __init__.py
│   │
│   ├── routers/                    # route definitions (no business logic)
│   │   ├── __init__.py
│   │   ├── piece_ingestion.py
│   │   ├── puzzle_solve.py
│   │   ├── interactive.py
│   │   └── debug.py
│   │
│   ├── schemas/                    # Pydantic request/response models
│   │   ├── __init__.py
│   │   ├── piece.py
│   │   ├── puzzle.py
│   │   ├── interactive.py
│   │   └── debug.py
│   │
│   ├── services/                   # thin wrappers around domain logic
│   │   ├── __init__.py
│   │   ├── piece_service.py
│   │   └── puzzle_service.py
│   │
│   └── utils/                      # webapp-specific helpers
│       ├── __init__.py
│       └── paths.py                # resource path resolution
│
├── tests/webapp/                   # webapp test suite
│   ├── __init__.py
│   ├── conftest.py
│   └── test_routes.py
│
├── docs/fastapi.md                 # developer documentation
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

---

## Starter Code Reference

All code follows the project style guide (4-space indent, `loguru` optional, type hints required).

### `src/snap_fit/webapp/__init__.py`

```python
"""snap_fit webapp package."""

__all__ = ["create_app"]
```

### `src/snap_fit/webapp/main.py`

```python
"""FastAPI application factory and entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from snap_fit.webapp.core.settings import get_settings
from snap_fit.webapp.core.logging_config import configure_logging
from snap_fit.webapp.utils.paths import resource_path


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="snap_fit API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # --- Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Static files (optional) ---
    static_dir = resource_path("static")
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # --- Routers ---
    from snap_fit.webapp.routers import (
        debug,
        interactive,
        piece_ingestion,
        puzzle_solve,
    )

    api_v1 = "/api/v1"
    app.include_router(piece_ingestion.router, prefix=f"{api_v1}/pieces", tags=["Pieces"])
    app.include_router(puzzle_solve.router, prefix=f"{api_v1}/puzzle", tags=["Puzzle"])
    app.include_router(interactive.router, prefix=f"{api_v1}/interactive", tags=["Interactive"])
    app.include_router(debug.router, prefix=f"{api_v1}/debug", tags=["Debug"])

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "snap_fit.webapp.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
```

### `src/snap_fit/webapp/core/settings.py`

```python
"""Application settings via pydantic-settings (v2 API)."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True

    # CORS
    cors_allow_origins: list[str] = ["*"]

    # Paths (optional overrides)
    data_dir: str = "data"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
```

### `src/snap_fit/webapp/core/logging_config.py`

```python
"""Logging configuration for the webapp."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from snap_fit.webapp.core.settings import Settings


def configure_logging(settings: Settings) -> None:
    """Set up stdlib logging; swap for loguru if preferred."""
    level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # Quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
```

### `src/snap_fit/webapp/utils/paths.py`

```python
"""Path utilities for locating webapp resources.

Leverages the existing SnapFitPaths singleton for consistent path resolution
across the entire snap_fit codebase.
"""

from pathlib import Path

from snap_fit.params.snap_fit_params import get_snap_fit_paths


def repo_root() -> Path:
    """Return the repository root directory."""
    return get_snap_fit_paths().root_fol


def resource_path(*parts: str) -> Path:
    """Return an absolute path inside webapp_resources/."""
    return repo_root() / "webapp_resources" / Path(*parts)


def data_path(*parts: str) -> Path:
    """Return an absolute path inside data/."""
    return get_snap_fit_paths().data_fol / Path(*parts)


def static_path(*parts: str) -> Path:
    """Return an absolute path inside static/."""
    return get_snap_fit_paths().static_fol / Path(*parts)


def cache_path(*parts: str) -> Path:
    """Return an absolute path inside cache/."""
    return get_snap_fit_paths().cache_fol / Path(*parts)
```

### `src/snap_fit/webapp/routers/piece_ingestion.py`

```python
"""Router: piece ingestion and query endpoints.

Uses the existing data layer (SheetManager, PieceMatcher) for persistence.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.data_models.sheet_record import SheetRecord
from snap_fit.puzzle.sheet_manager import SheetManager
from snap_fit.webapp.utils.paths import cache_path

router = APIRouter()


@router.get("/", response_model=list[PieceRecord], summary="List all pieces")
async def list_pieces() -> list[PieceRecord]:
    """Return all piece records from cached metadata."""
    metadata_path = cache_path("metadata.json")
    if not metadata_path.exists():
        return []
    data = SheetManager.load_metadata(metadata_path)
    return [PieceRecord.model_validate(p) for p in data.get("pieces", [])]


@router.get("/sheets", response_model=list[SheetRecord], summary="List all sheets")
async def list_sheets() -> list[SheetRecord]:
    """Return all sheet records from cached metadata."""
    metadata_path = cache_path("metadata.json")
    if not metadata_path.exists():
        return []
    data = SheetManager.load_metadata(metadata_path)
    return [SheetRecord.model_validate(s) for s in data.get("sheets", [])]


@router.get("/{piece_id}", response_model=PieceRecord, summary="Get piece by ID")
async def get_piece(piece_id: str) -> PieceRecord:
    """Retrieve piece details by piece ID (format: sheet_id-piece_idx)."""
    metadata_path = cache_path("metadata.json")
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="No metadata found")

    data = SheetManager.load_metadata(metadata_path)
    for p in data.get("pieces", []):
        record = PieceRecord.model_validate(p)
        if str(record.piece_id) == piece_id:
            return record
    raise HTTPException(status_code=404, detail=f"Piece {piece_id} not found")


@router.post("/ingest", summary="Ingest sheets from directory")
async def ingest_sheets(
    sheet_dir: str,
    threshold: int = 130,
    min_area: int = 80_000,
) -> dict:
    """Load sheets from a directory, compute pieces, and persist metadata.

    Args:
        sheet_dir: Path to directory containing sheet images.
        threshold: Threshold for image preprocessing.
        min_area: Minimum contour area for piece detection.

    Returns:
        Summary of ingested data.
    """
    from snap_fit.puzzle.sheet_manager import SheetManager as SM

    sheet_path = Path(sheet_dir)
    if not sheet_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Invalid directory: {sheet_dir}")

    manager = SM()
    # Note: add_sheet() processes the image and detects pieces
    for img_file in sorted(sheet_path.glob("*.png")):
        manager.add_sheet(img_file, threshold=threshold, min_area=min_area)

    # Persist to cache
    cache_dir = cache_path()
    cache_dir.mkdir(parents=True, exist_ok=True)
    manager.save_metadata(cache_dir / "metadata.json")
    manager.save_contour_cache(cache_dir / "contours")

    records = manager.to_records()
    return {
        "sheets_ingested": len(records["sheets"]),
        "pieces_detected": len(records["pieces"]),
        "cache_path": str(cache_dir),
    }
```

### `src/snap_fit/webapp/routers/puzzle_solve.py`

```python
"""Router: puzzle solving and match query endpoints."""

from fastapi import APIRouter, HTTPException

from snap_fit.data_models.match_result import MatchResult
from snap_fit.puzzle.piece_matcher import PieceMatcher
from snap_fit.webapp.utils.paths import cache_path

router = APIRouter()


@router.get("/matches", response_model=list[MatchResult], summary="List all matches")
async def list_matches(
    limit: int = 100,
    min_similarity: float | None = None,
) -> list[MatchResult]:
    """Return match results from cached matches.

    Args:
        limit: Maximum number of matches to return (default 100).
        min_similarity: Filter to matches with similarity >= this value.
    """
    matches_path = cache_path("matches.json")
    if not matches_path.exists():
        return []

    matcher = PieceMatcher(manager=None)  # Load-only mode
    matcher.load_matches_json(matches_path)

    results = matcher._results
    if min_similarity is not None:
        results = [r for r in results if r.similarity >= min_similarity]

    # Sort by similarity ascending (best matches have lowest similarity)
    results.sort(key=lambda r: r.similarity)
    return results[:limit]


@router.get(
    "/matches/{piece_id}",
    response_model=list[MatchResult],
    summary="Get matches for piece",
)
async def get_piece_matches(piece_id: str, limit: int = 10) -> list[MatchResult]:
    """Return top matches involving a specific piece.

    Args:
        piece_id: The piece ID (format: sheet_id-piece_idx).
        limit: Maximum number of matches to return.
    """
    matches_path = cache_path("matches.json")
    if not matches_path.exists():
        raise HTTPException(status_code=404, detail="No matches found")

    matcher = PieceMatcher(manager=None)
    matcher.load_matches_json(matches_path)

    # Filter matches involving this piece
    results = [
        r for r in matcher._results
        if str(r.seg_id1.piece_id) == piece_id or str(r.seg_id2.piece_id) == piece_id
    ]
    results.sort(key=lambda r: r.similarity)
    return results[:limit]


@router.post("/solve", summary="Solve a puzzle")
async def solve_puzzle(piece_ids: list[str] | None = None) -> dict:
    """Trigger puzzle solve using the linear solver.

    Args:
        piece_ids: Optional list of piece IDs to include in solve.
            If None, uses all pieces.

    Returns:
        Solution status and layout (when implemented).
    """
    # Placeholder - will integrate with snap_fit.solver
    return {
        "success": False,
        "message": "Solver integration pending",
        "piece_count": len(piece_ids) if piece_ids else 0,
    }
```

### `src/snap_fit/webapp/routers/interactive.py`

```python
"""Router: interactive session endpoints."""

from fastapi import APIRouter

from snap_fit.webapp.schemas.interactive import SessionInfo

router = APIRouter()


@router.get("/session", response_model=SessionInfo, summary="Get session info")
async def get_session() -> SessionInfo:
    """Return current interactive session state. Placeholder."""
    return SessionInfo(session_id="placeholder", active=False)
```

### `src/snap_fit/webapp/routers/debug.py`

```python
"""Router: debug / health-check endpoints."""

from fastapi import APIRouter

from snap_fit.webapp.schemas.debug import HealthResponse

router = APIRouter()


@router.get("/ping", response_model=HealthResponse, summary="Health check")
async def ping() -> HealthResponse:
    """Simple liveness probe."""
    return HealthResponse(status="ok")


@router.get("/info", summary="Build info")
async def info() -> dict:
    """Return version and debug metadata."""
    from snap_fit.webapp.core.settings import get_settings

    settings = get_settings()
    return {"debug": settings.debug, "version": "0.1.0"}
```

### `src/snap_fit/webapp/schemas/piece.py`

```python
"""Pydantic schemas for piece endpoints.

NOTE: The primary schemas are the existing data models:
- snap_fit.data_models.sheet_record.SheetRecord
- snap_fit.data_models.piece_record.PieceRecord

This file contains any additional request/response wrappers needed
by the API that are not covered by the core data models.
"""

from pydantic import BaseModel


class IngestRequest(BaseModel):
    """Request to ingest sheets from a directory."""

    sheet_dir: str
    threshold: int = 130
    min_area: int = 80_000


class IngestResponse(BaseModel):
    """Response from sheet ingestion."""

    sheets_ingested: int
    pieces_detected: int
    cache_path: str
```

### `src/snap_fit/webapp/schemas/puzzle.py`

```python
"""Pydantic schemas for puzzle endpoints.

NOTE: Match data uses the existing data model:
- snap_fit.data_models.match_result.MatchResult

This file contains request/response schemas specific to the API.
"""

from pydantic import BaseModel


class SolveRequest(BaseModel):
    """Request to solve a puzzle."""

    piece_ids: list[str] | None = None
    config_path: str | None = None


class SolveResponse(BaseModel):
    """Response from puzzle solve."""

    success: bool
    message: str | None = None
    layout: dict | None = None
    piece_count: int = 0
```

### `src/snap_fit/webapp/schemas/interactive.py`

```python
"""Pydantic schemas for interactive session endpoints."""

from pydantic import BaseModel


class SessionInfo(BaseModel):
    """Interactive session state."""

    session_id: str
    active: bool
```

### `src/snap_fit/webapp/schemas/debug.py`

```python
"""Pydantic schemas for debug endpoints."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
```

---

## Infrastructure Files

### `.env.example`

```dotenv
# snap_fit webapp environment configuration
# Copy to .env and adjust as needed

HOST=127.0.0.1
PORT=8000
DEBUG=true

# Comma-separated origins, or * for permissive dev mode
CORS_ALLOW_ORIGINS=*

# Optional path overrides
DATA_DIR=data
```

### `Dockerfile`

```dockerfile
# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Install dependencies first (layer caching)
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy source and install project
COPY src/ src/
COPY webapp_resources/ webapp_resources/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# --- Runtime stage ---
FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/webapp_resources /app/webapp_resources

EXPOSE 8000

CMD ["uvicorn", "snap_fit.webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `docker-compose.yml`

```yaml
services:
  webapp:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      # Hot-reload in development
      - ./src:/app/src:ro
      - ./webapp_resources:/app/webapp_resources:ro
    command: >
      uvicorn snap_fit.webapp.main:app
      --host 0.0.0.0
      --port 8000
      --reload
      --reload-dir /app/src
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/debug/ping"]
      interval: 10s
      timeout: 5s
      retries: 3
```

---

## Developer Commands

```bash
# 1. Install dependencies (uv)
uv add fastapi uvicorn pydantic-settings python-multipart

# 2. Run dev server (hot reload)
uv run uvicorn snap_fit.webapp.main:app --reload

# 3. Run via Docker Compose
docker compose up --build

# 4. Quick health check
curl http://localhost:8000/api/v1/debug/ping

# 5. Open Swagger UI
open http://localhost:8000/api/docs
```

---

## Testing Strategy

```bash
# Run webapp tests only
uv run pytest tests/webapp/ -v

# With coverage
uv run pytest tests/webapp/ --cov=snap_fit.webapp --cov-report=term-missing
```

Example smoke test (`tests/webapp/test_routes.py`):

```python
"""Smoke tests for webapp routes."""

import pytest
from fastapi.testclient import TestClient

from snap_fit.webapp.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_ping(client: TestClient) -> None:
    """Health endpoint returns ok."""
    response = client.get("/api/v1/debug/ping")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_available(client: TestClient) -> None:
    """OpenAPI schema is generated."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()


def test_list_pieces_empty(client: TestClient, tmp_path: Path) -> None:
    """List pieces returns empty when no cache exists."""
    # Assuming cache_path returns tmp_path in test config
    response = client.get("/api/v1/pieces/")
    assert response.status_code == 200
    # May be empty list if no metadata cached
    assert isinstance(response.json(), list)


def test_list_sheets_empty(client: TestClient) -> None:
    """List sheets returns empty when no cache exists."""
    response = client.get("/api/v1/pieces/sheets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---

## Extending the API

1. **Add a new router:** Create `src/snap_fit/webapp/routers/my_feature.py`
2. **Add schemas:** Create `src/snap_fit/webapp/schemas/my_feature.py`
3. **Register in `main.py`:** Import and `app.include_router(...)`
4. **Add tests:** Create `tests/webapp/test_my_feature.py`

Follow the existing patterns — routers handle HTTP concerns, services wrap domain logic, schemas define contracts.

---

## Open Questions

- [ ] Should we mount Jinja2 templates for an admin UI? --> answer: yes, prepare ui to navigate cached data
- [ ] Add rate limiting middleware? --> answer: no
- [ ] WebSocket support for real-time puzzle feedback? --> answer: not yet
- [x] ~~How to persist piece/sheet metadata?~~ → JSON via `SheetManager.save_metadata()`
- [x] ~~How to handle heavy contour data?~~ → Binary `.npz` via `save_contour_cache()`
- [x] ~~How to persist match results?~~ → JSON via `PieceMatcher.save_matches_json()`
- [ ] SQLite for matches at scale (4.5M records)? --> yes
- [ ] Incremental matching when adding new sheets? --> not yet

---

## Implemented Data Layer Reference

The following persistence methods are available for API services to use:

### SheetManager Methods

```python
from snap_fit.puzzle.sheet_manager import SheetManager

manager = SheetManager()
manager.add_sheet(img_path)  # Load and process a sheet image

# Export metadata
records = manager.to_records()  # {'sheets': [...], 'pieces': [...]}

# Persist
manager.save_metadata(Path("cache/metadata.json"))
manager.save_contour_cache(Path("cache/contours/"))

# Reload (metadata only, no object reconstruction)
data = SheetManager.load_metadata(Path("cache/metadata.json"))
# data['sheets'] → list of SheetRecord dicts
# data['pieces'] → list of PieceRecord dicts

# Load contour for re-matching
contour, corners = SheetManager.load_contour_for_piece(piece_id, cache_dir)
```

### PieceMatcher Methods

```python
from snap_fit.puzzle.piece_matcher import PieceMatcher

matcher = PieceMatcher(manager)
matcher.match_all()  # Compute all segment matches

# Persist matches
matcher.save_matches_json(Path("cache/matches.json"))

# Reload matches
matcher.load_matches_json(Path("cache/matches.json"))

# Query
matched_pairs = matcher.get_matched_pair_keys()  # set of frozenset[SegmentId]

# Incremental (add new pieces without re-matching all)
new_count = matcher.match_incremental(new_piece_ids)

# Reset
matcher.clear()
```

### Data Models

```python
from snap_fit.data_models import SheetRecord, PieceRecord, MatchResult

# SheetRecord fields
record = SheetRecord(
    sheet_id="sheet_01",
    img_path=Path("data/sheets/sheet_01.png"),
    piece_count=12,
    threshold=130,
    min_area=80_000,
    created_at=datetime.now(),
)

# PieceRecord fields
piece = PieceRecord(
    piece_id=PieceId(sheet_id="sheet_01", piece_idx=0),
    corners={"TL": (10, 20), "TR": (100, 20), ...},
    segment_shapes={"TOP": "OUT", "RIGHT": "IN", ...},
    oriented_piece_type=OrientedPieceType(...),
    flat_edges=["TOP"],
    contour_point_count=512,
    contour_region=(0, 0, 150, 150),
)

# MatchResult - already Pydantic, used as-is
match = MatchResult(seg_id1=..., seg_id2=..., similarity=0.123)
match.model_dump(mode="json")  # Serialize
```

---

## Next Steps

With the data layer complete, the API scaffold can be built with real persistence:

1. **Create scaffold** — Run Phase 1 tasks to set up directory structure
2. **Wire data layer** — Import `SheetManager`, `PieceMatcher`, `SheetRecord`, `PieceRecord` in services
3. **Configure cache path** — Add `CACHE_DIR` to settings, expose via `paths.py`
4. **Implement routers** — Use provided router templates that already call the data layer
5. **Add integration tests** — Test round-trip: ingest → persist → query via API

**Estimated effort:** ~2-3 hours for scaffold + basic endpoints

---

## References

- [FastAPI docs](https://fastapi.tiangolo.com/)
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [uv package manager](https://docs.astral.sh/uv/)
