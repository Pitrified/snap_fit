"""Pydantic schemas for settings endpoints."""

from pydantic import BaseModel


class SetDatasetRequest(BaseModel):
    """Request to set the active dataset tag. Pass None to clear selection."""

    tag: str | None = None
