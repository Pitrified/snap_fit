"""Tests for the SheetManager class."""

import json
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import numpy as np
import pytest

from snap_fit.config.types import CornerPos
from snap_fit.config.types import EdgePos
from snap_fit.config.types import SegmentShape
from snap_fit.data_models.piece_id import PieceId
from snap_fit.data_models.segment_id import SegmentId
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation import OrientedPieceType
from snap_fit.grid.orientation import PieceType
from snap_fit.image.segment import Segment
from snap_fit.puzzle.piece import Piece
from snap_fit.puzzle.sheet import Sheet
from snap_fit.puzzle.sheet_manager import SheetManager


@pytest.fixture
def sheet_manager() -> SheetManager:
    """Fixture for creating a SheetManager instance."""
    return SheetManager()


def create_mock_sheet(sheet_id: str) -> MagicMock:
    """Fixture to create a mock Sheet with pieces."""
    sheet = MagicMock(spec=Sheet)
    sheet.sheet_id = sheet_id
    # Create mock pieces with piece_id attributes
    piece0 = MagicMock(spec=Piece)
    piece0.piece_id = PieceId(sheet_id=sheet_id, piece_id=0)
    piece0.segments = {
        EdgePos.LEFT: MagicMock(spec=Segment),
        EdgePos.BOTTOM: MagicMock(spec=Segment),
        EdgePos.RIGHT: MagicMock(spec=Segment),
        EdgePos.TOP: MagicMock(spec=Segment),
    }
    piece1 = MagicMock(spec=Piece)
    piece1.piece_id = PieceId(sheet_id=sheet_id, piece_id=1)
    piece1.segments = {
        EdgePos.LEFT: MagicMock(spec=Segment),
        EdgePos.BOTTOM: MagicMock(spec=Segment),
        EdgePos.RIGHT: MagicMock(spec=Segment),
        EdgePos.TOP: MagicMock(spec=Segment),
    }
    sheet.pieces = [piece0, piece1]
    return sheet


@pytest.fixture
def mock_sheet() -> MagicMock:
    """Fixture for creating a mock Sheet."""
    return create_mock_sheet("test_sheet_1")


def test_add_sheet(sheet_manager: SheetManager, mock_sheet: MagicMock) -> None:
    """Test adding a single sheet."""
    sheet_id = "test_sheet_1"
    sheet_manager.add_sheet(mock_sheet, sheet_id)

    assert sheet_id in sheet_manager.sheets
    assert sheet_manager.sheets[sheet_id] == mock_sheet


def test_get_sheet(sheet_manager: SheetManager, mock_sheet: MagicMock) -> None:
    """Test retrieving a sheet."""
    sheet_id = "test_sheet_1"
    sheet_manager.add_sheet(mock_sheet, sheet_id)

    retrieved_sheet = sheet_manager.get_sheet(sheet_id)
    assert retrieved_sheet == mock_sheet


def test_get_sheet_not_found(sheet_manager: SheetManager) -> None:
    """Test retrieving a non-existent sheet."""
    retrieved_sheet = sheet_manager.get_sheet("non_existent")
    assert retrieved_sheet is None


def test_get_sheets_ls(sheet_manager: SheetManager) -> None:
    """Test retrieving all sheets as a list."""
    sheet1 = create_mock_sheet("sheet1")
    sheet2 = create_mock_sheet("sheet2")
    sheet_manager.add_sheet(sheet1, "sheet1")
    sheet_manager.add_sheet(sheet2, "sheet2")

    sheets_ls = sheet_manager.get_sheets_ls()
    assert len(sheets_ls) == 2
    assert sheet1 in sheets_ls
    assert sheet2 in sheets_ls


def test_get_pieces_ls(sheet_manager: SheetManager, mock_sheet: MagicMock) -> None:
    """Test retrieving all pieces from all sheets."""
    sheet_manager.add_sheet(mock_sheet, "sheet1")

    # mock_sheet has 2 pieces
    pieces = sheet_manager.get_pieces_ls()
    assert len(pieces) == 2
    assert pieces == mock_sheet.pieces


