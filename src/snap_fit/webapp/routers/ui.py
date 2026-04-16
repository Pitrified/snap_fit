"""Router: HTML UI pages for browsing cached data."""

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse

from snap_fit.config.types import EdgePos
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation_utils import get_original_edge_pos
from snap_fit.webapp.core.settings import Settings
from snap_fit.webapp.core.settings import get_settings
from snap_fit.webapp.services.interactive_service import InteractiveService
from snap_fit.webapp.services.piece_service import PieceService
from snap_fit.webapp.services.puzzle_service import PuzzleService

SettingsDep = Annotated[Settings, Depends(get_settings)]

router = APIRouter()


def get_piece_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> PieceService:
    """Dependency to get PieceService instance."""
    return PieceService(
        settings.cache_path,
        data_dir=settings.data_path,
        dataset_tag=settings.active_dataset,
    )


def get_puzzle_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> PuzzleService:
    """Dependency to get PuzzleService instance."""
    return PuzzleService(settings.cache_path, dataset_tag=settings.active_dataset)


def get_interactive_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> InteractiveService:
    """Dependency to get InteractiveService instance."""
    return InteractiveService(settings.cache_path, settings.data_path)


@router.get("/", response_class=HTMLResponse, summary="Home page")
async def home(request: Request) -> HTMLResponse:
    """Render the home page with navigation."""
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "index.html",
        {"title": "snap_fit Admin"},
    )


@router.get("/sheets", response_class=HTMLResponse, summary="Sheets list")
async def sheets_page(
    request: Request,
    service: Annotated[PieceService, Depends(get_piece_service)],
) -> HTMLResponse:
    """Render the sheets list page."""
    templates = request.app.state.templates
    sheets = service.list_sheets()
    return templates.TemplateResponse(
        request,
        "sheets.html",
        {"title": "Sheets", "sheets": sheets},
    )


@router.get("/sheets/{sheet_id}", response_class=HTMLResponse, summary="Sheet detail")
async def sheet_detail_page(
    request: Request,
    sheet_id: str,
    service: Annotated[PieceService, Depends(get_piece_service)],
) -> HTMLResponse:
    """Render a sheet detail page with its pieces."""
    templates = request.app.state.templates
    sheet = service.get_sheet(sheet_id)
    pieces = service.get_pieces_for_sheet(sheet_id) if sheet else []
    return templates.TemplateResponse(
        request,
        "sheet_detail.html",
        {
            "title": f"Sheet: {sheet_id}",
            "sheet": sheet,
            "pieces": pieces,
        },
    )


@router.get("/pieces", response_class=HTMLResponse, summary="Pieces list")
async def pieces_page(
    request: Request,
    service: Annotated[PieceService, Depends(get_piece_service)],
) -> HTMLResponse:
    """Render the pieces list page."""
    templates = request.app.state.templates
    pieces = service.list_pieces()
    return templates.TemplateResponse(
        request,
        "pieces.html",
        {"title": "Pieces", "pieces": pieces},
    )


@router.get(
    "/pieces/{piece_id}",
    response_class=HTMLResponse,
    summary="Piece detail",
)
async def piece_detail_page(
    request: Request,
    piece_id: str,
    piece_service: Annotated[PieceService, Depends(get_piece_service)],
    puzzle_service: Annotated[PuzzleService, Depends(get_puzzle_service)],
) -> HTMLResponse:
    """Render a piece detail page with its matches."""
    templates = request.app.state.templates
    piece = piece_service.get_piece(piece_id)
    matches = puzzle_service.get_matches_for_piece(piece_id, limit=20) if piece else []
    return templates.TemplateResponse(
        request,
        "piece_detail.html",
        {
            "title": f"Piece: {piece_id}",
            "piece": piece,
            "matches": matches,
        },
    )


@router.get("/matches", response_class=HTMLResponse, summary="Matches list")
async def matches_page(
    request: Request,
    limit: int = 100,
    service: Annotated[PuzzleService, Depends(get_puzzle_service)] = None,  # type: ignore[assignment]
) -> HTMLResponse:
    """Render the matches list page."""
    templates = request.app.state.templates
    matches = service.list_matches(limit=limit)
    total_count = service.match_count()
    return templates.TemplateResponse(
        request,
        "matches.html",
        {
            "title": "Matches",
            "matches": matches,
            "total_count": total_count,
            "limit": limit,
        },
    )


