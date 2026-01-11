"""Service layer for puzzle operations (stubs)."""

from typing import Any


def solve_puzzle(
    piece_ids: list[str], config_path: str | None = None
) -> dict[str, Any]:
    """Attempt to solve a puzzle (placeholder implementation)."""
    # Use inputs minimally to avoid unused-argument lint warnings
    count = len(piece_ids) if piece_ids is not None else 0
    return {
        "success": False,
        "message": f"Not implemented ({count} pieces, config={config_path})",
        "layout": None,
    }
