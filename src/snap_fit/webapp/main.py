"""FastAPI application factory and entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from snap_fit.webapp.core.logging_config import configure_logging
from snap_fit.webapp.core.settings import get_settings
from snap_fit.webapp.routers import debug
from snap_fit.webapp.routers import interactive
from snap_fit.webapp.routers import piece_ingestion
from snap_fit.webapp.routers import puzzle_solve
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
    api_v1 = "/api/v1"
    app.include_router(
        piece_ingestion.router, prefix=f"{api_v1}/pieces", tags=["Pieces"]
    )
    app.include_router(puzzle_solve.router, prefix=f"{api_v1}/puzzle", tags=["Puzzle"])
    app.include_router(
        interactive.router, prefix=f"{api_v1}/interactive", tags=["Interactive"]
    )
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
