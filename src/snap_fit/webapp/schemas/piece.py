"""Pydantic schemas for piece endpoints."""

from pydantic import BaseModel


class PieceIn(BaseModel):
    """Input schema for piece ingestion."""

    name: str
    image_path: str | None = None


class PieceOut(BaseModel):
    """Output schema for piece resources."""

    id: str
    name: str
    image_path: str | None = None
