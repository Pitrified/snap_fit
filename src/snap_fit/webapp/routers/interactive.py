"""Router: interactive session endpoints."""

from fastapi import APIRouter

from snap_fit.webapp.schemas.interactive import SessionInfo

router = APIRouter()


@router.get("/session", summary="Get session info")
async def get_session() -> SessionInfo:
    """Return current interactive session state."""
    return SessionInfo(session_id="placeholder", active=False)
