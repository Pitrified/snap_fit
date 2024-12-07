"""Types and aliases for snap-fit package."""

from enum import Enum


class CornerPos(Enum):
    """Corner position enumeration."""

    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


CORNER_POSS = [
    CornerPos.TOP_LEFT,
    CornerPos.TOP_RIGHT,
    CornerPos.BOTTOM_LEFT,
    CornerPos.BOTTOM_RIGHT,
]


class EdgePos(Enum):
    """Edge position enumeration."""

    TOP = "top"
    RIGHT = "right"
    BOTTOM = "bottom"
    LEFT = "left"


EDGE_POSS = [
    EdgePos.TOP,
    EdgePos.RIGHT,
    EdgePos.BOTTOM,
    EdgePos.LEFT,
]

EDGE_ENDS_TO_CORNER = {
    EdgePos.TOP: (CornerPos.TOP_LEFT, CornerPos.TOP_RIGHT),
    EdgePos.RIGHT: (CornerPos.TOP_RIGHT, CornerPos.BOTTOM_RIGHT),
    EdgePos.BOTTOM: (CornerPos.BOTTOM_RIGHT, CornerPos.BOTTOM_LEFT),
    EdgePos.LEFT: (CornerPos.BOTTOM_LEFT, CornerPos.TOP_LEFT),
}
