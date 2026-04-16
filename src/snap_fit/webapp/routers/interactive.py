"""Router: interactive session endpoints."""

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from snap_fit.webapp.core.settings import Settings
from snap_fit.webapp.core.settings import get_settings
from snap_fit.webapp.schemas.interactive import CreateSessionRequest
from snap_fit.webapp.schemas.interactive import PlaceRequest
from snap_fit.webapp.schemas.interactive import SolveSessionResponse
from snap_fit.webapp.schemas.interactive import SuggestionBundle
from snap_fit.webapp.schemas.interactive import SuggestionRequest
from snap_fit.webapp.services.interactive_service import InteractiveService

router = APIRouter()


def _get_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> InteractiveService:
    return InteractiveService(settings.cache_path, settings.data_path)


def _require_tag(
    settings: Annotated[Settings, Depends(get_settings)],
    dataset_tag: str | None = None,
) -> str:
    """Resolve the dataset tag from the query param or active setting."""
    tag = dataset_tag or settings.active_dataset
    if tag is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "dataset_tag query parameter is required (or set an active dataset)."
            ),
        )
    return tag


# ------------------------------------------------------------------
# Session CRUD
# ------------------------------------------------------------------


@router.post("/sessions", summary="Create solve session")
async def create_session(
    req: CreateSessionRequest,
    service: Annotated[InteractiveService, Depends(_get_service)],
) -> SolveSessionResponse:
    """Create a new interactive solve session."""
    try:
        return service.create_session(req.dataset_tag, req.grid_rows, req.grid_cols)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/sessions", summary="List sessions for dataset")
async def list_sessions(
    service: Annotated[InteractiveService, Depends(_get_service)],
    tag: Annotated[str, Depends(_require_tag)],
) -> list[SolveSessionResponse]:
    """Return all sessions for the given dataset."""
    return service.list_sessions(tag)


@router.get("/sessions/{session_id}", summary="Get session state")
async def get_session(
    session_id: str,
    service: Annotated[InteractiveService, Depends(_get_service)],
    tag: Annotated[str, Depends(_require_tag)],
) -> SolveSessionResponse:
    """Return the current state of a solve session."""
    result = service.get_session(tag, session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.post("/sessions/{session_id}/place", summary="Place a piece")
async def place_piece(
    session_id: str,
    req: PlaceRequest,
    service: Annotated[InteractiveService, Depends(_get_service)],
    tag: Annotated[str, Depends(_require_tag)],
) -> SolveSessionResponse:
    """Place a piece on the grid."""
    try:
        return service.place_piece(
            tag,
            session_id,
            req.piece_id,
            req.position,
            req.orientation,
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/undo", summary="Undo last placement")
async def undo(
    session_id: str,
    service: Annotated[InteractiveService, Depends(_get_service)],
    tag: Annotated[str, Depends(_require_tag)],
) -> SolveSessionResponse:
    """Remove the last placed piece."""
    try:
        return service.undo(tag, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/sessions/{session_id}", summary="Delete session")
async def delete_session(
    session_id: str,
    service: Annotated[InteractiveService, Depends(_get_service)],
    tag: Annotated[str, Depends(_require_tag)],
) -> dict[str, bool]:
    """Delete a solve session."""
    deleted = service.delete_session(tag, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}


# ------------------------------------------------------------------
# Suggestion engine
# ------------------------------------------------------------------


@router.post("/sessions/{session_id}/next_suggestion", summary="Get next suggestion")
async def next_suggestion(
    session_id: str,
    req: SuggestionRequest,
    service: Annotated[InteractiveService, Depends(_get_service)],
    tag: Annotated[str, Depends(_require_tag)],
) -> SuggestionBundle:
    """Generate ranked candidates for the next open slot."""
    try:
        return service.suggest_next(
            tag,
            session_id,
            override_pos=req.override_pos,
            top_k=req.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/accept", summary="Accept suggestion")
async def accept_suggestion(
    session_id: str,
    service: Annotated[InteractiveService, Depends(_get_service)],
    tag: Annotated[str, Depends(_require_tag)],
) -> SolveSessionResponse:
    """Accept the current pending suggestion candidate and place the piece."""
    try:
        return service.accept(tag, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/reject", summary="Reject suggestion")
async def reject_suggestion(
    session_id: str,
    service: Annotated[InteractiveService, Depends(_get_service)],
    tag: Annotated[str, Depends(_require_tag)],
) -> SuggestionBundle:
    """Reject the current pending candidate and advance to the next."""
    try:
        return service.reject(tag, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
