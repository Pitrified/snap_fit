"""Pydantic schemas for interactive session endpoints."""

from datetime import datetime

from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    """Request body for creating a new solve session."""

    dataset_tag: str
    grid_rows: int | None = None
    grid_cols: int | None = None


class PlaceRequest(BaseModel):
    """Request body for placing a piece on the grid."""

    piece_id: str
    position: str
    orientation: int


class SuggestionRequest(BaseModel):
    """Request body for generating a next-slot suggestion."""

    override_pos: str | None = None
    top_k: int = 5


class NeighborScoreDetail(BaseModel):
    """Score and edge info for one placed neighbor of a suggestion candidate."""

    score: float
    my_edge: str
    their_edge: str
    their_piece_id: str
    their_orientation: int


class SuggestionCandidate(BaseModel):
    """A single candidate for a grid slot."""

    piece_id: str
    piece_label: str | None = None
    orientation: int
    score: float
    neighbor_scores: dict[str, float]
    neighbor_details: dict[str, NeighborScoreDetail] = {}


class SuggestionBundle(BaseModel):
    """Top-K candidates for the next placement."""

    slot: str
    candidates: list[SuggestionCandidate]
    current_index: int = 0


class SolveSessionResponse(BaseModel):
    """Full session state returned from all session endpoints."""

    session_id: str
    dataset_tag: str
    grid_rows: int
    grid_cols: int
    placement: dict[str, tuple[str, int]]
    rejected: dict[str, list[str]]
    undo_stack: list[str]
    placed_count: int
    total_cells: int
    complete: bool
    score: float | None = None
    pending_suggestion: SuggestionBundle | None = None
    created_at: datetime
    updated_at: datetime
