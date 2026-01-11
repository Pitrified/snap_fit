## Overview

We will add a clean, scalable FastAPI application to the repository following best practices. Below are three candidate approaches — pick one and I will scaffold the code and files accordingly.

**Option A — Minimal, Opinionated Starter (recommended for quick iteration)**

- Description: Single FastAPI app under `src/snap_fit/webapp/` with modular routers, basic settings, CORS, logging, and Docker support.
- Pros: Fast to implement, easy to extend, good developer DX (Swagger, hot reload).
- Cons: Less separation for very large deployments; production tuning must be added later.

**Option B — Modular Sub-apps & Dependency Injection (recommended for long-term scalability)**

- Description: Use FastAPI sub-applications and dependency-injection-friendly services. Clear separation between `api/` (versioned routers), `services/`, and `core/` (settings, logging). `webapp_resources/` at repo root serves templates/static.
- Pros: Better for large codebases and teams; easier to extract microservices.
- Cons: Slightly more boilerplate to start.

**Option C — Container-First, Production-Ready Layout**

- Description: Similar to Option B but with opinionated production configuration (Gunicorn/uvicorn workers, more robust Dockerfile, and example Nginx reverse proxy in compose).
- Pros: Production-ready defaults, useful when deploying immediately.
- Cons: More initial complexity; overkill for prototyping.

Please reply with your chosen option (A, B, or C) or propose modifications. After you choose, I'll populate the **Plan** below with small actionable steps and start scaffolding files.

## Plan — Chosen: Option A (Minimal starter with helpful bells)

I will scaffold a minimal but well-structured FastAPI application under `src/snap_fit/webapp/` with modular routers and helpful conveniences (settings, logging, CORS, API prefix, Docker examples, and docs). Below is a sequential, actionable plan and the exact file tree and starter code snippets you can apply directly.

High-level steps

1. Create branch: `git checkout -b feat/fastapi-scaffold`
2. Create layout under `src/snap_fit/webapp/` and top-level `webapp_resources/`.
3. Add starter files (routers, schemas, core settings/logging, services, main entrypoint).
4. Add `Dockerfile`, `docker-compose.yml`, and `.env.example` in repo root (or feature folder).
5. Add `docs/fastapi.md` describing install/run/test instructions.
6. Add minimal tests and typing stubs in `tests/webapp/`.

File tree to create (exact paths)

```
webapp_resources/
	templates/
		index.html
	static/
		css/
			style.css

src/snap_fit/webapp/
	__init__.py
	main.py
	core/
		__init__.py
		settings.py
		logging_config.py
	api/
		__init__.py
	routers/
		__init__.py
		piece_ingestion.py
		puzzle_solve.py
		interactive.py
		debug.py
	schemas/
		__init__.py
		piece.py
		puzzle.py
		interactive.py
		debug.py
	services/
		__init__.py
		piece_service.py
		puzzle_service.py
	utils/
		__init__.py
		paths.py

.env.example
Dockerfile
docker-compose.yml
docs/fastapi.md
tests/webapp/test_routes.py
```

Starter code snippets (apply these into the files above)

- `src/snap_fit/webapp/__init__.py`:

```
# Package marker for webapp
__all__ = ["main"]
```

- `src/snap_fit/webapp/main.py`:

```
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from snap_fit.webapp.core.settings import Settings
from snap_fit.webapp.core.logging_config import configure_logging

settings = Settings()
configure_logging(settings)

def create_app() -> FastAPI:
		app = FastAPI(title="snap_fit API", version="0.1.0")

		# CORS
		app.add_middleware(
				CORSMiddleware,
				allow_origins=settings.cors_allow_origins,
				allow_credentials=True,
				allow_methods=["*"],
				allow_headers=["*"],
		)

		# Mount routers under API version prefix
		from snap_fit.webapp.routers import (
				piece_ingestion,
				puzzle_solve,
				interactive,
				debug,
		)

		api_prefix = "/api/v1"
		app.include_router(piece_ingestion.router, prefix=f"{api_prefix}/pieces", tags=["pieces"])
		app.include_router(puzzle_solve.router, prefix=f"{api_prefix}/puzzle", tags=["puzzle"])
		app.include_router(interactive.router, prefix=f"{api_prefix}/interactive", tags=["interactive"])
		app.include_router(debug.router, prefix=f"{api_prefix}/debug", tags=["debug"])

		return app


app = create_app()

if __name__ == "__main__":
		import uvicorn

		uvicorn.run("snap_fit.webapp.main:app", host=settings.host, port=settings.port, reload=True)
```

