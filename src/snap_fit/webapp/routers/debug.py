"""Router: debug / health-check endpoints."""

from fastapi import APIRouter

from snap_fit.webapp.core.settings import get_settings
from snap_fit.webapp.schemas.debug import HealthResponse

router = APIRouter()


@router.get("/ping", summary="Health check")
async def ping() -> HealthResponse:
    """Return liveness status."""
    return HealthResponse(status="ok")


@router.get("/info", summary="Build info")
async def info() -> dict:
    """Return version and debug metadata."""
    settings = get_settings()
    return {"debug": settings.debug, "version": "0.1.0"}
