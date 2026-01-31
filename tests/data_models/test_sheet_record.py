"""Tests for the SheetRecord data model."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from snap_fit.data_models.sheet_record import SheetRecord


class TestSheetRecordBasics:
    """Test basic SheetRecord functionality."""

    def test_create_sheet_record(self) -> None:
        """Test creating a SheetRecord with all fields."""
        record = SheetRecord(
            sheet_id="sheet_01",
            img_path=Path("images/sheet_01.jpg"),
            piece_count=12,
            threshold=130,
            min_area=80_000,
        )

        assert record.sheet_id == "sheet_01"
        assert record.img_path == Path("images/sheet_01.jpg")
        assert record.piece_count == 12
        assert record.threshold == 130
        assert record.min_area == 80_000
        assert isinstance(record.created_at, datetime)

    def test_create_with_defaults(self) -> None:
        """Test creating a SheetRecord with default values."""
        record = SheetRecord(
            sheet_id="sheet_01",
            img_path=Path("sheet.jpg"),
            piece_count=10,
        )

        assert record.threshold == 130
        assert record.min_area == 80_000

    def test_serialization(self) -> None:
        """Test JSON serialization."""
        record = SheetRecord(
            sheet_id="sheet_01",
            img_path=Path("images/sheet.jpg"),
            piece_count=5,
        )

        data = record.model_dump(mode="json")

        assert data["sheet_id"] == "sheet_01"
        assert data["img_path"] == "images/sheet.jpg"
        assert data["piece_count"] == 5
        assert "created_at" in data

    def test_deserialization(self) -> None:
        """Test JSON deserialization."""
        data = {
            "sheet_id": "sheet_02",
            "img_path": "data/sheet_02.png",
            "piece_count": 8,
            "threshold": 140,
            "min_area": 100_000,
            "created_at": "2024-01-15T10:30:00",
        }

        record = SheetRecord.model_validate(data)

        assert record.sheet_id == "sheet_02"
        assert record.img_path == Path("data/sheet_02.png")
        assert record.piece_count == 8
        assert record.threshold == 140
        assert record.min_area == 100_000


class TestSheetRecordFromSheet:
    """Test SheetRecord.from_sheet class method."""

    def test_from_sheet_basic(self) -> None:
        """Test creating SheetRecord from a Sheet mock."""
        mock_sheet = MagicMock()
        mock_sheet.sheet_id = "test_sheet"
        mock_sheet.img_fp = Path("/data/root/images/test.jpg")
        mock_sheet.pieces = [MagicMock(), MagicMock(), MagicMock()]
        mock_sheet.threshold = 125
        mock_sheet.min_area = 90_000

        record = SheetRecord.from_sheet(mock_sheet)

        assert record.sheet_id == "test_sheet"
        assert record.img_path == Path("/data/root/images/test.jpg")
        assert record.piece_count == 3
        assert record.threshold == 125
        assert record.min_area == 90_000

    def test_from_sheet_with_data_root(self) -> None:
        """Test creating SheetRecord with relative path."""
        mock_sheet = MagicMock()
        mock_sheet.sheet_id = "sheet_a"
        mock_sheet.img_fp = Path("/data/root/images/sheet_a.jpg")
        mock_sheet.pieces = [MagicMock()]
        mock_sheet.threshold = 130
        mock_sheet.min_area = 80_000

        data_root = Path("/data/root")
        record = SheetRecord.from_sheet(mock_sheet, data_root=data_root)

        assert record.img_path == Path("images/sheet_a.jpg")

    def test_from_sheet_data_root_not_parent(self) -> None:
        """Test when data_root is not a parent of img_fp."""
        mock_sheet = MagicMock()
        mock_sheet.sheet_id = "external"
        mock_sheet.img_fp = Path("/other/path/image.jpg")
        mock_sheet.pieces = []
        mock_sheet.threshold = 130
        mock_sheet.min_area = 80_000

        data_root = Path("/data/root")
        record = SheetRecord.from_sheet(mock_sheet, data_root=data_root)

        # Should keep absolute path when relative_to fails
        assert record.img_path == Path("/other/path/image.jpg")
