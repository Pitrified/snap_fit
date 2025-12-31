"""Grid position type for puzzle grid."""

from pydantic import BaseModel


class GridPos(BaseModel, frozen=True):
    """Grid position with row and column.

    Frozen for hashability (can be used in sets/dicts).

    Attributes:
        ro: Row index (0-based).
        co: Column index (0-based).
    """

    ro: int
    co: int

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"({self.ro}, {self.co})"

    def __repr__(self) -> str:
        """Detailed repr for debugging."""
        return f"GridPos(ro={self.ro}, co={self.co})"
