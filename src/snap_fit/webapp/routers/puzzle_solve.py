"""Router: puzzle solving endpoints."""

from fastapi import APIRouter

from snap_fit.webapp.schemas.puzzle import PuzzleSolveRequest
from snap_fit.webapp.schemas.puzzle import PuzzleSolveResponse

router = APIRouter()


@router.post("/solve", summary="Solve a puzzle")
async def solve_puzzle(_request: PuzzleSolveRequest) -> PuzzleSolveResponse:
    """Trigger puzzle solve and return status."""
    return PuzzleSolveResponse(success=False, message="Not implemented")