def test_add_sheets_glob(sheet_manager: SheetManager, tmp_path: Path) -> None:
    """Test adding sheets from a directory using glob."""
    # Create dummy files
    (tmp_path / "sheet1.txt").touch()
    (tmp_path / "sheet2.txt").touch()
    (tmp_path / "ignore.log").touch()

    mock_loader = MagicMock()
    mock_sheet = MagicMock(spec=Sheet)
    mock_sheet.pieces = []
    mock_loader.return_value = mock_sheet

    sheet_manager.add_sheets(
        folder_path=tmp_path,
        pattern="*.txt",
        loader_func=mock_loader,
    )

    assert len(sheet_manager.sheets) == 2
    assert mock_loader.call_count == 2

    # Check IDs are relative paths
    assert "sheet1.txt" in sheet_manager.sheets
    assert "sheet2.txt" in sheet_manager.sheets


def test_add_sheets_no_loader(sheet_manager: SheetManager, tmp_path: Path) -> None:
    """Test adding sheets without a loader function (should warn and skip)."""
    (tmp_path / "sheet1.txt").touch()

    with patch("snap_fit.puzzle.sheet_manager.lg") as mock_logger:
        sheet_manager.add_sheets(
            folder_path=tmp_path,
            pattern="*.txt",
            loader_func=None,
        )

        assert len(sheet_manager.sheets) == 0
        mock_logger.warning.assert_called()


def test_add_sheets_folder_not_found(sheet_manager: SheetManager) -> None:
    """Test adding sheets from a non-existent folder."""
    with patch("snap_fit.puzzle.sheet_manager.lg") as mock_logger:
        sheet_manager.add_sheets(Path("/non/existent/path"))
        mock_logger.error.assert_called()


# --- SegmentId integration tests ---


def test_get_segment_ids_all(
    sheet_manager: SheetManager, mock_sheet: MagicMock
) -> None:
    """Test retrieving all segment IDs from the manager."""
    sheet_manager.add_sheet(mock_sheet, "sheet_a")

    all_ids = sheet_manager.get_segment_ids_all()

    # 1 sheet * 2 pieces * 4 edges = 8 segment IDs
    assert len(all_ids) == 8

    # Check all are SegmentId instances
    assert all(isinstance(sid, SegmentId) for sid in all_ids)

    # Check sheet_id is correct
    assert all(sid.sheet_id == "sheet_a" for sid in all_ids)

    # Check both piece_ids are present
    piece_ids = {sid.piece_id_int for sid in all_ids}
    assert piece_ids == {0, 1}

    # Check all edge positions are present for each piece
    for piece_id_int in [0, 1]:
        piece_edges = {
            sid.edge_pos for sid in all_ids if sid.piece_id_int == piece_id_int
        }
        assert piece_edges == set(EdgePos)


def test_get_segment_ids_all_multiple_sheets(sheet_manager: SheetManager) -> None:
    """Test retrieving all segment IDs from multiple sheets."""
    sheet_a = create_mock_sheet("sheet_a")
    sheet_b = create_mock_sheet("sheet_b")
    sheet_manager.add_sheet(sheet_a, "sheet_a")
    sheet_manager.add_sheet(sheet_b, "sheet_b")

    all_ids = sheet_manager.get_segment_ids_all()

    # 2 sheets * 2 pieces * 4 edges = 16 segment IDs
    assert len(all_ids) == 16

    sheet_ids = {sid.sheet_id for sid in all_ids}
    assert sheet_ids == {"sheet_a", "sheet_b"}


def test_get_segment_ids_all_empty(sheet_manager: SheetManager) -> None:
    """Test retrieving segment IDs when no sheets are loaded."""
    all_ids = sheet_manager.get_segment_ids_all()
    assert all_ids == []


def test_get_segment_ids_other_pieces(
    sheet_manager: SheetManager, mock_sheet: MagicMock
) -> None:
    """Test retrieving segment IDs from other pieces."""
    sheet_manager.add_sheet(mock_sheet, "sheet_a")

    pid = PieceId(sheet_id="sheet_a", piece_id=0)
    query_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)
    other_ids = sheet_manager.get_segment_ids_other_pieces(query_id)

    # Should exclude all 4 edges of piece 0, leaving 4 edges of piece 1
    assert len(other_ids) == 4

    # None should be from piece 0 in sheet_a
    assert all(
        not (sid.sheet_id == "sheet_a" and sid.piece_id_int == 0) for sid in other_ids
    )

    # All should be from piece 1
    assert all(sid.piece_id_int == 1 for sid in other_ids)


