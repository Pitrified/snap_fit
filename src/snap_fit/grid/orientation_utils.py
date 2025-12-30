"""Orientation utility functions for grid model."""

from snap_fit.config.types import EdgePos
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation import OrientedPieceType
from snap_fit.grid.orientation import PieceType

# Mapping from EdgePos to its clockwise index (0=TOP, 1=RIGHT, 2=BOTTOM, 3=LEFT)
_EDGE_TO_INDEX: dict[EdgePos, int] = {
    EdgePos.TOP: 0,
    EdgePos.RIGHT: 1,
    EdgePos.BOTTOM: 2,
    EdgePos.LEFT: 3,
}

_INDEX_TO_EDGE: dict[int, EdgePos] = {v: k for k, v in _EDGE_TO_INDEX.items()}

# For corners, canonical is TOP+LEFT flat, so second flat is at index 3 (LEFT)
# relative to first flat at index 0 (TOP)
_CORNER_SECOND_FLAT_OFFSET = 3  # LEFT is 3 steps clockwise from TOP

# Number of flat edges for each piece type
_CORNER_FLAT_COUNT = 2
_ADJACENT_WRAP_DIFF = (
    3  # Difference when two adjacent edges wrap around (e.g., LEFT and TOP)
)


def get_piece_type(flat_edge_count: int) -> PieceType:
    """Classify piece based on number of flat edges.

    Args:
        flat_edge_count: Number of flat (boundary) edges on the piece.

    Returns:
        PieceType: INNER (0), EDGE (1), or CORNER (2).

    Raises:
        ValueError: If flat_edge_count is not 0, 1, or 2.
    """
    if flat_edge_count == 0:
        return PieceType.INNER
    if flat_edge_count == 1:
        return PieceType.EDGE
    if flat_edge_count == _CORNER_FLAT_COUNT:
        return PieceType.CORNER
    msg = f"Invalid flat_edge_count: {flat_edge_count}. Expected 0, 1, or 2."
    raise ValueError(msg)


def detect_base_orientation(flat_edge_positions: list[EdgePos]) -> Orientation:
    """Determine piece's photographed orientation relative to canonical.

    Canonical conventions:
    - EDGE: flat on TOP (DEG_0)
    - CORNER: flats on TOP + LEFT (DEG_0)
    - INNER: no flat edges, returns DEG_0

    Args:
        flat_edge_positions: List of EdgePos where flat edges are detected.

    Returns:
        Orientation: The rotation from canonical to the photographed orientation.
                    To rotate piece to canonical, apply -orientation.
    """
    n_flats = len(flat_edge_positions)

    if n_flats == 0:
        # INNER piece: no anchor, canonical by definition
        return Orientation.DEG_0

    if n_flats == 1:
        # EDGE piece: canonical has flat on TOP
        # If flat is on RIGHT, piece is rotated 90° from canonical
        flat_pos = flat_edge_positions[0]
        flat_idx = _EDGE_TO_INDEX[flat_pos]
        canonical_idx = _EDGE_TO_INDEX[EdgePos.TOP]
        steps = (flat_idx - canonical_idx) % 4
        return Orientation.from_steps(steps)

    if n_flats == _CORNER_FLAT_COUNT:
        # CORNER piece: canonical has flats on TOP + LEFT
        # In canonical: TOP is at index 0, LEFT is at index 3 (diff of 3 clockwise)
        # We need to find which flat corresponds to "TOP" (the first flat clockwise)
        idxs = sorted(_EDGE_TO_INDEX[p] for p in flat_edge_positions)

        # Two adjacent flats: check if they're adjacent (differ by 1 or 3)
        diff = (idxs[1] - idxs[0]) % 4
        if diff == 1:
            # Adjacent clockwise: idxs[1] is one step clockwise from idxs[0]
            # The "first" flat (corresponding to TOP) is idxs[1]
            # because in canonical TOP(0)+LEFT(3), LEFT is 3 steps from TOP
            # Here with diff=1, idxs[0] would be the "LEFT-equivalent" (second flat)
            first_flat_idx = idxs[1]
        elif diff == _ADJACENT_WRAP_DIFF:
            # Wrapping case: idxs[0] is 3 steps before idxs[1] (wrapping around)
            # This is like TOP(0)+LEFT(3): idxs[0]=0 is TOP, idxs[1]=3 is LEFT
            first_flat_idx = idxs[0]
        else:
            # Non-adjacent flats (opposite edges) - unusual but handle gracefully
            first_flat_idx = idxs[0]

        canonical_first_idx = _EDGE_TO_INDEX[EdgePos.TOP]
        steps = (first_flat_idx - canonical_first_idx) % 4
        return Orientation.from_steps(steps)

    # More than 2 flats: unusual, return DEG_0
    return Orientation.DEG_0


def compute_rotation(
    piece: OrientedPieceType, target: OrientedPieceType
) -> Orientation:
    """Compute rotation needed to align piece's base orientation to target.

    Args:
        piece: The piece's detected OrientedPieceType (from photograph).
        target: The target slot's OrientedPieceType (from grid).

    Returns:
        Orientation: The rotation to apply to the piece to fit the target slot.

    Example:
        If piece has flat on RIGHT (90° from canonical) and slot wants flat on
        BOTTOM (180° from canonical), the rotation needed is 90°.
    """
    # piece.orientation is the rotation from canonical to photographed position
    # target.orientation is the rotation from canonical to desired position
    # Rotation needed: target.orientation - piece.orientation
    return target.orientation - piece.orientation


def get_rotated_edge_pos(original_pos: EdgePos, rotation: Orientation) -> EdgePos:
    """Compute effective edge position after rotation.

    When a piece is rotated, its edges move to new positions.
    This function returns where an edge ends up after rotation.

    Args:
        original_pos: The edge position in the piece's original orientation.
        rotation: The clockwise rotation applied to the piece.

    Returns:
        EdgePos: The edge position after rotation.

    Example:
        If original_pos is TOP and rotation is 90°, the TOP edge moves to
        where RIGHT was, so returns RIGHT.
    """
    original_idx = _EDGE_TO_INDEX[original_pos]
    rotated_idx = (original_idx + rotation.steps) % 4
    return _INDEX_TO_EDGE[rotated_idx]


def get_original_edge_pos(rotated_pos: EdgePos, rotation: Orientation) -> EdgePos:
    """Compute original edge position before rotation.

    Inverse of get_rotated_edge_pos. Given where an edge is after rotation,
    returns where it was originally.

    Args:
        rotated_pos: The edge position after rotation.
        rotation: The clockwise rotation that was applied.

    Returns:
        EdgePos: The original edge position before rotation.

    Example:
        If we want the edge that ends up at TOP after a 90° rotation,
        that was originally at LEFT.
    """
    rotated_idx = _EDGE_TO_INDEX[rotated_pos]
    original_idx = (rotated_idx - rotation.steps) % 4
    return _INDEX_TO_EDGE[original_idx]
