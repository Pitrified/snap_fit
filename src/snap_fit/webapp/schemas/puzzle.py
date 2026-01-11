"""Pydantic schemas for puzzle endpoints."""

from pydantic import BaseModel


class PuzzleSolveRequest(BaseModel):
    """Request to solve a puzzle."""

    piece_ids: list[str]
    config_path: str | None = None


class PuzzleSolveResponse(BaseModel):
    """Response from puzzle solve."""

    success: bool
    message: str | None = None
    layout: dict | None = None
