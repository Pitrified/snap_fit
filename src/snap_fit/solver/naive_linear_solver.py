"""Naive Linear Solver - Greedy row-by-row puzzle solver."""

import random
from typing import TYPE_CHECKING
from typing import Any

from loguru import logger as lg

from snap_fit.data_models.piece_id import PieceId
from snap_fit.grid.grid_model import GridModel
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.placement_state import PlacementState
from snap_fit.grid.scoring import score_edge
from snap_fit.grid.scoring import score_grid_with_details
from snap_fit.grid.types import GridPos
from snap_fit.puzzle.sheet_manager import SheetManager

if TYPE_CHECKING:
    from snap_fit.puzzle.piece_matcher import PieceMatcher


class NaiveLinearSolver:
    """Greedy row-by-row puzzle solver.

    Places pieces starting from the top-left corner, filling each row
    left-to-right before moving to the next row. Uses a greedy strategy
    to select the best-matching piece at each position.

    Handles misclassified pieces gracefully by falling back to any available
    piece when the expected type runs out.

    Edge and corner pieces are rotated based on their detected base orientation
    so their flat edge(s) align with the grid boundary.

    Attributes:
        grid: The grid model defining puzzle structure.
        matcher: Piece matcher with cached similarity scores.
        manager: SheetManager for piece metadata access.
        state: Current placement state (populated after solve()).

    Example:
        >>> from snap_fit.solver import NaiveLinearSolver, partition_pieces_by_type
        >>> corners, edges, inners = partition_pieces_by_type(manager)
        >>> solver = NaiveLinearSolver(grid, matcher, manager, corners, edges, inners)
        >>> result = solver.solve()
        >>> score = solver.score_solution(result)
    """

    def __init__(
        self,
        grid: GridModel,
        matcher: "PieceMatcher",
        manager: SheetManager,
        corners: list[PieceId],
        edges: list[PieceId],
        inners: list[PieceId],
    ) -> None:
        """Initialize the solver.

        Args:
            grid: The grid model defining puzzle structure.
            matcher: Pre-populated piece matcher with cached scores.
            manager: SheetManager to access piece metadata (for base orientations).
            corners: Available corner piece IDs.
            edges: Available edge piece IDs.
            inners: Available inner piece IDs.
        """
        self.grid = grid
        self.matcher: Any = matcher  # Use Any to allow duck-typed matchers
        self.manager = manager
        self.state = PlacementState(grid)

        # Mutable pools of available pieces
        self._corners = list(corners)
        self._edges = list(edges)
        self._inners = list(inners)

        # Track if we had to abort early
        self._aborted = False
        self._abort_reason = ""

    def _get_all_available(self) -> list[PieceId]:
        """Get all remaining available pieces regardless of type."""
        return self._corners + self._edges + self._inners

    def _remove_from_pool(self, piece_id: PieceId) -> None:
        """Remove a piece from whichever pool it belongs to."""
        if piece_id in self._corners:
            self._corners.remove(piece_id)
        elif piece_id in self._edges:
            self._edges.remove(piece_id)
        elif piece_id in self._inners:
            self._inners.remove(piece_id)

    def _get_candidates_with_fallback(
        self, primary: list[PieceId], slot_type: str
    ) -> list[PieceId]:
        """Get candidates, falling back to all available if primary is empty.

        Args:
            primary: The preferred candidate list (e.g., corners for corner slots).
            slot_type: Description for logging (e.g., "corner", "edge").

        Returns:
            List of candidate piece IDs.
        """
        if primary:
            return primary

        # Fallback: use any available piece
        all_available = self._get_all_available()
        if all_available:
            lg.warning(
                f"No {slot_type} pieces left, falling back to {len(all_available)} "
                f"remaining pieces of other types"
            )
            return all_available

        return []

    def _compute_piece_orientation(
        self, piece_id: PieceId, slot_orientation: Orientation
    ) -> Orientation:
        """Compute the rotation needed for a piece to match a slot's orientation.

        For edge/corner pieces, this rotates the piece so its flat edge(s) align
        with the grid boundary.

        Args:
            piece_id: The piece to place.
            slot_orientation: The canonical orientation required by the grid slot.

        Returns:
            The orientation to use when placing the piece.
        """
        piece = self.manager.get_piece(piece_id)
        if piece is None:
            lg.warning(
                f"Could not find piece {piece_id}, using slot orientation directly"
            )
            return slot_orientation

        # Get the piece's base orientation (where its flat edge(s) are detected)
        piece_base_orientation = piece.oriented_piece_type.orientation

        # Rotation needed = slot_orientation - piece_base_orientation
        # This rotates the piece so its flat aligns with the slot's flat position
        rotation = slot_orientation - piece_base_orientation
        return rotation

    def solve(self) -> PlacementState:
        """Execute the greedy solver.

        Fills the grid row by row, left to right, starting from the top-left
        corner. Uses greedy selection to pick the best-matching piece at each
        position based on similarity scores with already-placed neighbors.

        Returns:
            PlacementState with pieces placed (may be incomplete if pieces run out).

        Raises:
            No exceptions are raised; solver tracks abort status internally.
        """
        lg.info(f"Starting solve for {self.grid.rows}x{self.grid.cols} grid")
        lg.info(
            f"Available: {len(self._corners)} corners, {len(self._edges)} edges, "
            f"{len(self._inners)} inners"
        )

        try:
            # Row 0
            self._place_row_zero()

            # Remaining rows
            for row in range(1, self.grid.rows):
                self._place_subsequent_row(row)

        except StopIteration as e:
            self._aborted = True
            self._abort_reason = str(e)
            lg.error(f"Solver aborted: {e}")

        lg.info(
            f"Solve complete. Placed {self.state.placed_count}/{self.grid.total_cells} "
            "pieces."
        )
        if self._aborted:
            lg.warning(f"Puzzle incomplete due to: {self._abort_reason}")

        return self.state

    def score_solution(self, state: PlacementState | None = None) -> float:
        """Compute total score for a placement state.

        Args:
            state: Placement state to score. If None, uses self.state.

        Returns:
            Total similarity score (lower is better).
        """
        if state is None:
            state = self.state
        total_score, _ = score_grid_with_details(state, self.matcher)
        return total_score

    def _place_row_zero(self) -> None:
        """Place the first row: corner → edges → corner."""
        # Top-left corner (0, 0) - random selection
        pos_tl = GridPos(ro=0, co=0)
        slot_orientation = self.grid.get_slot_type(pos_tl).orientation
        candidates = self._get_candidates_with_fallback(self._corners, "corner")
        if not candidates:
            msg = "No pieces available for top-left corner"
            raise StopIteration(msg)

        corner_tl = random.choice(candidates)  # noqa: S311
        piece_orientation = self._compute_piece_orientation(corner_tl, slot_orientation)
        self._remove_from_pool(corner_tl)
        self.state.place(corner_tl, pos_tl, piece_orientation)
        lg.debug(
            f"Placed top-left corner {corner_tl} at {pos_tl} orient={piece_orientation}"
        )

        # Edge pieces for columns 1..cols-2
        for col in range(1, self.grid.cols - 1):
            pos = GridPos(ro=0, co=col)
            slot_orientation = self.grid.get_slot_type(pos).orientation
            neighbors = [GridPos(ro=0, co=col - 1)]  # left neighbor only

            candidates = self._get_candidates_with_fallback(self._edges, "edge")
            if not candidates:
                msg = f"No pieces available for position {pos}"
                raise StopIteration(msg)

            best_piece, best_orient, best_score = self._find_best_piece_boundary(
                candidates=candidates,
                pos=pos,
                neighbors=neighbors,
                slot_orientation=slot_orientation,
            )
            self._remove_from_pool(best_piece)
            self.state.place(best_piece, pos, best_orient)
            lg.debug(
                f"Placed edge {best_piece} at {pos} orient={best_orient} "
                f"score={best_score:.4f}"
            )

        # Top-right corner (0, cols-1)
        pos_tr = GridPos(ro=0, co=self.grid.cols - 1)
        slot_orientation = self.grid.get_slot_type(pos_tr).orientation
        neighbors = [GridPos(ro=0, co=self.grid.cols - 2)]  # left neighbor

        candidates = self._get_candidates_with_fallback(self._corners, "corner")
        if not candidates:
            msg = f"No pieces available for position {pos_tr}"
            raise StopIteration(msg)

        best_piece, best_orient, best_score = self._find_best_piece_boundary(
            candidates=candidates,
            pos=pos_tr,
            neighbors=neighbors,
            slot_orientation=slot_orientation,
        )
        self._remove_from_pool(best_piece)
        self.state.place(best_piece, pos_tr, best_orient)
        lg.debug(
            f"Placed top-right corner {best_piece} at {pos_tr} orient={best_orient} "
            f"score={best_score:.4f}"
        )

    def _place_subsequent_row(self, row: int) -> None:
        """Place a row using top and left neighbor constraints.

        Args:
            row: The row index (1 to rows-1).
        """
        is_last_row = row == self.grid.rows - 1

        # Left edge or bottom-left corner
        pos_left = GridPos(ro=row, co=0)
        slot_orientation = self.grid.get_slot_type(pos_left).orientation
        neighbors = [GridPos(ro=row - 1, co=0)]  # top neighbor

        if is_last_row:
            candidates = self._get_candidates_with_fallback(self._corners, "corner")
        else:
            candidates = self._get_candidates_with_fallback(self._edges, "edge")

        if not candidates:
            msg = f"No pieces available for position {pos_left}"
            raise StopIteration(msg)

        best_piece, best_orient, best_score = self._find_best_piece_boundary(
            candidates=candidates,
            pos=pos_left,
            neighbors=neighbors,
            slot_orientation=slot_orientation,
        )
        self._remove_from_pool(best_piece)
        self.state.place(best_piece, pos_left, best_orient)
        lg.debug(
            f"Placed left piece {best_piece} at {pos_left} orient={best_orient} "
            f"score={best_score:.4f}"
        )

        # Inner pieces (or bottom edges for last row) for columns 1..cols-2
        for col in range(1, self.grid.cols - 1):
            pos = GridPos(ro=row, co=col)
            neighbors = [
                GridPos(ro=row, co=col - 1),  # left
                GridPos(ro=row - 1, co=col),  # top
            ]

            if is_last_row:
                slot_orientation = self.grid.get_slot_type(pos).orientation
                candidates = self._get_candidates_with_fallback(self._edges, "edge")

                if not candidates:
                    msg = f"No pieces available for position {pos}"
                    raise StopIteration(msg)

                best_piece, best_orient, best_score = self._find_best_piece_boundary(
                    candidates=candidates,
                    pos=pos,
                    neighbors=neighbors,
                    slot_orientation=slot_orientation,
                )
            else:
                candidates = self._get_candidates_with_fallback(self._inners, "inner")

                if not candidates:
                    msg = f"No pieces available for position {pos}"
                    raise StopIteration(msg)

                # Inner pieces try all 4 orientations
                best_piece, best_orient, best_score = self._find_best_piece_inner(
                    candidates=candidates,
                    pos=pos,
                    neighbors=neighbors,
                )

            self._remove_from_pool(best_piece)
            self.state.place(best_piece, pos, best_orient)
            lg.debug(
                f"Placed {best_piece} at {pos} orient={best_orient} "
                f"score={best_score:.4f}"
            )

        # Right edge or bottom-right corner
        pos_right = GridPos(ro=row, co=self.grid.cols - 1)
        slot_orientation = self.grid.get_slot_type(pos_right).orientation
        neighbors = [
            GridPos(ro=row, co=self.grid.cols - 2),  # left
            GridPos(ro=row - 1, co=self.grid.cols - 1),  # top
        ]

        if is_last_row:
            candidates = self._get_candidates_with_fallback(self._corners, "corner")
        else:
            candidates = self._get_candidates_with_fallback(self._edges, "edge")

        if not candidates:
            msg = f"No pieces available for position {pos_right}"
            raise StopIteration(msg)

        best_piece, best_orient, best_score = self._find_best_piece_boundary(
            candidates=candidates,
            pos=pos_right,
            neighbors=neighbors,
            slot_orientation=slot_orientation,
        )
        self._remove_from_pool(best_piece)
        self.state.place(best_piece, pos_right, best_orient)
        lg.debug(
            f"Placed right piece {best_piece} at {pos_right} orient={best_orient} "
            f"score={best_score:.4f}"
        )

    def _find_best_piece_boundary(
        self,
        candidates: list[PieceId],
        pos: GridPos,
        neighbors: list[GridPos],
        slot_orientation: Orientation,
    ) -> tuple[PieceId, Orientation, float]:
        """Find best edge/corner piece, using fixed orientation per piece.

        Each candidate has exactly ONE valid orientation based on where its
        flat edge(s) are detected and where the slot requires them.

        Args:
            candidates: Available edge/corner pieces to evaluate.
            pos: Target grid position.
            neighbors: Adjacent positions with already-placed pieces.
            slot_orientation: The canonical orientation required by the slot.

        Returns:
            Tuple of (best_piece_id, best_orientation, best_score).

        Raises:
            StopIteration: If no candidates available or no valid piece found.
        """
        if not candidates:
            msg = f"No candidates available for position {pos}"
            raise StopIteration(msg)

        best_piece: PieceId | None = None
        best_orient: Orientation = Orientation.DEG_0
        best_score = float("inf")

        for piece_id in candidates:
            # Compute the ONE valid orientation for this boundary piece
            orientation = self._compute_piece_orientation(piece_id, slot_orientation)

            # Temporarily place to compute score
            self.state.place(piece_id, pos, orientation)

            # Sum scores against all placed neighbors
            total_score = 0.0
            for neighbor_pos in neighbors:
                edge_score = score_edge(self.state, pos, neighbor_pos, self.matcher)
                if edge_score is not None:
                    total_score += edge_score

            # Track best
            if total_score < best_score:
                best_score = total_score
                best_piece = piece_id
                best_orient = orientation

            # Remove temporary placement
            self.state.remove(pos)

        if best_piece is None:
            msg = f"Could not find best piece for position {pos}"
            raise StopIteration(msg)

        return best_piece, best_orient, best_score

    def _find_best_piece_inner(
        self,
        candidates: list[PieceId],
        pos: GridPos,
        neighbors: list[GridPos],
    ) -> tuple[PieceId, Orientation, float]:
        """Find best inner piece, trying all 4 orientations.

        Inner pieces have no flat edges so can be placed in any orientation.

        Args:
            candidates: Available inner pieces to evaluate.
            pos: Target grid position.
            neighbors: Adjacent positions with already-placed pieces.

        Returns:
            Tuple of (best_piece_id, best_orientation, best_score).

        Raises:
            StopIteration: If no candidates available or no valid piece found.
        """
        if not candidates:
            msg = f"No candidates available for position {pos}"
            raise StopIteration(msg)

        best_piece: PieceId | None = None
        best_orient: Orientation = Orientation.DEG_0
        best_score = float("inf")

        for piece_id in candidates:
            for orientation in Orientation:
                # Temporarily place to compute score
                self.state.place(piece_id, pos, orientation)

                # Sum scores against all placed neighbors
                total_score = 0.0
                for neighbor_pos in neighbors:
                    edge_score = score_edge(self.state, pos, neighbor_pos, self.matcher)
                    if edge_score is not None:
                        total_score += edge_score

                # Track best
                if total_score < best_score:
                    best_score = total_score
                    best_piece = piece_id
                    best_orient = orientation

                # Remove temporary placement
                self.state.remove(pos)

        if best_piece is None:
            msg = f"Could not find best piece for position {pos}"
            raise StopIteration(msg)

        return best_piece, best_orient, best_score
