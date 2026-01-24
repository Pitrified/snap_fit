"""Match result data model."""

from pydantic import BaseModel
from pydantic import Field

from snap_fit.data_models.segment_id import SegmentId


class MatchResult(BaseModel):
    """Result of matching two segments."""

    seg_id1: SegmentId
    seg_id2: SegmentId
    similarity: float
    similarity_manual_: float | None = Field(default=None, alias="similarity_manual")

    @property
    def pair(self) -> frozenset[SegmentId]:
        """Get the segment IDs as a frozenset for symmetric lookup."""
        return frozenset({self.seg_id1, self.seg_id2})

    def get_other(self, seg_id: SegmentId) -> SegmentId:
        """Get the other segment ID in the match."""
        if seg_id == self.seg_id1:
            return self.seg_id2
        if seg_id == self.seg_id2:
            return self.seg_id1
        msg = f"SegmentId {seg_id} not in this match result"
        raise ValueError(msg)

    @property
    def similarity_manual(self) -> float:
        """Get the manually adjusted similarity, or default to computed similarity."""
        return (
            self.similarity_manual_
            if self.similarity_manual_ is not None
            else self.similarity
        )

    @similarity_manual.setter
    def similarity_manual(self, value: float | None) -> None:
        self.similarity_manual_ = value
