"""Tests for SheetMetadata model."""

from datetime import UTC
from datetime import date
from datetime import datetime

import pytest

from snap_fit.aruco.sheet_metadata import SheetMetadata


@pytest.fixture
def typical_metadata() -> SheetMetadata:
    """Typical SheetMetadata for a known print run."""
    return SheetMetadata(
        tag_name="oca",
        sheet_index=1,
        total_sheets=6,
        board_config_id="oca",
        printed_at=date(2025, 1, 15),
    )


def test_to_qr_payload(typical_metadata: SheetMetadata) -> None:
    """Payload matches expected CSV format."""
    assert typical_metadata.to_qr_payload() == "oca,1,6,oca,20250115"


def test_round_trip(typical_metadata: SheetMetadata) -> None:
    """from_qr_payload(to_qr_payload()) recovers the original model."""
    recovered = SheetMetadata.from_qr_payload(typical_metadata.to_qr_payload())
    assert recovered == typical_metadata


def test_total_sheets_none_round_trip() -> None:
    """total_sheets=None is encoded as empty field and decoded back to None."""
    meta = SheetMetadata(
        tag_name="oca",
        sheet_index=0,
        total_sheets=None,
        board_config_id="oca",
        printed_at=date(2025, 1, 15),
    )
    payload = meta.to_qr_payload()
    assert ",,oca," in payload  # empty total_sheets field
    recovered = SheetMetadata.from_qr_payload(payload)
    assert recovered.total_sheets is None
    assert recovered == meta


def test_single_char_tag_round_trip() -> None:
    """Single-character tag name survives round-trip."""
    meta = SheetMetadata(
        tag_name="x",
        sheet_index=0,
        total_sheets=1,
        board_config_id="x",
        printed_at=date(2026, 4, 10),
    )
    assert SheetMetadata.from_qr_payload(meta.to_qr_payload()) == meta


def test_payload_size_typical(typical_metadata: SheetMetadata) -> None:
    """Typical payload fits within 26 bytes (QR V2 ECC-M capacity)."""
    assert len(typical_metadata.to_qr_payload().encode()) <= 26


def test_printed_at_defaults_to_today() -> None:
    """printed_at defaults to today when not supplied."""
    meta = SheetMetadata(
        tag_name="oca",
        sheet_index=0,
        board_config_id="oca",
    )
    assert meta.printed_at == datetime.now(tz=UTC).date()