- `src/snap_fit/webapp/core/settings.py`:

```
from pydantic import BaseSettings
from typing import List


class Settings(BaseSettings):
		host: str = "127.0.0.1"
		port: int = 8000
		debug: bool = True
		cors_allow_origins: List[str] = ["*"]

		class Config:
				env_file = ".env"


__all__ = ["Settings"]
```

- `src/snap_fit/webapp/core/logging_config.py`:

```
import logging
from logging.config import dictConfig

from snap_fit.webapp.core.settings import Settings


def configure_logging(settings: Settings) -> None:
		# Minimal logging configuration — replace with dictConfig for complex setups
		level = logging.DEBUG if settings.debug else logging.INFO
		logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


__all__ = ["configure_logging"]
```

- `src/snap_fit/webapp/routers/piece_ingestion.py` (starter router):

```
from fastapi import APIRouter
from snap_fit.webapp.schemas.piece import PieceIn, PieceOut

router = APIRouter()


@router.post("/", response_model=PieceOut)
async def ingest_piece(payload: PieceIn):
		"""Placeholder: accept a piece payload and return basic response."""
		return {"id": "placeholder", **payload.dict()}
```

- `src/snap_fit/webapp/routers/puzzle_solve.py`:

```
from fastapi import APIRouter

router = APIRouter()


@router.post("/solve")
async def solve_puzzle():
		"""Placeholder puzzle solve endpoint."""
		return {"status": "ok", "solution": None}
```

- `src/snap_fit/webapp/routers/interactive.py`:

```
from fastapi import APIRouter

router = APIRouter()


@router.get("/session")
async def get_session():
		return {"session": "placeholder"}
```

- `src/snap_fit/webapp/routers/debug.py`:

```
from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def ping():
		return {"pong": True}
```

- `src/snap_fit/webapp/schemas/piece.py`:

```
from pydantic import BaseModel
from typing import Optional


class PieceIn(BaseModel):
		name: str
		image_path: Optional[str]


class PieceOut(PieceIn):
		id: str
```

- `src/snap_fit/webapp/schemas/puzzle.py`:

```
from pydantic import BaseModel


class PuzzleRequest(BaseModel):
		pieces: list[str]


class PuzzleSolution(BaseModel):
		success: bool
		layout: dict | None = None
```

- `src/snap_fit/webapp/utils/paths.py` (helpful path helpers):

```
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def resource_path(*parts: str) -> Path:
		return ROOT.joinpath("webapp_resources", *parts)
```

- `.env.example`:

```
# Example environment variables for the FastAPI app
HOST=127.0.0.1
PORT=8000
DEBUG=true
# CORS origins comma separated
CORS_ALLOW_ORIGINS=*
```

- `Dockerfile` (example):

```
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml poetry.lock* /app/
# If using uv as package manager, install uv first or use pip
RUN pip install --no-cache-dir uvicorn fastapi python-dotenv
COPY . /app
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "snap_fit.webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- `docker-compose.yml` (example):

```
version: '3.8'
services:
	web:
		build: .
		ports:
			- 8000:8000
		env_file:
			- .env
		volumes:
			- .:/app:rw
		command: uvicorn snap_fit.webapp.main:app --host 0.0.0.0 --port 8000 --reload
```

Docs and developer commands

- Install runtime deps (using `uv` package manager in this repo):

```
# Example (adjust to your uv usage):
uv add fastapi uvicorn python-dotenv pydantic
```

- Run dev server (from repo root):

```
# ensure src on python path
PYTHONPATH=src uvicorn snap_fit.webapp.main:app --reload --app-dir src
```

- Run in Docker:

```
docker build -t snap_fit_webapp .
docker run --env-file .env -p 8000:8000 snap_fit_webapp
```

Testing and tips

- Swagger UI available at `http://localhost:8000/docs` when server is running.
- Quick health check: `curl http://localhost:8000/api/v1/debug/ping`
- Add new routers under `src/snap_fit/webapp/routers/` and include them in `main.py` with the `/api/v1` prefix.

Next actions I will perform after you confirm this plan:

- Create actual files and commit them on branch `feat/fastapi-scaffold`.
- Add basic tests under `tests/webapp/` and wire up CI if requested.

---

Feature branch suggestion: `feat/fastapi-scaffold`.
