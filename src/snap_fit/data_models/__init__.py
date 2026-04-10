"""Data models for snap_fit."""

from snap_fit.data_models.match_result import MatchResult
from snap_fit.data_models.piece_id import PieceId
from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.data_models.segment_id import SegmentId

# SheetRecord is lazy-loaded to avoid a circular import:
# sheet_record imports SheetMetadata from aruco.sheet_metadata, which itself
# imports data_models.basemodel_kwargs, triggering this __init__.py.
# Python 3.7+ module __getattr__ defers the import until first access.


def __getattr__(name: str) -> object:
    if name == "SheetRecord":
        from snap_fit.data_models.sheet_record import SheetRecord  # noqa: PLC0415

        return SheetRecord
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__ = ["MatchResult", "PieceId", "PieceRecord", "SegmentId", "SheetRecord"]
