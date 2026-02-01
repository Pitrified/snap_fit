# FastAPI Webapp — Developer Guide

This document describes how to run, develop, test and maintain the `snap_fit` FastAPI application under `src/snap_fit/webapp`.

## Overview

The webapp provides:
- **REST API** for querying pieces, sheets, and match results
- **Admin UI** (HTML) for browsing cached puzzle data
- **Data Layer Integration** with `SheetManager` and `PieceMatcher` persistence

## Location

- Application package: `src/snap_fit/webapp/`
- Static & templates: `webapp_resources/`
- Tests: `tests/webapp/`
- Example env: `.env.example`
- Docker assets: `Dockerfile`, `docker-compose.yml`

## Quick Start (Development)

1. Install runtime dependencies:

```bash
uv add fastapi uvicorn pydantic-settings python-multipart httpx jinja2
```

2. Run the dev server (hot reload):

```bash
uv run uvicorn snap_fit.webapp.main:app --reload
```

3. Open in browser:

```bash
# Admin UI
open http://127.0.0.1:8000/

# Swagger UI (API docs)
open http://127.0.0.1:8000/api/docs

# Health check
curl http://127.0.0.1:8000/api/v1/debug/ping
```

## API Endpoints

### Pieces

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/pieces/` | List all pieces |
| `GET` | `/api/v1/pieces/sheets` | List all sheets |
| `GET` | `/api/v1/pieces/sheets/{sheet_id}` | Get sheet by ID |
| `GET` | `/api/v1/pieces/sheets/{sheet_id}/pieces` | List pieces for sheet |
| `GET` | `/api/v1/pieces/{piece_id}` | Get piece by ID |
| `POST` | `/api/v1/pieces/ingest` | Ingest sheets from directory |

### Puzzle / Matches

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/puzzle/matches` | List all matches |
| `GET` | `/api/v1/puzzle/matches/count` | Get total match count |
| `GET` | `/api/v1/puzzle/matches/piece/{piece_id}` | Get matches for piece |
| `GET` | `/api/v1/puzzle/matches/segment/{piece_id}/{edge}` | Get matches for segment |
| `POST` | `/api/v1/puzzle/solve` | Solve puzzle (WIP) |

### Debug

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/debug/ping` | Health check |
| `GET` | `/api/v1/debug/info` | Build info |

## Admin UI Pages

| URL | Description |
|-----|-------------|
| `/` | Home dashboard with counts |
| `/sheets` | List all sheets |
| `/sheets/{id}` | Sheet detail with pieces |
| `/pieces` | List all pieces |
| `/pieces/{id}` | Piece detail with matches |
| `/matches` | List match results |

## Data Layer Integration

The webapp uses the persistence layer from `snap_fit`:

```python
# Services use SheetManager and PieceMatcher
from snap_fit.webapp.services.piece_service import PieceService
from snap_fit.webapp.services.puzzle_service import PuzzleService

# Data models for API responses
from snap_fit.data_models import SheetRecord, PieceRecord, MatchResult
```

### Cache Directory

Configure via environment variable:

```bash
export CACHE_DIR=/path/to/cache
```

Or in `.env`:

```
CACHE_DIR=cache
```

The service looks for:
- `{CACHE_DIR}/metadata.json` — Sheet and piece metadata
- `{CACHE_DIR}/matches.json` — Match results
- `{CACHE_DIR}/contours/` — Binary contour cache

## Run in Docker

```bash
cp .env.example .env
docker compose up --build
```

## Testing

Run webapp tests:

```bash
uv run pytest tests/webapp/ -v
```

Run all tests:

```bash
uv run pytest
```

## Linting & Type-Checking

```bash
uv run ruff check src/snap_fit/webapp tests/webapp
uv run pyright
```

## Project Layout

```
src/snap_fit/webapp/
├── __init__.py
├── main.py              # App factory, middleware, router mounts
├── core/
│   ├── settings.py      # pydantic-settings config
│   └── logging_config.py
├── routers/
│   ├── piece_ingestion.py  # /api/v1/pieces endpoints
│   ├── puzzle_solve.py     # /api/v1/puzzle endpoints
│   ├── interactive.py      # /api/v1/interactive endpoints
│   ├── debug.py            # /api/v1/debug endpoints
│   └── ui.py               # HTML UI pages
├── schemas/
│   ├── piece.py         # IngestRequest, IngestResponse
│   ├── puzzle.py        # SolveRequest, SolveResponse
│   ├── interactive.py   # SessionInfo
│   └── debug.py         # HealthResponse
├── services/
│   ├── piece_service.py   # Wraps SheetManager
│   └── puzzle_service.py  # Wraps PieceMatcher
└── utils/
    └── paths.py         # Resource path resolution
```

## Adding New Features

1. **Add router** in `src/snap_fit/webapp/routers/my_feature.py`
2. **Add schemas** in `src/snap_fit/webapp/schemas/my_feature.py`
3. **Add service** in `src/snap_fit/webapp/services/my_service.py` (if needed)
4. **Register in `main.py`**: Import and `app.include_router(...)`
5. **Add tests** in `tests/webapp/test_my_feature.py`

## FAQ

**Q: Where do I put domain logic?**
A: Keep domain logic in `src/snap_fit/` and call it from `services/` to keep the HTTP layer thin.

**Q: How to add templates/static assets?**
A: Put files under `webapp_resources/templates` or `webapp_resources/static`.

**Q: How to ingest sheets via API?**
A: POST to `/api/v1/pieces/ingest` with JSON body:
```json
{
  "sheet_dir": "/path/to/sheets",
  "threshold": 130,
  "min_area": 80000
}
```