def test_get_segment_ids_other_pieces_multiple_sheets(
    sheet_manager: SheetManager,
) -> None:
    """Test retrieving segment IDs from other pieces across multiple sheets."""
    sheet_a = create_mock_sheet("sheet_a")
    sheet_b = create_mock_sheet("sheet_b")
    sheet_manager.add_sheet(sheet_a, "sheet_a")
    sheet_manager.add_sheet(sheet_b, "sheet_b")

    pid = PieceId(sheet_id="sheet_a", piece_id=0)
    query_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)
    other_ids = sheet_manager.get_segment_ids_other_pieces(query_id)

    # Total 16, minus 4 edges of piece 0 in sheet_a = 12
    assert len(other_ids) == 12

    # Should include all segments from sheet_b
    sheet_b_ids = [sid for sid in other_ids if sid.sheet_id == "sheet_b"]
    assert len(sheet_b_ids) == 8


def test_get_segment(sheet_manager: SheetManager, mock_sheet: MagicMock) -> None:
    """Test retrieving a segment by SegmentId."""
    sheet_manager.add_sheet(mock_sheet, "sheet_a")

    pid = PieceId(sheet_id="sheet_a", piece_id=0)
    seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)
    segment = sheet_manager.get_segment(seg_id)

    assert segment is not None
    assert segment == mock_sheet.pieces[0].segments[EdgePos.LEFT]


def test_get_segment_not_found_sheet(sheet_manager: SheetManager) -> None:
    """Test retrieving a segment from a non-existent sheet."""
    pid = PieceId(sheet_id="non_existent", piece_id=0)
    seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)
    segment = sheet_manager.get_segment(seg_id)
    assert segment is None


def test_get_segment_not_found_piece(
    sheet_manager: SheetManager, mock_sheet: MagicMock
) -> None:
    """Test retrieving a segment from a non-existent piece."""
    sheet_manager.add_sheet(mock_sheet, "sheet_a")

    pid = PieceId(sheet_id="sheet_a", piece_id=999)
    seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)
    segment = sheet_manager.get_segment(seg_id)
    assert segment is None


def test_get_piece_by_segment_id(
    sheet_manager: SheetManager, mock_sheet: MagicMock
) -> None:
    """Test retrieving a piece by SegmentId."""
    sheet_manager.add_sheet(mock_sheet, "sheet_a")

    pid = PieceId(sheet_id="sheet_a", piece_id=1)
    seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.TOP)
    piece = sheet_manager.get_piece_by_segment_id(seg_id)

    assert piece is not None
    assert piece == mock_sheet.pieces[1]


def test_get_piece_by_segment_id_not_found(sheet_manager: SheetManager) -> None:
    """Test retrieving a piece from a non-existent sheet."""
    pid = PieceId(sheet_id="non_existent", piece_id=0)
    seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)
    piece = sheet_manager.get_piece_by_segment_id(seg_id)
    assert piece is None


def test_get_sheet_by_segment_id(
    sheet_manager: SheetManager, mock_sheet: MagicMock
) -> None:
    """Test retrieving a sheet by SegmentId."""
    sheet_manager.add_sheet(mock_sheet, "sheet_a")

    pid = PieceId(sheet_id="sheet_a", piece_id=0)
    seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)
    sheet = sheet_manager.get_sheet_by_segment_id(seg_id)

    assert sheet is not None
    assert sheet == mock_sheet


def test_get_sheet_by_segment_id_not_found(sheet_manager: SheetManager) -> None:
    """Test retrieving a sheet from a non-existent SegmentId."""
    pid = PieceId(sheet_id="non_existent", piece_id=0)
    seg_id = SegmentId(piece_id=pid, edge_pos=EdgePos.LEFT)
    sheet = sheet_manager.get_sheet_by_segment_id(seg_id)
    assert sheet is None


# -----------------------------------------------------------------------------
# Persistence Tests
# -----------------------------------------------------------------------------


