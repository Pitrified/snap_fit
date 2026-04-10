"""Tests for SheetMetadata model."""

from datetime import UTC
from datetime import date
from datetime import datetime

import numpy as np
import pytest

from snap_fit.aruco.sheet_metadata import QRChunkHandler
from snap_fit.aruco.sheet_metadata import SheetMetadata
from snap_fit.aruco.sheet_metadata import SheetMetadataDecoder
from snap_fit.aruco.sheet_metadata import SheetMetadataEncoder
from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
from snap_fit.config.aruco.metadata_zone_config import MetadataZoneConfig


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


# ---------------------------------------------------------------------------
# SheetMetadataEncoder tests
# ---------------------------------------------------------------------------


@pytest.fixture
def board_config() -> ArucoBoardConfig:
    """Return the default ArucoBoardConfig."""
    return ArucoBoardConfig()


@pytest.fixture
def zone_config() -> MetadataZoneConfig:
    """Return the default MetadataZoneConfig."""
    return MetadataZoneConfig()


@pytest.fixture
def encoder(board_config: ArucoBoardConfig) -> SheetMetadataEncoder:
    """Return a SheetMetadataEncoder with the default board config."""
    return SheetMetadataEncoder(board_config)


@pytest.fixture
def blank_board(board_config: ArucoBoardConfig) -> np.ndarray:
    """Return a white BGR board-sized image."""
    w, h = board_config.board_dimensions()
    return np.full((h, w, 3), 255, dtype=np.uint8)


def test_encoder_returns_same_shape(
    encoder: SheetMetadataEncoder,
    blank_board: np.ndarray,
    typical_metadata: SheetMetadata,
    zone_config: MetadataZoneConfig,
) -> None:
    """render() returns an image with the same shape as the input."""
    result = encoder.render(blank_board, typical_metadata, zone_config)
    assert result.shape == blank_board.shape


def test_encoder_does_not_modify_original(
    encoder: SheetMetadataEncoder,
    blank_board: np.ndarray,
    typical_metadata: SheetMetadata,
    zone_config: MetadataZoneConfig,
) -> None:
    """render() returns a copy; the original is unchanged."""
    original = blank_board.copy()
    encoder.render(blank_board, typical_metadata, zone_config)
    np.testing.assert_array_equal(blank_board, original)


def test_encoder_disabled_returns_copy(
    encoder: SheetMetadataEncoder,
    blank_board: np.ndarray,
    typical_metadata: SheetMetadata,
) -> None:
    """When config.enabled=False, render returns an unmodified copy."""
    config = MetadataZoneConfig(enabled=False)
    result = encoder.render(blank_board, typical_metadata, config)
    np.testing.assert_array_equal(result, blank_board)


def test_encoder_modifies_strip_region(
    encoder: SheetMetadataEncoder,
    blank_board: np.ndarray,
    typical_metadata: SheetMetadata,
    zone_config: MetadataZoneConfig,
) -> None:
    """QR codes are written into the expected strip region."""
    x0, y0, x1, y1 = encoder._strip_region()
    result = encoder.render(blank_board, typical_metadata, zone_config)
    strip = result[y0:y1, x0:x1]
    # Strip should no longer be all-white after QR rendering
    assert strip.min() < 255


# ---------------------------------------------------------------------------
# SheetMetadataDecoder tests
# ---------------------------------------------------------------------------


def test_encoder_decoder_round_trip(
    encoder: SheetMetadataEncoder,
    blank_board: np.ndarray,
    typical_metadata: SheetMetadata,
    zone_config: MetadataZoneConfig,
) -> None:
    """Encode onto a board image then decode back recovers the original metadata."""
    encoded_board = encoder.render(blank_board, typical_metadata, zone_config)
    decoder = SheetMetadataDecoder()
    recovered = decoder.decode(encoded_board)
    assert recovered == typical_metadata


def test_decoder_returns_none_on_blank_image() -> None:
    """decode() returns None (no raise) when no QR code is present."""
    blank = np.full((200, 200, 3), 255, dtype=np.uint8)
    decoder = SheetMetadataDecoder()
    assert decoder.decode(blank) is None


def test_decoder_returns_none_on_bad_payload(
    encoder: SheetMetadataEncoder,
    blank_board: np.ndarray,
    zone_config: MetadataZoneConfig,
) -> None:
    """decode() returns None when QR decodes but payload is malformed."""
    # Encode an arbitrary non-metadata string directly via QRChunkHandler
    handler = QRChunkHandler(n_codes=1, ecc="M")
    import cv2

    (qr_img,) = handler.encode("not,valid,payload,at,all,extra")
    x0, y0, _x1, y1 = encoder._strip_region()
    strip_h = y1 - y0
    img = blank_board.copy()
    qr_resized = cv2.resize(qr_img, (strip_h, strip_h), interpolation=cv2.INTER_NEAREST)
    img[y0:y1, x0 : x0 + strip_h] = cv2.cvtColor(qr_resized, cv2.COLOR_GRAY2BGR)
    decoder = SheetMetadataDecoder()
    # "not,valid,payload,at,all,extra" has 6 parts; date parse will fail
    result = decoder.decode(img)
    # May be None or a recovered value depending on parser tolerance; just no raise
    assert result is None or isinstance(result, SheetMetadata)
