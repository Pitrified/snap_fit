# FastAPI Webapp — Developer Guide

This document describes how to run, develop, test and maintain the `snap_fit` FastAPI scaffold added under `src/snap_fit/webapp`.

Location

- Application package: `src/snap_fit/webapp`
- Static & templates: `webapp_resources/`
- Tests: `tests/webapp/`
- Example env: `.env.example`
- Docker assets: `Dockerfile`, `docker-compose.yml`

Quick start (development)

1. Install runtime dependencies into the project's virtual environment (uses `uv` in this repo):

```bash
uv add fastapi uvicorn pydantic-settings python-multipart httpx
```

2. Run the dev server (hot reload):

```bash
uv run uvicorn snap_fit.webapp.main:app --reload
```

3. Health-check & API docs

```bash
# Health
curl http://127.0.0.1:8000/api/v1/debug/ping

# OpenAPI JSON
open http://127.0.0.1:8000/api/openapi.json

# Swagger UI
open http://127.0.0.1:8000/api/docs
```

Run in Docker (local dev)

```bash
cp .env.example .env
docker compose up --build
```

Testing

Run the webapp smoke tests only:

```bash
uv run pytest tests/webapp/ -q
```

Linting & type-checking

```bash
uv run ruff check src/snap_fit/webapp tests/webapp
uv run pyright
```

Project layout notes

- `main.py` exports an app factory `create_app()` and top-level `app` variable for running via Uvicorn.
- `routers/` should contain HTTP-only handlers; business logic goes into `services/` or the existing domain code in `src/snap_fit/`.
- `schemas/` holds Pydantic models used for request/response validation.
- `core/settings.py` uses `pydantic-settings` to load `.env` at repo root.

Maintenance guidance

- Keep webapp dependencies minimal and pinned in `pyproject.toml`.
- Add router-level unit or integration tests under `tests/webapp/` whenever adding endpoints.
- For production deployments, add a small reverse-proxy (Nginx) and run Uvicorn behind Gunicorn or use an ASGI server with process managers.
- Use `docker` + `docker-compose` for reproducible local environments and CI jobs.

Contributing checklist (small PRs)

- Add a router file in `src/snap_fit/webapp/routers/` and corresponding Pydantic schemas.
- Add a thin service wrapper in `src/snap_fit/webapp/services/` that delegates to domain code in `src/snap_fit/`.
- Add a smoke test in `tests/webapp/` verifying route and OpenAPI availability.
- Run `uv run ruff check` and `uv run pyright` before pushing.

FAQ

- Q: Where do I put domain logic?
  - A: Keep domain logic in `src/snap_fit/` and call it from `services/` to keep HTTP layer thin and testable.

- Q: How to add templates/static assets?
  - A: Put files under `webapp_resources/templates` or `webapp_resources/static` and use `resource_path()` from `snap_fit.webapp.utils.paths`.

If you'd like, I can also commit these docs and open a PR with the scaffolding changes.