def create_mock_sheet_for_persistence(sheet_id: str) -> MagicMock:
    """Create a mock sheet with full attributes for persistence testing."""
    sheet = MagicMock(spec=Sheet)
    sheet.sheet_id = sheet_id
    sheet.img_fp = Path(f"/data/images/{sheet_id}.jpg")
    sheet.threshold = 130
    sheet.min_area = 80_000

    # Create mock pieces with all required attributes
    pieces = []
    for i in range(2):
        piece = MagicMock(spec=Piece)
        piece.piece_id = PieceId(sheet_id=sheet_id, piece_id=i)
        piece.corners = {
            CornerPos.TOP_LEFT: (10 + i * 100, 20),
            CornerPos.TOP_RIGHT: (90 + i * 100, 25),
            CornerPos.BOTTOM_LEFT: (15 + i * 100, 110),
            CornerPos.BOTTOM_RIGHT: (95 + i * 100, 115),
        }
        piece.flat_edges = [EdgePos.TOP] if i == 0 else []
        piece.oriented_piece_type = OrientedPieceType(
            piece_type=PieceType.EDGE if i == 0 else PieceType.INNER,
            orientation=Orientation.DEG_0,
        )

        # Mock segments
        segments = {}
        shapes = [SegmentShape.IN, SegmentShape.OUT, SegmentShape.EDGE, SegmentShape.IN]
        for ep, shape in zip(EdgePos, shapes):
            seg = MagicMock(spec=Segment)
            seg.shape = shape
            segments[ep] = seg
        piece.segments = segments

        # Mock contour
        contour = MagicMock()
        contour.cv_contour = np.array([[[10, 20]], [[30, 40]], [[50, 60]]])
        contour.region = (5, 10, 100, 120)
        contour.corner_idxs = {
            CornerPos.TOP_LEFT: 0,
            CornerPos.TOP_RIGHT: 1,
            CornerPos.BOTTOM_LEFT: 2,
            CornerPos.BOTTOM_RIGHT: 0,
        }
        piece.contour = contour

        pieces.append(piece)

    sheet.pieces = pieces
    return sheet


def test_to_records(sheet_manager: SheetManager) -> None:
    """Test exporting sheets to records."""
    sheet = create_mock_sheet_for_persistence("test_sheet")
    sheet_manager.add_sheet(sheet, "test_sheet")

    records = sheet_manager.to_records()

    assert "sheets" in records
    assert "pieces" in records
    assert len(records["sheets"]) == 1
    assert len(records["pieces"]) == 2
    assert records["sheets"][0]["sheet_id"] == "test_sheet"
    assert records["pieces"][0]["piece_id"]["sheet_id"] == "test_sheet"


def test_to_records_with_data_root(sheet_manager: SheetManager) -> None:
    """Test exporting with relative paths."""
    sheet = create_mock_sheet_for_persistence("test_sheet")
    sheet.img_fp = Path("/data/root/images/test_sheet.jpg")
    sheet_manager.add_sheet(sheet, "test_sheet")

    data_root = Path("/data/root")
    records = sheet_manager.to_records(data_root=data_root)

    assert records["sheets"][0]["img_path"] == "images/test_sheet.jpg"


def test_save_metadata(sheet_manager: SheetManager, tmp_path: Path) -> None:
    """Test saving metadata to JSON."""
    sheet = create_mock_sheet_for_persistence("sheet_a")
    sheet_manager.add_sheet(sheet, "sheet_a")

    output_path = tmp_path / "metadata.json"
    sheet_manager.save_metadata(output_path)

    assert output_path.exists()
    data = json.loads(output_path.read_text())
    assert len(data["sheets"]) == 1
    assert len(data["pieces"]) == 2


def test_save_metadata_creates_parent_dirs(
    sheet_manager: SheetManager, tmp_path: Path
) -> None:
    """Test that save_metadata creates parent directories."""
    sheet = create_mock_sheet_for_persistence("sheet_a")
    sheet_manager.add_sheet(sheet, "sheet_a")

    output_path = tmp_path / "nested" / "dir" / "metadata.json"
    sheet_manager.save_metadata(output_path)

    assert output_path.exists()


