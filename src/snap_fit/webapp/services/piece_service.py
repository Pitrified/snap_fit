"""Service layer for piece operations (stubs)."""

from typing import TypedDict


class Piece(TypedDict):
    """Typed dict describing a piece resource."""

    id: str
    name: str
    image_path: str | None


def create_piece(name: str, image_path: str | None = None) -> Piece:
    """Create a new piece record (stub implementation)."""
    return {"id": "placeholder", "name": name, "image_path": image_path}


def get_piece(piece_id: str) -> Piece:
    """Retrieve a piece record by id (stub implementation)."""
    return {"id": piece_id, "name": "unknown", "image_path": None}
