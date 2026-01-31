"""Tests for the PieceRecord data model."""

from unittest.mock import MagicMock

import pytest

from snap_fit.config.types import CornerPos
from snap_fit.config.types import EdgePos
from snap_fit.config.types import SegmentShape
from snap_fit.data_models.piece_id import PieceId
from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation import OrientedPieceType
from snap_fit.grid.orientation import PieceType


class TestPieceRecordBasics:
    """Test basic PieceRecord functionality."""

    def test_create_piece_record(self) -> None:
        """Test creating a PieceRecord with all fields."""
        piece_id = PieceId(sheet_id="sheet_01", piece_id=0)
        oriented_type = OrientedPieceType(
            piece_type=PieceType.EDGE, orientation=Orientation.DEG_90
        )

        record = PieceRecord(
            piece_id=piece_id,
            corners={
                "top_left": (10, 20),
                "top_right": (100, 25),
                "bottom_left": (15, 110),
                "bottom_right": (105, 115),
            },
            segment_shapes={
                "left": "in",
                "right": "out",
                "top": "edge",
                "bottom": "in",
            },
            oriented_piece_type=oriented_type,
            flat_edges=["top"],
            contour_point_count=500,
            contour_region=(5, 10, 120, 130),
        )

        assert record.piece_id == piece_id
        assert record.corners["top_left"] == (10, 20)
        assert record.segment_shapes["left"] == "in"
        assert record.oriented_piece_type is not None
        assert record.oriented_piece_type.piece_type == PieceType.EDGE
        assert record.flat_edges == ["top"]
        assert record.contour_point_count == 500
        assert record.contour_region == (5, 10, 120, 130)

    def test_create_with_none_oriented_type(self) -> None:
        """Test creating a PieceRecord with no oriented_piece_type."""
        piece_id = PieceId(sheet_id="sheet_01", piece_id=1)

        record = PieceRecord(
            piece_id=piece_id,
            corners={
                "top_left": (0, 0),
                "top_right": (0, 0),
                "bottom_left": (0, 0),
                "bottom_right": (0, 0),
            },
            segment_shapes={"left": "in", "right": "out", "top": "in", "bottom": "out"},
            oriented_piece_type=None,
            flat_edges=[],
            contour_point_count=100,
            contour_region=(0, 0, 50, 50),
        )

        assert record.oriented_piece_type is None

    def test_serialization(self) -> None:
        """Test JSON serialization."""
        piece_id = PieceId(sheet_id="sheet_01", piece_id=2)
        oriented_type = OrientedPieceType(
            piece_type=PieceType.CORNER, orientation=Orientation.DEG_180
        )

        record = PieceRecord(
            piece_id=piece_id,
            corners={
                "top_left": (10, 20),
                "top_right": (100, 20),
                "bottom_left": (10, 100),
                "bottom_right": (100, 100),
            },
            segment_shapes={
                "left": "edge",
                "right": "out",
                "top": "edge",
                "bottom": "in",
            },
            oriented_piece_type=oriented_type,
            flat_edges=["left", "top"],
            contour_point_count=450,
            contour_region=(5, 15, 110, 95),
        )

        data = record.model_dump(mode="json")

        assert data["piece_id"]["sheet_id"] == "sheet_01"
        assert data["piece_id"]["piece_id"] == 2
        assert data["corners"]["top_left"] == [10, 20]
        assert data["segment_shapes"]["left"] == "edge"
        assert data["flat_edges"] == ["left", "top"]
        assert data["contour_point_count"] == 450

    def test_deserialization(self) -> None:
        """Test JSON deserialization."""
        data = {
            "piece_id": {"sheet_id": "sheet_x", "piece_id": 5},
            "corners": {
                "top_left": [10, 10],
                "top_right": [110, 10],
                "bottom_left": [10, 110],
                "bottom_right": [110, 110],
            },
            "segment_shapes": {
                "left": "in",
                "right": "out",
                "top": "weird",
                "bottom": "in",
            },
            "oriented_piece_type": {
                "piece_type": 0,  # INNER
                "orientation": 0,  # DEG_0
            },
            "flat_edges": [],
            "contour_point_count": 520,
            "contour_region": [0, 0, 120, 120],
        }

        record = PieceRecord.model_validate(data)

        assert record.piece_id.sheet_id == "sheet_x"
        assert record.piece_id.piece_id == 5
        assert record.corners["top_left"] == (10, 10)
        assert record.segment_shapes["top"] == "weird"
        assert record.oriented_piece_type is not None
        assert record.oriented_piece_type.piece_type == PieceType.INNER
        assert record.contour_point_count == 520


class TestPieceRecordFromPiece:
    """Test PieceRecord.from_piece class method."""

    @pytest.fixture
    def mock_piece(self) -> MagicMock:
        """Create a mock Piece object."""
        piece = MagicMock()
        piece.piece_id = PieceId(sheet_id="test_sheet", piece_id=3)

        # Mock corners
        piece.corners = {
            CornerPos.TOP_LEFT: (15, 25),
            CornerPos.TOP_RIGHT: (115, 30),
            CornerPos.BOTTOM_LEFT: (20, 125),
            CornerPos.BOTTOM_RIGHT: (120, 130),
        }

        # Mock segments with shapes - match EdgePos enum order: LEFT, BOTTOM, RIGHT, TOP
        mock_segments = {}
        shape_map = {
            EdgePos.LEFT: SegmentShape.IN,
            EdgePos.BOTTOM: SegmentShape.OUT,
            EdgePos.RIGHT: SegmentShape.EDGE,
            EdgePos.TOP: SegmentShape.IN,
        }
        for edge_pos, shape in shape_map.items():
            seg = MagicMock()
            seg.shape = shape
            mock_segments[edge_pos] = seg
        piece.segments = mock_segments

        # Mock oriented_piece_type
        piece.oriented_piece_type = OrientedPieceType(
            piece_type=PieceType.EDGE, orientation=Orientation.DEG_270
        )

        # Mock flat_edges
        piece.flat_edges = [EdgePos.RIGHT]

        # Mock contour
        piece.contour.cv_contour = MagicMock()
        piece.contour.cv_contour.__len__ = lambda x: 480
        piece.contour.region = (10, 20, 100, 110)

        return piece

    def test_from_piece_basic(self, mock_piece: MagicMock) -> None:
        """Test creating PieceRecord from a Piece mock."""
        record = PieceRecord.from_piece(mock_piece)

        assert record.piece_id.sheet_id == "test_sheet"
        assert record.piece_id.piece_id == 3
        assert record.corners["top_left"] == (15, 25)
        assert record.corners["bottom_right"] == (120, 130)
        assert record.segment_shapes["right"] == "edge"
        assert record.oriented_piece_type is not None
        assert record.oriented_piece_type.piece_type == PieceType.EDGE
        assert record.flat_edges == ["right"]
        assert record.contour_point_count == 480
        assert record.contour_region == (10, 20, 100, 110)

    def test_from_piece_all_segment_shapes(self, mock_piece: MagicMock) -> None:
        """Test that all segment shapes are captured."""
        record = PieceRecord.from_piece(mock_piece)

        # Check all edge positions are present
        assert set(record.segment_shapes.keys()) == {"left", "bottom", "right", "top"}

        # Check specific shapes (based on shape_map in fixture)
        assert record.segment_shapes["left"] == "in"
        assert record.segment_shapes["bottom"] == "out"
        assert record.segment_shapes["right"] == "edge"
        assert record.segment_shapes["top"] == "in"
