"""Sheet identity metadata model for QR code embedding."""

from datetime import date

from pydantic import Field

from snap_fit.data_models.basemodel_kwargs import BaseModelKwargs


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
