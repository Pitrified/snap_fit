"""Router: HTML UI pages for browsing cached data."""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse

from snap_fit.webapp.core.settings import Settings
from snap_fit.webapp.core.settings import get_settings
from snap_fit.webapp.services.piece_service import PieceService
from snap_fit.webapp.services.puzzle_service import PuzzleService

router = APIRouter()


def get_piece_service(settings: Settings = Depends(get_settings)) -> PieceService:
    """Dependency to get PieceService instance."""
    return PieceService(settings.cache_path)


def get_puzzle_service(settings: Settings = Depends(get_settings)) -> PuzzleService:
    """Dependency to get PuzzleService instance."""
    return PuzzleService(settings.cache_path)


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
    service: PieceService = Depends(get_piece_service),
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
    service: PieceService = Depends(get_piece_service),
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
    service: PieceService = Depends(get_piece_service),
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
    piece_service: PieceService = Depends(get_piece_service),
    puzzle_service: PuzzleService = Depends(get_puzzle_service),
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
    service: PuzzleService = Depends(get_puzzle_service),
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
