"""Grid model for puzzle piece placement and scoring."""

from snap_fit.grid.grid_model import GridModel
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation import OrientedPieceType
from snap_fit.grid.orientation import PieceType
from snap_fit.grid.orientation_utils import compute_rotation
from snap_fit.grid.orientation_utils import detect_base_orientation
from snap_fit.grid.orientation_utils import get_original_edge_pos
from snap_fit.grid.orientation_utils import get_piece_type
from snap_fit.grid.orientation_utils import get_rotated_edge_pos
from snap_fit.grid.placement_state import PlacementState
from snap_fit.grid.scoring import score_edge
from snap_fit.grid.scoring import score_grid
from snap_fit.grid.scoring import score_grid_with_details
from snap_fit.grid.types import GridPos

__all__ = [
    "GridModel",
    "GridPos",
    "Orientation",
    "OrientedPieceType",
    "PieceType",
    "PlacementState",
    "compute_rotation",
    "detect_base_orientation",
    "get_original_edge_pos",
    "get_piece_type",
    "get_rotated_edge_pos",
    "score_edge",
    "score_grid",
    "score_grid_with_details",
]
