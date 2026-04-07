# `webapp`

> Module: `src/snap_fit/webapp/`
> Related tests: `tests/webapp/`

## Purpose

FastAPI web application providing REST API endpoints and an HTML UI for puzzle piece ingestion, match browsing, and puzzle solving. Built with the app factory pattern via `create_app()`.

## Architecture

```
webapp/
  main.py           # create_app() factory, module-level `app` instance
  core/
    settings.py     # Settings via pydantic-settings (.env support)
    logging_config.py
  routers/
    piece_ingestion.py  # /api/v1/pieces - CRUD for sheets and pieces
    puzzle_solve.py     # /api/v1/puzzle - match queries and solve endpoint
    interactive.py      # /api/v1/interactive - interactive features
    debug.py            # /api/v1/debug - debug endpoints
    ui.py               # / - HTML pages (Jinja2 templates)
  services/
    piece_service.py    # Business logic for piece/sheet operations
    puzzle_service.py   # Business logic for matches and solving
  schemas/              # Request/response Pydantic models
  utils/
    paths.py            # Resource path resolution
```

## Usage

### Running the server

```bash
uv run uvicorn snap_fit.webapp.main:app --reload
```

### API endpoints

**Pieces** (`/api/v1/pieces`):

- `GET /` - list all pieces
- `GET /sheets` - list all sheets
- `GET /sheets/{sheet_id}` - sheet detail
- `GET /sheets/{sheet_id}/pieces` - pieces for a sheet
- `GET /{piece_id}` - piece detail
- `POST /ingest` - ingest a dataset by tag

**Puzzle** (`/api/v1/puzzle`):

- `GET /matches` - list matches (with limit and min_similarity filters)
- `GET /matches/piece/{piece_id}` - matches for a piece
- `GET /matches/segment/{piece_id}/{edge_pos}` - matches for a segment
- `GET /matches/count` - total match count
- `POST /solve` - solve puzzle (stub)

**UI** (`/`):

- `GET /` - home page
- `GET /sheets`, `/sheets/{id}` - sheet views
- `GET /pieces`, `/pieces/{id}` - piece views with top matches
- `GET /matches` - match browser

### Settings

Environment-driven via `pydantic-settings`. Key fields:

| Setting | Default | Description |
|---------|---------|-------------|
| `host` | `127.0.0.1` | Server host |
| `port` | `8000` | Server port |
| `debug` | `True` | Enable reload |
| `cors_allow_origins` | `["*"]` | CORS origins |
| `data_dir` | `"data"` | Data directory path |
| `cache_dir` | `"cache"` | Cache directory path |

## Service Layer

### `PieceService`

Aggregates sheet and piece data across all cached datasets. Each dataset lives under `cache/{tag}/` with its own `dataset.db`. Key method: `ingest_sheets(tag, data_dir)` loads images via `SheetAruco`, detects pieces, and persists to SQLite + JSON + contour cache.

### `PuzzleService`

Aggregates match results across datasets. Provides filtered queries by piece, segment, or similarity threshold. The `solve_puzzle()` method is currently a stub.

## Common Pitfalls

- **Settings .env location**: The `.env` file should be at `~/cred/snap_fit/.env`, not in the project root.
- **Static files**: Templates and static files are resolved from `webapp_resources/` via `utils/paths.py`.
- **CORS**: Default allows all origins (`*`). Restrict in production.

## Related Modules

- [`puzzle/sheet_manager`](../puzzle/sheet_manager.md) - used by PieceService for ingestion
- [`puzzle/sheet_aruco`](../puzzle/sheet_aruco.md) - ArUco-based sheet loading during ingestion
- [`persistence`](../persistence/index.md) - `DatasetStore` for all database operations
- [`params`](../params/index.md) - alternative path resolution via `SnapFitPaths`
