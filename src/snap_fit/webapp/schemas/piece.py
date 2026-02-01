"""Pydantic schemas for piece endpoints.

NOTE: The primary schemas are the existing data models:
- snap_fit.data_models.sheet_record.SheetRecord
- snap_fit.data_models.piece_record.PieceRecord

This file contains any additional request/response wrappers needed
by the API that are not covered by the core data models.
"""

from pydantic import BaseModel


class PieceIn(BaseModel):
    """Input schema for piece ingestion (legacy, deprecated)."""

    name: str
    image_path: str | None = None


class PieceOut(BaseModel):
    """Output schema for piece resources (legacy, deprecated)."""

    id: str
    name: str
    image_path: str | None = None


class IngestRequest(BaseModel):
    """Request to ingest sheets from a directory."""

    sheet_dir: str
    threshold: int = 130
    min_area: int = 80_000


class IngestResponse(BaseModel):
    """Response from sheet ingestion."""

    sheets_ingested: int
    pieces_detected: int
    cache_path: str