@router.get("/settings", response_class=HTMLResponse, summary="Settings page")
async def settings_page(
    request: Request,
    settings: SettingsDep,
) -> HTMLResponse:
    """Render the settings page for dataset selection."""
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "title": "Settings",
            "available_datasets": settings.available_datasets(),
            "active_dataset": settings.active_dataset,
        },
    )


# ------------------------------------------------------------------
# Solver pages
# ------------------------------------------------------------------


@router.get("/solver", response_class=HTMLResponse, summary="Solver home")
async def solver_home(
    request: Request,
    settings: SettingsDep,
    service: Annotated[InteractiveService, Depends(get_interactive_service)],
) -> HTMLResponse:
    """Render the solver session list and create form."""
    templates = request.app.state.templates
    tag = settings.active_dataset
    sessions = service.list_sessions(tag) if tag else []
    return templates.TemplateResponse(
        request,
        "solver_home.html",
        {
            "title": "Solver",
            "datasets": settings.available_datasets(),
            "sessions": sessions,
            "current_tag": tag,
        },
    )


@router.get(
    "/solver/{session_id}",
    response_class=HTMLResponse,
    summary="Interactive solver view",
)
async def solver_page(
    request: Request,
    session_id: str,
    settings: SettingsDep,
    interactive_service: Annotated[
        InteractiveService, Depends(get_interactive_service)
    ],
    piece_service: Annotated[PieceService, Depends(get_piece_service)],
) -> HTMLResponse:
    """Render the interactive solver view for a session."""
    templates = request.app.state.templates
    tag = settings.active_dataset
    if tag is None:
        return templates.TemplateResponse(
            request,
            "solver_home.html",
            {
                "title": "Solver",
                "datasets": settings.available_datasets(),
                "sessions": [],
                "current_tag": None,
                "error": "Select a dataset first.",
            },
        )
    session = interactive_service.get_session(tag, session_id)
    if session is None:
        return templates.TemplateResponse(
            request,
            "solver_home.html",
            {
                "title": "Solver",
                "datasets": settings.available_datasets(),
                "sessions": interactive_service.list_sessions(tag),
                "current_tag": tag,
                "error": f"Session {session_id} not found.",
            },
        )
    all_pieces = piece_service.list_pieces()
    placed_ids = {pid for pid, _orient in session.placement.values()}
    unplaced = [p for p in all_pieces if str(p.piece_id) not in placed_ids]
    return templates.TemplateResponse(
        request,
        "solver.html",
        {
            "title": f"Solver: {session_id[:8]}",
            "session": session,
            "unplaced": unplaced,
        },
    )


# ------------------------------------------------------------------
# Debug pages
# ------------------------------------------------------------------

_ORIENTATION_DEGREES = [0, 90, 180, 270]


@router.get(
    "/debug/orientations",
    response_class=HTMLResponse,
    summary="Orientation debug page",
)
async def orientation_debug_page(
    request: Request,
    piece_id: str | None = None,
    service: Annotated[PieceService, Depends(get_piece_service)] = None,  # type: ignore[assignment]
) -> HTMLResponse:
    """Show pieces in all 4 orientations for visual verification."""
    templates = request.app.state.templates
    if piece_id:
        piece = service.get_piece(piece_id)
        pieces = [piece] if piece else []
    else:
        pieces = service.list_pieces()[:12]

    # Pre-compute {deg: {rotated_edge_value: original_edge_value}} server-side
    # so templates don't need to call Python functions.
    edge_map: dict[int, dict[str, str]] = {
        deg: {
            edge.value: get_original_edge_pos(edge, Orientation(deg)).value
            for edge in EdgePos
        }
        for deg in _ORIENTATION_DEGREES
    }

    return templates.TemplateResponse(
        request,
        "debug_orientations.html",
        {
            "title": "Orientation Debug",
            "pieces": pieces,
            "edge_map": edge_map,
            "orientations": _ORIENTATION_DEGREES,
        },
    )