def test_save_contour_cache(sheet_manager: SheetManager, tmp_path: Path) -> None:
    """Test saving contour cache."""
    sheet = create_mock_sheet_for_persistence("test_sheet")
    sheet_manager.add_sheet(sheet, "test_sheet")

    cache_dir = tmp_path / "cache"
    sheet_manager.save_contour_cache(cache_dir)

    # Check files were created
    npz_file = cache_dir / "test_sheet_contours.npz"
    json_file = cache_dir / "test_sheet_corners.json"
    assert npz_file.exists()
    assert json_file.exists()

    # Verify npz content
    with np.load(npz_file) as data:
        keys = list(data.keys())
        assert len(keys) == 2  # Two pieces

    # Verify json content
    corners_data = json.loads(json_file.read_text())
    assert len(corners_data) == 2  # Two pieces


def test_load_metadata(sheet_manager: SheetManager, tmp_path: Path) -> None:
    """Test loading metadata from JSON."""
    # Create a metadata file
    metadata = {
        "sheets": [
            {
                "sheet_id": "sheet_x",
                "img_path": "images/sheet_x.jpg",
                "piece_count": 3,
                "threshold": 140,
                "min_area": 90000,
                "created_at": "2024-01-15T10:00:00",
            }
        ],
        "pieces": [
            {
                "piece_id": {"sheet_id": "sheet_x", "piece_id": 0},
                "corners": {"top_left": [10, 20]},
                "segment_shapes": {"left": "in"},
                "oriented_piece_type": None,
                "flat_edges": [],
                "contour_point_count": 100,
                "contour_region": [0, 0, 50, 50],
            }
        ],
    }
    input_path = tmp_path / "metadata.json"
    input_path.write_text(json.dumps(metadata))

    loaded = SheetManager.load_metadata(input_path)

    assert len(loaded["sheets"]) == 1
    assert len(loaded["pieces"]) == 1
    assert loaded["sheets"][0]["sheet_id"] == "sheet_x"


def test_load_contour_for_piece(sheet_manager: SheetManager, tmp_path: Path) -> None:
    """Test loading contour for a specific piece."""
    # Create cache files
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    piece_id = PieceId(sheet_id="sheet_a", piece_id=0)
    contour_points = np.array([[[10, 20]], [[30, 40]], [[50, 60]]])

    # Save npz
    np.savez_compressed(
        cache_dir / "sheet_a_contours.npz", **{f"contour_{piece_id}": contour_points}
    )

    # Save corners json
    corners = {
        str(piece_id): {
            "top_left": 0,
            "top_right": 1,
            "bottom_left": 2,
            "bottom_right": 0,
        }
    }
    (cache_dir / "sheet_a_corners.json").write_text(json.dumps(corners))

    # Load and verify
    loaded_contour, loaded_corners = SheetManager.load_contour_for_piece(
        piece_id, cache_dir
    )

    np.testing.assert_array_equal(loaded_contour, contour_points)
    assert loaded_corners["top_left"] == 0
    assert loaded_corners["bottom_left"] == 2


def test_load_contour_for_piece_not_found(tmp_path: Path) -> None:
    """Test loading contour when file doesn't exist."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    piece_id = PieceId(sheet_id="nonexistent", piece_id=0)

    with pytest.raises(FileNotFoundError):
        SheetManager.load_contour_for_piece(piece_id, cache_dir)


def test_save_load_metadata_round_trip(
    sheet_manager: SheetManager, tmp_path: Path
) -> None:
    """Test full round-trip of save and load metadata."""
    sheet = create_mock_sheet_for_persistence("round_trip_sheet")
    sheet_manager.add_sheet(sheet, "round_trip_sheet")

    output_path = tmp_path / "metadata.json"
    sheet_manager.save_metadata(output_path)

    loaded = SheetManager.load_metadata(output_path)

    # Verify structure
    assert len(loaded["sheets"]) == 1
    assert len(loaded["pieces"]) == 2
    assert loaded["sheets"][0]["sheet_id"] == "round_trip_sheet"
    assert loaded["sheets"][0]["piece_count"] == 2
    assert loaded["pieces"][0]["contour_point_count"] == 3  # From mock contour
