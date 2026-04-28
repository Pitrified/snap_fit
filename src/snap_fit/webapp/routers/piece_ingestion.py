"""Router: piece ingestion and query endpoints.

Uses the data layer (SheetManager) via PieceService for persistence.
"""

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import Response

from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.data_models.sheet_record import SheetRecord
from snap_fit.webapp.core.settings import Settings
from snap_fit.webapp.core.settings import get_settings
from snap_fit.webapp.schemas.piece import IngestRequest
from snap_fit.webapp.schemas.piece import IngestResponse
from snap_fit.webapp.schemas.piece import SegmentShapesUpdate
from snap_fit.webapp.services.piece_service import PieceService

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


@router.get("/match-preview", summary="Get match preview image")
async def get_match_preview_img(
    piece1: str,
    edge1: str,
    piece2: str,
    edge2: str,
    service: Annotated[PieceService, Depends(get_piece_service)],
    orient1: int = 0,
    orient2: int = 0,
    size: int | None = None,
) -> Response:
    """Return a side-by-side PNG preview of two matching piece edges.

    Args:
        piece1: Placed piece identifier.
        edge1: ``EdgePos`` value of piece1's edge facing piece2
            (``top``/``right``/``bottom``/``left``).
        piece2: Candidate piece identifier.
        edge2: ``EdgePos`` value of piece2's edge facing piece1.
        orient1: Placement orientation of piece1 (0/90/180/270).
        orient2: Placement orientation of piece2 (0/90/180/270).
        size: Optional max dimension for the result image.
        service: ``PieceService`` instance (injected).
    """
    img_bytes = service.get_match_preview_img(
        piece1, edge1, orient1, piece2, edge2, orient2, size=size
    )
    if img_bytes is None:
        raise HTTPException(
            status_code=404,
            detail=f"Preview not available for {piece1} vs {piece2}",
        )
    return Response(content=img_bytes, media_type="image/png")


@router.get("/{piece_id}/img", summary="Get piece image")
async def get_piece_img(
    piece_id: str,
    service: Annotated[PieceService, Depends(get_piece_service)],
    size: int | None = None,
    orientation: int = 0,
    label: str | None = None,
) -> Response:
    """Return a PNG image of the piece cropped from its sheet photo."""
    if orientation not in (0, 90, 180, 270):
        raise HTTPException(
            status_code=400, detail="orientation must be 0, 90, 180, or 270"
        )
    try:
        img_bytes = service.get_piece_img(
            piece_id, size=size, orientation=orientation, label=label
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if img_bytes is None:
        raise HTTPException(status_code=404, detail=f"Piece {piece_id} not found")
    return Response(content=img_bytes, media_type="image/png")


@router.get("/{piece_id}/img/inspect", summary="Get piece image with contour overlay")
async def get_piece_inspection_img(
    piece_id: str,
    service: Annotated[PieceService, Depends(get_piece_service)],
    size: int | None = None,
) -> Response:
    """Return a PNG of the piece with coloured contour segment and corner overlays."""
    img_bytes = service.get_piece_inspection_img(piece_id, size=size)
    if img_bytes is None:
        raise HTTPException(status_code=404, detail=f"Piece {piece_id} not found")
    return Response(content=img_bytes, media_type="image/png")


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


@router.patch("/{piece_id}/segments", summary="Update piece segment shapes")
async def update_segment_shapes(
    piece_id: str,
    body: SegmentShapesUpdate,
    service: Annotated[PieceService, Depends(get_piece_service)],
) -> PieceRecord:
    """Update segment shape labels for a piece.

    Only the edges provided in ``shapes`` are changed.  The piece type and
    flat-edge list are recomputed automatically.

    Args:
        piece_id: Piece identifier (``sheet_id:piece_idx``).
        body: Mapping of edge position to shape value.
        service: PieceService instance (injected).

    Returns:
        The updated PieceRecord.
    """
    try:
        return service.update_segment_shapes(piece_id, body.shapes)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
