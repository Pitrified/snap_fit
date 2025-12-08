"""Tests for the SheetManager class."""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

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
    sheet.pieces = [MagicMock(spec=Piece), MagicMock(spec=Piece)]
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
