"""Sheet identity metadata model for QR code embedding."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import cv2
from loguru import logger as lg
import numpy as np
from pydantic import Field
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from qrcode.constants import ERROR_CORRECT_L
from qrcode.constants import ERROR_CORRECT_M
from qrcode.constants import ERROR_CORRECT_Q

from snap_fit.data_models.basemodel_kwargs import BaseModelKwargs

if TYPE_CHECKING:
    from snap_fit.config.aruco.aruco_board_config import ArucoBoardConfig
    from snap_fit.config.aruco.metadata_zone_config import MetadataZoneConfig

_ECC_MAP: dict[str, int] = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}

# opencv ndim value for BGR images
_BGR_NDIM: int = 3


class SheetMetadata(BaseModelKwargs):
    """Identity metadata for a single printed puzzle sheet.

    Attributes:
        tag_name: Dataset tag, e.g. "oca" or "milano1".
        sheet_index: Zero-based index within the print run.
        total_sheets: Total sheets in the print run; may be unknown at print time.
        board_config_id: Matches data/aruco_boards/{id}/.
        printed_at: Date the board was printed.
    """

    tag_name: str
    sheet_index: int
    total_sheets: int | None = None
    board_config_id: str
    printed_at: date = Field(default_factory=date.today)

    def to_qr_payload(self) -> str:
        """Encode to compact CSV: 'oca,2,6,oca,20250115'."""
        ts = str(self.total_sheets) if self.total_sheets is not None else ""
        date_str = f"{self.printed_at:%Y%m%d}"
        parts = [
            self.tag_name,
            str(self.sheet_index),
            ts,
            self.board_config_id,
            date_str,
        ]
        return ",".join(parts)

    @classmethod
    def from_qr_payload(cls, s: str) -> SheetMetadata:
        """Decode from compact CSV payload string.

        Args:
            s: CSV string produced by to_qr_payload().

        Returns:
            Reconstructed SheetMetadata instance.
        """
        parts = s.split(",")
        return cls(
            tag_name=parts[0],
            sheet_index=int(parts[1]),
            total_sheets=int(parts[2]) if parts[2] else None,
            board_config_id=parts[3],
            printed_at=date(int(parts[4][:4]), int(parts[4][4:6]), int(parts[4][6:8])),
        )


class QRChunkHandler:
    """Encodes/decodes a payload across N identical QR images.

    All N codes carry the full payload for redundancy. Decode succeeds on any
    single readable code. Chunked split-and-reconstruct is explicitly deferred.

    Attributes:
        n_codes: Number of identical QR images to generate.
        ecc: Error correction level - one of 'L', 'M', 'Q', 'H'.
    """

    def __init__(self, n_codes: int = 3, ecc: str = "M") -> None:
        """Initialise with code count and error correction level."""
        if ecc not in _ECC_MAP:
            msg = f"ecc must be one of {list(_ECC_MAP)}; got {ecc!r}"
            raise ValueError(msg)
        self.n_codes = n_codes
        self.ecc = ecc

    def encode(self, payload: str) -> list[np.ndarray]:
        """Return a list of n_codes identical QR code images.

        Args:
            payload: String to encode into each QR code.

        Returns:
            List of n_codes uint8 grayscale numpy arrays (white=255, black=0).
        """
        qr = qrcode.QRCode(
            error_correction=_ECC_MAP[self.ecc],
            box_size=7,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        pil_img = qr.make_image(fill_color="black", back_color="white")
        arr = np.array(pil_img.get_image().convert("L"), dtype=np.uint8)
        return [arr.copy() for _ in range(self.n_codes)]

    def decode_first(self, image: np.ndarray) -> str | None:
        """Detect and decode any QR code present in image.

        Args:
            image: Grayscale or BGR numpy array containing at least one QR code.

        Returns:
            Decoded payload string, or None if no readable QR code is found.
        """
        # detectMulti handles multiple (or small) codes in large images better
        # than the single detectAndDecode path.
        detector = cv2.QRCodeDetector()
        detected, points = detector.detectMulti(image)
        if detected and points is not None:
            ok, decoded, _ = detector.decodeMulti(image, points)
            if ok and decoded:
                first = next((t for t in decoded if t), None)
                if first:
                    return first
        # WeChatQRCode provides a robust fallback for challenging cases.
        try:
            wechat = cv2.wechat_qrcode_WeChatQRCode()  # type: ignore[attr-defined]
            texts, _ = wechat.detectAndDecode(image)
            if texts:
                return texts[0]
        except (cv2.error, AttributeError):
            pass
        return None


class SheetMetadataEncoder:
    """Renders QR codes and human-readable text onto a board image.

    The QR strip occupies the bottom interior band of the board, symmetric
    with the ArUco ring band at the top. Text is placed as a single line
    just above the strip.
    """

    def __init__(self, board_config: ArucoBoardConfig) -> None:
        """Initialise with the board geometry configuration.

        Args:
            board_config: ArUco board config used to derive strip coordinates.
        """
        self.board_config = board_config

    def _strip_region(self) -> tuple[int, int, int, int]:
        """Return (x0, y0, x1, y1) of the QR strip in board pixel coordinates."""
        board_w, board_h = self.board_config.board_dimensions()
        ring_start = self.board_config.margin + self.board_config.marker_length
        x0 = ring_start
        x1 = board_w - self.board_config.marker_length
        y1 = board_h - self.board_config.marker_length
        y0 = y1 - ring_start
        return (x0, y0, x1, y1)

    def render(
        self,
        board_img: np.ndarray,
        metadata: SheetMetadata,
        config: MetadataZoneConfig,
    ) -> np.ndarray:
        """Return a copy of board_img with QR strip and text rendered.

        Args:
            board_img: Source board image (grayscale or BGR).
            metadata: Sheet identity to encode.
            config: QR strip and text rendering parameters.

        Returns:
            Modified copy of board_img.
        """
        if not config.enabled:
            return board_img.copy()

        img = board_img.copy()
        payload = metadata.to_qr_payload()
        handler = QRChunkHandler(n_codes=config.qr_n_codes, ecc=config.qr_ecc)
        qr_images = handler.encode(payload)
        strip = self._strip_region()
        self._place_qr_codes(img, qr_images, strip)
        if config.text_enabled:
            self._place_text(img, metadata, strip)
        return img

    def _place_qr_codes(
        self,
        img: np.ndarray,
        qr_images: list[np.ndarray],
        strip_region: tuple[int, int, int, int],
    ) -> None:
        """Place QR images evenly spaced inside the strip region."""
        x0, y0, x1, y1 = strip_region
        strip_h = y1 - y0
        strip_w = x1 - x0
        n = len(qr_images)
        total_qr = n * strip_h
        gap = max(0, (strip_w - total_qr) // (n + 1))
        is_color = img.ndim == _BGR_NDIM
        for i, qr_raw in enumerate(qr_images):
            qr_resized = cv2.resize(
                qr_raw, (strip_h, strip_h), interpolation=cv2.INTER_AREA
            )
            x_start = x0 + gap + i * (strip_h + gap)
            if x_start + strip_h > x1:
                break
            if is_color:
                img[y0:y1, x_start : x_start + strip_h] = cv2.cvtColor(
                    qr_resized, cv2.COLOR_GRAY2BGR
                )
            else:
                img[y0:y1, x_start : x_start + strip_h] = qr_resized

    def _place_text(
        self,
        img: np.ndarray,
        metadata: SheetMetadata,
        strip_region: tuple[int, int, int, int],
    ) -> None:
        """Render a human-readable identity line just above the QR strip."""
        x0, y0, _x1, _y1 = strip_region
        ts = "??" if metadata.total_sheets is None else f"{metadata.total_sheets:02d}"
        text = (
            f"{metadata.tag_name}  "
            f"{metadata.sheet_index + 1:02d}/{ts}  "
            f"{metadata.printed_at:%Y-%m-%d}"
        )
        # Use (0, 0, 0) for putText - OpenCV uses the first channel for grayscale.
        cv2.putText(
            img,
            text,
            (x0, y0 - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )


class SheetMetadataDecoder:
    """Extracts SheetMetadata from a raw (pre-rectified) photo."""

    def decode(self, image: np.ndarray) -> SheetMetadata | None:
        """Try to decode metadata from image. Returns None with a warning if not found.

        Args:
            image: Grayscale or BGR numpy array of the board photo.

        Returns:
            Decoded SheetMetadata, or None if no readable QR code is found.
        """
        handler = QRChunkHandler()
        payload = handler.decode_first(image)
        if payload is None:
            lg.warning("No QR code found in image")
            return None
        try:
            return SheetMetadata.from_qr_payload(payload)
        except (ValueError, IndexError):
            lg.warning("QR payload could not be parsed: %r", payload)
            return None
