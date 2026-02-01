"""Pydantic schemas for puzzle endpoints.

NOTE: Match data uses the existing data model:
- snap_fit.data_models.match_result.MatchResult

This file contains request/response schemas specific to the API.
"""

from pydantic import BaseModel


class PuzzleSolveRequest(BaseModel):
    """Request to solve a puzzle."""

    piece_ids: list[str] | None = None
    config_path: str | None = None


class PuzzleSolveResponse(BaseModel):
    """Response from puzzle solve."""

    success: bool
    message: str | None = None
    layout: dict | None = None
    piece_count: int = 0


class MatchQueryParams(BaseModel):
    """Parameters for filtering match results."""

    limit: int = 100
    min_similarity: float | None = None
    piece_id: str | None = None
