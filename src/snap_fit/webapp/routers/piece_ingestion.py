"""Router: piece ingestion and query endpoints.

Uses the data layer (SheetManager) via PieceService for persistence.
"""

from typing import Annotated

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


def get_piece_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> PieceService:
    """Dependency to get PieceService instance."""
    return PieceService(settings.cache_path, dataset_tag=settings.active_dataset)


@router.get("/", summary="List all pieces")
async def list_pieces(
    service: Annotated[PieceService, Depends(get_piece_service)],
) -> list[PieceRecord]:
    """Return all piece records from cached metadata."""
    return service.list_pieces()


@router.get("/sheets", summary="List all sheets")
async def list_sheets(
    service: Annotated[PieceService, Depends(get_piece_service)],
) -> list[SheetRecord]:
    """Return all sheet records from cached metadata."""
    return service.list_sheets()


@router.get(
    "/sheets/{sheet_id}",
    summary="Get sheet by ID",
)
async def get_sheet(
    sheet_id: str,
    service: Annotated[PieceService, Depends(get_piece_service)],
) -> SheetRecord:
    """Retrieve sheet details by sheet ID."""
    record = service.get_sheet(sheet_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Sheet {sheet_id} not found")
    return record


@router.get(
    "/sheets/{sheet_id}/pieces",
    summary="List pieces for sheet",
)
async def list_pieces_for_sheet(
    sheet_id: str,
    service: Annotated[PieceService, Depends(get_piece_service)],
) -> list[PieceRecord]:
    """Return all pieces belonging to a specific sheet."""
    return service.get_pieces_for_sheet(sheet_id)


@router.get("/{piece_id}", summary="Get piece by ID")
async def get_piece(
    piece_id: str,
    service: Annotated[PieceService, Depends(get_piece_service)],
) -> PieceRecord:
    """Retrieve piece details by piece ID (format: sheet_id-piece_idx)."""
    record = service.get_piece(piece_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Piece {piece_id} not found")
    return record


@router.post("/ingest", summary="Ingest sheets")
async def ingest_sheets(
    request: IngestRequest,
    service: Annotated[PieceService, Depends(get_piece_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> IngestResponse:
    """Load sheets for a named dataset, compute pieces, and persist metadata.

    Args:
        request: Ingestion parameters - only `sheets_tag` is required.
            The config and image folder are resolved automatically from
            `data/{sheets_tag}/`.
        service: PieceService instance (injected).
        settings: App settings used to resolve data_dir (injected).

    Returns:
        Summary of ingested data.
    """
    try:
        result = service.ingest_sheets(
            sheets_tag=request.sheets_tag,
            data_dir=settings.data_path,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IngestResponse(**result)
