"""Sheet identity metadata model for QR code embedding."""

from datetime import date

import cv2
import numpy as np
from pydantic import Field
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from qrcode.constants import ERROR_CORRECT_L
from qrcode.constants import ERROR_CORRECT_M
from qrcode.constants import ERROR_CORRECT_Q

from snap_fit.data_models.basemodel_kwargs import BaseModelKwargs

_ECC_MAP: dict[str, int] = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


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
    def from_qr_payload(cls, s: str) -> "SheetMetadata":
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
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(image)
        if data:
            return data
        return None
