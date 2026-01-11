"""Router: piece ingestion endpoints."""

from fastapi import APIRouter

from snap_fit.webapp.schemas.piece import PieceIn
from snap_fit.webapp.schemas.piece import PieceOut

router = APIRouter()


@router.post("/", summary="Ingest a puzzle piece")
async def ingest_piece(payload: PieceIn) -> PieceOut:
    """Accept piece metadata and return created resource."""
    return PieceOut(id="placeholder", **payload.model_dump())


@router.get("/{piece_id}", summary="Get piece by ID")
async def get_piece(piece_id: str) -> PieceOut:
    """Retrieve piece details."""
    return PieceOut(id=piece_id, name="unknown", image_path=None)
