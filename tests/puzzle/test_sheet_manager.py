"""Tests for the SheetManager class."""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from snap_fit.config.types import EdgePos
from snap_fit.data_models.segment_id import SegmentId
from snap_fit.image.segment import Segment
from snap_fit.puzzle.piece import Piece
from snap_fit.puzzle.sheet import Sheet
from snap_fit.puzzle.sheet_manager import SheetManager


@pytest.fixture
def sheet_manager() -> SheetManager:
    """Fixture for creating a SheetManager instance."""
    return SheetManager()


@pytest.fixture
def mock_sheet() -> MagicMock:
    """Fixture for creating a mock Sheet."""
    sheet = MagicMock(spec=Sheet)
    # Create mock pieces with piece_id attributes
    piece0 = MagicMock(spec=Piece)
    piece0.piece_id = 0
    piece0.segments = {
        EdgePos.LEFT: MagicMock(spec=Segment),
        EdgePos.BOTTOM: MagicMock(spec=Segment),
        EdgePos.RIGHT: MagicMock(spec=Segment),
        EdgePos.TOP: MagicMock(spec=Segment),
    }
    piece1 = MagicMock(spec=Piece)
    piece1.piece_id = 1
    piece1.segments = {
        EdgePos.LEFT: MagicMock(spec=Segment),
        EdgePos.BOTTOM: MagicMock(spec=Segment),
        EdgePos.RIGHT: MagicMock(spec=Segment),
        EdgePos.TOP: MagicMock(spec=Segment),
    }
    sheet.pieces = [piece0, piece1]
    return sheet


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


def test_get_sheets_ls(sheet_manager: SheetManager, mock_sheet: MagicMock) -> None:
    """Test retrieving all sheets as a list."""
    sheet_manager.add_sheet(mock_sheet, "sheet1")
    sheet_manager.add_sheet(mock_sheet, "sheet2")

    sheets_ls = sheet_manager.get_sheets_ls()
    assert len(sheets_ls) == 2
    assert mock_sheet in sheets_ls


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
    mock_loader.return_value = MagicMock(spec=Sheet)

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
    piece_ids = {sid.piece_id for sid in all_ids}
    assert piece_ids == {0, 1}

    # Check all edge positions are present for each piece
    for piece_id in [0, 1]:
        piece_edges = {sid.edge_pos for sid in all_ids if sid.piece_id == piece_id}
        assert piece_edges == set(EdgePos)


def test_get_segment_ids_all_multiple_sheets(
    sheet_manager: SheetManager, mock_sheet: MagicMock
) -> None:
    """Test retrieving all segment IDs from multiple sheets."""
    sheet_manager.add_sheet(mock_sheet, "sheet_a")
    sheet_manager.add_sheet(mock_sheet, "sheet_b")

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

    query_id = SegmentId(sheet_id="sheet_a", piece_id=0, edge_pos=EdgePos.LEFT)
    other_ids = sheet_manager.get_segment_ids_other_pieces(query_id)

    # Should exclude all 4 edges of piece 0, leaving 4 edges of piece 1
    assert len(other_ids) == 4

    # None should be from piece 0 in sheet_a
    assert all(
        not (sid.sheet_id == "sheet_a" and sid.piece_id == 0) for sid in other_ids
    )

    # All should be from piece 1
    assert all(sid.piece_id == 1 for sid in other_ids)


def test_get_segment_ids_other_pieces_multiple_sheets(
    sheet_manager: SheetManager, mock_sheet: MagicMock
) -> None:
    """Test retrieving segment IDs from other pieces across multiple sheets."""
    sheet_manager.add_sheet(mock_sheet, "sheet_a")
    sheet_manager.add_sheet(mock_sheet, "sheet_b")

    query_id = SegmentId(sheet_id="sheet_a", piece_id=0, edge_pos=EdgePos.LEFT)
    other_ids = sheet_manager.get_segment_ids_other_pieces(query_id)

    # Total 16, minus 4 edges of piece 0 in sheet_a = 12
    assert len(other_ids) == 12

    # Should include all segments from sheet_b
    sheet_b_ids = [sid for sid in other_ids if sid.sheet_id == "sheet_b"]
    assert len(sheet_b_ids) == 8


def test_get_segment(sheet_manager: SheetManager, mock_sheet: MagicMock) -> None:
    """Test retrieving a segment by SegmentId."""
    sheet_manager.add_sheet(mock_sheet, "sheet_a")

    seg_id = SegmentId(sheet_id="sheet_a", piece_id=0, edge_pos=EdgePos.LEFT)
    segment = sheet_manager.get_segment(seg_id)

    assert segment is not None
    assert segment == mock_sheet.pieces[0].segments[EdgePos.LEFT]


def test_get_segment_not_found_sheet(sheet_manager: SheetManager) -> None:
    """Test retrieving a segment from a non-existent sheet."""
    seg_id = SegmentId(sheet_id="non_existent", piece_id=0, edge_pos=EdgePos.LEFT)
    segment = sheet_manager.get_segment(seg_id)
    assert segment is None


def test_get_segment_not_found_piece(
    sheet_manager: SheetManager, mock_sheet: MagicMock
) -> None:
    """Test retrieving a segment from a non-existent piece."""
    sheet_manager.add_sheet(mock_sheet, "sheet_a")

    seg_id = SegmentId(sheet_id="sheet_a", piece_id=999, edge_pos=EdgePos.LEFT)
    segment = sheet_manager.get_segment(seg_id)
    assert segment is None


def test_get_piece_by_segment_id(
    sheet_manager: SheetManager, mock_sheet: MagicMock
) -> None:
    """Test retrieving a piece by SegmentId."""
    sheet_manager.add_sheet(mock_sheet, "sheet_a")

    seg_id = SegmentId(sheet_id="sheet_a", piece_id=1, edge_pos=EdgePos.TOP)
    piece = sheet_manager.get_piece_by_segment_id(seg_id)

    assert piece is not None
    assert piece == mock_sheet.pieces[1]


def test_get_piece_by_segment_id_not_found(sheet_manager: SheetManager) -> None:
    """Test retrieving a piece from a non-existent sheet."""
    seg_id = SegmentId(sheet_id="non_existent", piece_id=0, edge_pos=EdgePos.LEFT)
    piece = sheet_manager.get_piece_by_segment_id(seg_id)
    assert piece is None


def test_get_sheet_by_segment_id(
    sheet_manager: SheetManager, mock_sheet: MagicMock
) -> None:
    """Test retrieving a sheet by SegmentId."""
    sheet_manager.add_sheet(mock_sheet, "sheet_a")

    seg_id = SegmentId(sheet_id="sheet_a", piece_id=0, edge_pos=EdgePos.LEFT)
    sheet = sheet_manager.get_sheet_by_segment_id(seg_id)

    assert sheet is not None
    assert sheet == mock_sheet


def test_get_sheet_by_segment_id_not_found(sheet_manager: SheetManager) -> None:
    """Test retrieving a sheet from a non-existent SegmentId."""
    seg_id = SegmentId(sheet_id="non_existent", piece_id=0, edge_pos=EdgePos.LEFT)
    sheet = sheet_manager.get_sheet_by_segment_id(seg_id)
    assert sheet is None
