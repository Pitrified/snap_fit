"""Router: puzzle solving and match query endpoints.

Uses the data layer (PieceMatcher) via PuzzleService for match access.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from snap_fit.data_models.match_result import MatchResult
from snap_fit.webapp.core.settings import Settings
from snap_fit.webapp.core.settings import get_settings
from snap_fit.webapp.schemas.puzzle import PuzzleSolveRequest
from snap_fit.webapp.schemas.puzzle import PuzzleSolveResponse
from snap_fit.webapp.services.puzzle_service import PuzzleService

router = APIRouter()


def get_puzzle_service(settings: Settings = Depends(get_settings)) -> PuzzleService:
    """Dependency to get PuzzleService instance."""
    return PuzzleService(settings.cache_path)


@router.get("/matches", response_model=list[MatchResult], summary="List all matches")
async def list_matches(
    limit: int = 100,
    min_similarity: float | None = None,
    service: PuzzleService = Depends(get_puzzle_service),
) -> list[MatchResult]:
    """Return match results from cached matches.

    Args:
        limit: Maximum number of matches to return (default 100).
        min_similarity: Filter to matches with similarity >= this value.
    """
    return service.list_matches(limit=limit, min_similarity=min_similarity)


@router.get(
    "/matches/piece/{piece_id}",
    response_model=list[MatchResult],
    summary="Get matches for piece",
)
async def get_piece_matches(
    piece_id: str,
    limit: int = 10,
    service: PuzzleService = Depends(get_puzzle_service),
) -> list[MatchResult]:
    """Return top matches involving a specific piece.

    Args:
        piece_id: The piece ID (format: sheet_id-piece_idx).
        limit: Maximum number of matches to return.
    """
    matches = service.get_matches_for_piece(piece_id, limit=limit)
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"No matches found for piece {piece_id}",
        )
    return matches


@router.get(
    "/matches/segment/{piece_id}/{edge_pos}",
    response_model=list[MatchResult],
    summary="Get matches for segment",
)
async def get_segment_matches(
    piece_id: str,
    edge_pos: str,
    limit: int = 5,
    service: PuzzleService = Depends(get_puzzle_service),
) -> list[MatchResult]:
    """Return top matches for a specific segment.

    Args:
        piece_id: The piece ID (format: sheet_id-piece_idx).
        edge_pos: The edge position (TOP, RIGHT, BOTTOM, LEFT).
        limit: Maximum number of matches to return.
    """
    matches = service.get_matches_for_segment(piece_id, edge_pos, limit=limit)
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"No matches found for segment {piece_id}/{edge_pos}",
        )
    return matches


@router.get("/matches/count", summary="Get match count")
async def get_match_count(
    service: PuzzleService = Depends(get_puzzle_service),
) -> dict:
    """Return the total number of cached matches."""
    return {"count": service.match_count()}


@router.post("/solve", response_model=PuzzleSolveResponse, summary="Solve a puzzle")
async def solve_puzzle(
    request: PuzzleSolveRequest,
    service: PuzzleService = Depends(get_puzzle_service),
) -> PuzzleSolveResponse:
    """Trigger puzzle solve using the linear solver.

    Args:
        request: Solve parameters (piece_ids, config_path).

    Returns:
        Solution status and layout (when implemented).
    """
    result = service.solve_puzzle(
        piece_ids=request.piece_ids,
        config_path=request.config_path,
    )
    return PuzzleSolveResponse(**result)
