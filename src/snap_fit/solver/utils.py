"""Utility functions for puzzle solvers."""

from loguru import logger as lg

from snap_fit.data_models.piece_id import PieceId
from snap_fit.grid.orientation import PieceType
from snap_fit.puzzle.sheet_manager import SheetManager


def get_factor_pairs(
    n: int,
    min_size: int = 4,
) -> list[tuple[int, int]]:
    """Get all (rows, cols) pairs where rows <= cols and rows * cols == n.

    Args:
        n: The number to factor.
        min_size: Minimum size for rows and cols.

    Returns:
        List of (rows, cols) pairs.
    """
    pairs = []
    i = min_size
    while i * i <= n:
        if n % i == 0:
            j = n // i
            pairs.append((i, j))
            # ? if i != j: pairs.append((j, i)) # do we need both orientations?
        i += 1
    return sorted(pairs)


def partition_pieces_by_type(
    manager: SheetManager,
) -> tuple[list[PieceId], list[PieceId], list[PieceId]]:
    """Partition all pieces by their type (corner, edge, inner).

    Uses the detected piece type from each piece's oriented_piece_type
    to categorize pieces into three groups for placement during solving.

    Args:
        manager: SheetManager containing loaded puzzle pieces.

    Returns:
        Tuple of (corners, edges, inners) as lists of PieceId.

    Example:
        >>> corners, edges, inners = partition_pieces_by_type(manager)
        >>> lg.info(f"{len(corners)} corners, {len(edges)} edges, {len(inners)} inners")
    """
    corners: list[PieceId] = []
    edges: list[PieceId] = []
    inners: list[PieceId] = []

    for piece in manager.get_pieces_ls():
        piece_type = piece.oriented_piece_type.piece_type
        if piece_type == PieceType.CORNER:
            corners.append(piece.piece_id)
        elif piece_type == PieceType.EDGE:
            edges.append(piece.piece_id)
        else:
            inners.append(piece.piece_id)

    lg.debug(
        f"Partitioned pieces: {len(corners)} corners, {len(edges)} edges, "
        f"{len(inners)} inners"
    )

    return corners, edges, inners


def infer_grid_size(
    corners: list[PieceId],
    edges: list[PieceId],
    inners: list[PieceId],
    tolerance: int = 2,
) -> tuple[int, int] | None:
    """Infer grid dimensions from piece counts.

    Attempts to match piece counts to known grid sizes, allowing for
    some tolerance in case of piece type misclassification.

    For an NxM grid:
    - Corners: 4
    - Edges: 2*(N-2) + 2*(M-2)
    - Inners: (N-2)*(M-2)

    Args:
        corners: List of corner piece IDs.
        edges: List of edge piece IDs.
        inners: List of inner piece IDs.
        tolerance: Maximum allowed misclassification count.

    Returns:
        Tuple of (rows, cols) if a matching size is found, None otherwise.

    Example:
        >>> size = infer_grid_size(corners, edges, inners)
        >>> if size:
        ...     rows, cols = size
    """
    total_pieces = len(corners) + len(edges) + len(inners)

    # Generate all valid grid sizes for the given piece count
    possible_sizes = get_factor_pairs(total_pieces)

    for rows, cols in possible_sizes:
        if rows * cols != total_pieces:
            continue

        expected_corners = 4
        expected_edges = 2 * (rows - 2) + 2 * (cols - 2)
        expected_inners = (rows - 2) * (cols - 2)

        # Check if counts match within tolerance
        corner_diff = abs(len(corners) - expected_corners)
        edge_diff = abs(len(edges) - expected_edges)
        inner_diff = abs(len(inners) - expected_inners)

        if corner_diff + edge_diff + inner_diff <= tolerance:
            lg.debug(
                f"Matched grid {rows}x{cols}: expected "
                f"({expected_corners}, {expected_edges}, {expected_inners}), "
                f"got ({len(corners)}, {len(edges)}, {len(inners)})"
            )
            return (rows, cols)

    # Fallback: find any grid that matches total piece count (less strict)
    # start from the end to prefer squarer grids
    for rows, cols in reversed(possible_sizes):
        lg.warning(
            f"Using grid size {rows}x{cols} based on piece count only "
            f"(type distribution didn't match)"
        )
        return (rows, cols)

    return None
