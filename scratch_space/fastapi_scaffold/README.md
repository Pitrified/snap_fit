# FastAPI Scaffold — Feature Plan

> **Status:** ✅ Approach selected (Option A)  
> **Branch:** `feat/fastapi-scaffold`  
> **Author:** dev_plan_agent  
> **Last updated:** 2026-01-12

---

## Overview

Add a production-ready FastAPI application to the `snap_fit` repository. The web layer will expose puzzle-solving capabilities via a REST API while maintaining clean separation from the existing domain logic in `src/snap_fit/`.

### Evaluated Approaches

| Option | Summary | Trade-offs |
|--------|---------|------------|
| **A — Minimal Starter** | Single app, modular routers, settings via `pydantic-settings`, CORS, Docker | Fast to ship; extend later for scale |
| **B — Sub-apps + DI** | Versioned sub-applications, full dependency injection | Better isolation; more boilerplate |
| **C — Container-First** | Gunicorn workers, Nginx reverse proxy, health probes | Production-hardened; overkill for MVP |

**Decision:** Proceed with **Option A** — minimal starter with quality-of-life conveniences (hot reload, Swagger UI, typed settings, path utilities).

---

## Implementation Plan

### Phase 1 — Scaffold Structure

| # | Task | Artifact |
|---|------|----------|
| 1 | Create feature branch | `git checkout -b feat/fastapi-scaffold` |
| 2 | Scaffold `src/snap_fit/webapp/` package | Directory tree below |
| 3 | Add `webapp_resources/` at repo root | Templates + static assets |
| 4 | Wire up `main.py` entrypoint | App factory, middleware, router mounts |

### Phase 2 — Configuration & Infra

| # | Task | Artifact |
|---|------|----------|
| 5 | Add `.env.example` | Environment variable template |
| 6 | Add `Dockerfile` (uv-based) | Multi-stage build |
| 7 | Add `docker-compose.yml` | Local dev orchestration |

### Phase 3 — Docs & Tests

| # | Task | Artifact |
|---|------|----------|
| 8 | Create `docs/fastapi.md` | Install, run, extend guide |
| 9 | Add `tests/webapp/` | Smoke tests for each router |

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
"""Router: piece ingestion endpoints."""

from fastapi import APIRouter

from snap_fit.webapp.schemas.piece import PieceIn, PieceOut

router = APIRouter()


@router.post("/", response_model=PieceOut, summary="Ingest a puzzle piece")
async def ingest_piece(payload: PieceIn) -> PieceOut:
    """Accept piece metadata; return created resource. Business logic TBD."""
    return PieceOut(id="placeholder", **payload.model_dump())


@router.get("/{piece_id}", response_model=PieceOut, summary="Get piece by ID")
async def get_piece(piece_id: str) -> PieceOut:
    """Retrieve piece details. Placeholder implementation."""
    return PieceOut(id=piece_id, name="unknown", image_path=None)
```

### `src/snap_fit/webapp/routers/puzzle_solve.py`

```python
"""Router: puzzle solving endpoints."""

from fastapi import APIRouter

from snap_fit.webapp.schemas.puzzle import PuzzleSolveRequest, PuzzleSolveResponse

router = APIRouter()


@router.post("/solve", response_model=PuzzleSolveResponse, summary="Solve a puzzle")
async def solve_puzzle(request: PuzzleSolveRequest) -> PuzzleSolveResponse:
    """Trigger puzzle solve. Returns solution or status. Business logic TBD."""
    return PuzzleSolveResponse(success=False, message="Not implemented")
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
"""Pydantic schemas for piece endpoints."""

from pydantic import BaseModel


class PieceIn(BaseModel):
    """Input schema for piece ingestion."""

    name: str
    image_path: str | None = None


class PieceOut(BaseModel):
    """Output schema for piece resources."""

    id: str
    name: str
    image_path: str | None = None
```

### `src/snap_fit/webapp/schemas/puzzle.py`

```python
"""Pydantic schemas for puzzle endpoints."""

from pydantic import BaseModel


class PuzzleSolveRequest(BaseModel):
    """Request to solve a puzzle."""

    piece_ids: list[str]
    config_path: str | None = None


class PuzzleSolveResponse(BaseModel):
    """Response from puzzle solve."""

    success: bool
    message: str | None = None
    layout: dict | None = None
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

- [ ] Should we mount Jinja2 templates for an admin UI?
- [ ] Add rate limiting middleware?
- [ ] WebSocket support for real-time puzzle feedback?

---

## References

- [FastAPI docs](https://fastapi.tiangolo.com/)
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [uv package manager](https://docs.astral.sh/uv/)
