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
    """Request to ingest sheets for a named dataset.

    sheets_tag identifies the dataset folder under `data/`.
    The config is loaded from `data/{sheets_tag}/{sheets_tag}_SheetArucoConfig.json`
    and images are read from `data/{sheets_tag}/sheets/*.jpg`.
    """

    sheets_tag: str


class IngestResponse(BaseModel):
    """Response from sheet ingestion."""

    sheets_tag: str
    sheets_ingested: int
    pieces_detected: int
    cache_path: str
