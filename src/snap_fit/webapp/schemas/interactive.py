"""Pydantic schemas for interactive session endpoints."""

from pydantic import BaseModel


class SessionInfo(BaseModel):
    """Interactive session state."""

    session_id: str
    active: bool
