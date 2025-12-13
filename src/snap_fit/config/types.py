"""Types and aliases for snap-fit package."""

from enum import Enum
from enum import StrEnum


class CornerPos(Enum):
    """Corner position enumeration."""

    TOP_LEFT = "top_left"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    TOP_RIGHT = "top_right"


class EdgePos(Enum):
    """Edge position enumeration."""

    LEFT = "left"
    BOTTOM = "bottom"
    RIGHT = "right"
    TOP = "top"


EDGE_ENDS_TO_CORNER = {
    EdgePos.LEFT: (CornerPos.TOP_LEFT, CornerPos.BOTTOM_LEFT),
    EdgePos.BOTTOM: (CornerPos.BOTTOM_LEFT, CornerPos.BOTTOM_RIGHT),
    EdgePos.RIGHT: (CornerPos.BOTTOM_RIGHT, CornerPos.TOP_RIGHT),
    EdgePos.TOP: (CornerPos.TOP_RIGHT, CornerPos.TOP_LEFT),
}


class SegmentShape(StrEnum):
    """Shape of a segment."""

    IN = "in"
    OUT = "out"
    EDGE = "edge"
    WEIRD = "weird"
