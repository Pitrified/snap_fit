"""Router: piece ingestion and query endpoints.

Uses the data layer (SheetManager) via PieceService for persistence.
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.data_models.sheet_record import SheetRecord
from snap_fit.webapp.core.settings import Settings
from snap_fit.webapp.core.settings import get_settings
from snap_fit.webapp.schemas.piece import IngestRequest
from snap_fit.webapp.schemas.piece import IngestResponse
from snap_fit.webapp.services.piece_service import PieceService

router = APIRouter()


def get_piece_service(settings: Settings = Depends(get_settings)) -> PieceService:
    """Dependency to get PieceService instance."""
    return PieceService(settings.cache_path)


@router.get("/", response_model=list[PieceRecord], summary="List all pieces")
async def list_pieces(
    service: PieceService = Depends(get_piece_service),
) -> list[PieceRecord]:
    """Return all piece records from cached metadata."""
    return service.list_pieces()


@router.get("/sheets", response_model=list[SheetRecord], summary="List all sheets")
async def list_sheets(
    service: PieceService = Depends(get_piece_service),
) -> list[SheetRecord]:
    """Return all sheet records from cached metadata."""
    return service.list_sheets()


@router.get(
    "/sheets/{sheet_id}",
    response_model=SheetRecord,
    summary="Get sheet by ID",
)
async def get_sheet(
    sheet_id: str,
    service: PieceService = Depends(get_piece_service),
) -> SheetRecord:
    """Retrieve sheet details by sheet ID."""
    record = service.get_sheet(sheet_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Sheet {sheet_id} not found")
    return record


@router.get(
    "/sheets/{sheet_id}/pieces",
    response_model=list[PieceRecord],
    summary="List pieces for sheet",
)
async def list_pieces_for_sheet(
    sheet_id: str,
    service: PieceService = Depends(get_piece_service),
) -> list[PieceRecord]:
    """Return all pieces belonging to a specific sheet."""
    return service.get_pieces_for_sheet(sheet_id)


@router.get("/{piece_id}", response_model=PieceRecord, summary="Get piece by ID")
async def get_piece(
    piece_id: str,
    service: PieceService = Depends(get_piece_service),
) -> PieceRecord:
    """Retrieve piece details by piece ID (format: sheet_id-piece_idx)."""
    record = service.get_piece(piece_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Piece {piece_id} not found")
    return record


@router.post("/ingest", response_model=IngestResponse, summary="Ingest sheets")
async def ingest_sheets(
    request: IngestRequest,
    service: PieceService = Depends(get_piece_service),
) -> IngestResponse:
    """Load sheets from a directory, compute pieces, and persist metadata.

    Args:
        request: Ingestion parameters (sheet_dir, threshold, min_area).

    Returns:
        Summary of ingested data.
    """
    sheet_path = Path(request.sheet_dir)
    if not sheet_path.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid directory: {request.sheet_dir}",
        )

    result = service.ingest_sheets(
        sheet_dir=sheet_path,
        threshold=request.threshold,
        min_area=request.min_area,
    )
    return IngestResponse(**result)
