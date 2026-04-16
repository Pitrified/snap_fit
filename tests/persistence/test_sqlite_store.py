"""Tests for DatasetStore (SQLite persistence)."""

from datetime import UTC
from datetime import datetime
from pathlib import Path
import sqlite3

import pytest

from snap_fit.aruco.sheet_metadata import SheetMetadata
from snap_fit.config.types import EdgePos
from snap_fit.data_models.match_result import MatchResult
from snap_fit.data_models.piece_id import PieceId
from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.data_models.segment_id import SegmentId
from snap_fit.data_models.sheet_record import SheetRecord
from snap_fit.grid.orientation import Orientation
from snap_fit.grid.orientation import OrientedPieceType
from snap_fit.grid.orientation import PieceType
from snap_fit.persistence.sqlite_store import DatasetStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CORNERS = {
    "top_left": (10, 20),
    "bottom_left": (10, 80),
    "bottom_right": (90, 80),
    "top_right": (90, 20),
}

_SEGMENT_SHAPES = {
    "left": "out",
    "bottom": "in",
    "right": "out",
    "top": "edge",
}


def _make_sheet(n: int, *, with_metadata: bool = False) -> SheetRecord:
    metadata = None
    if with_metadata:
        metadata = SheetMetadata(
            tag_name="oca",
            sheet_index=n,
            total_sheets=3,
            board_config_id="oca",
        )
    return SheetRecord(
        sheet_id=f"sheet_{n}.jpg",
        img_path=Path(f"data/sheet_{n}.jpg"),
        piece_count=n + 1,
        threshold=130,
        min_area=80_000,
        created_at=datetime(2026, 1, n + 1, tzinfo=UTC),
        metadata=metadata,
    )


def _make_piece(
    sheet_id: str,
    piece_idx: int,
    *,
    with_opt: bool = False,
    label: str | None = None,
    sheet_origin: tuple[int, int] = (0, 0),
    padded_size: tuple[int, int] = (0, 0),
) -> PieceRecord:
    opt = None
    if with_opt:
        opt = OrientedPieceType(
            piece_type=PieceType.EDGE, orientation=Orientation.DEG_0
        )
    return PieceRecord(
        piece_id=PieceId(sheet_id=sheet_id, piece_id=piece_idx),
        corners=_CORNERS,
        segment_shapes=_SEGMENT_SHAPES,
        oriented_piece_type=opt,
        flat_edges=["top"],
        contour_point_count=500,
        contour_region=(10, 20, 80, 60),
        label=label,
        sheet_origin=sheet_origin,
        padded_size=padded_size,
    )


def _make_match(
    sid1: str,
    pid1: int,
    ep1: EdgePos,
    sid2: str,
    pid2: int,
    ep2: EdgePos,
    sim: float,
    sim_manual: float | None = None,
) -> MatchResult:
    seg1 = SegmentId(piece_id=PieceId(sheet_id=sid1, piece_id=pid1), edge_pos=ep1)
    seg2 = SegmentId(piece_id=PieceId(sheet_id=sid2, piece_id=pid2), edge_pos=ep2)
    return MatchResult.model_validate(
        {
            "seg_id1": seg1.model_dump(),
            "seg_id2": seg2.model_dump(),
            "similarity": sim,
            "similarity_manual": sim_manual,
        }
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Return a valid but non-existent .db path in a temp directory."""
    return tmp_path / "test.db"


@pytest.fixture
def store(db_path: Path) -> DatasetStore:
    """Return an open DatasetStore backed by a temp database."""
    return DatasetStore(db_path)


@pytest.fixture
def sheets() -> list[SheetRecord]:
    """Return three sample SheetRecords."""
    return [_make_sheet(i) for i in range(3)]


@pytest.fixture
def pieces() -> list[PieceRecord]:
    """Return sample PieceRecords across two sheets."""
    return [
        _make_piece("sheet_0.jpg", 0),
        _make_piece("sheet_0.jpg", 1, with_opt=True),
        _make_piece("sheet_1.jpg", 0),
    ]


@pytest.fixture
def matches() -> list[MatchResult]:
    """Return sample MatchResults."""
    return [
        _make_match("s1.jpg", 0, EdgePos.LEFT, "s2.jpg", 0, EdgePos.RIGHT, 5.0),
        _make_match("s1.jpg", 0, EdgePos.TOP, "s3.jpg", 0, EdgePos.BOTTOM, 2.0),
        _make_match("s2.jpg", 1, EdgePos.LEFT, "s3.jpg", 1, EdgePos.RIGHT, 8.0),
    ]


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_create_store_creates_tables(db_path: Path) -> None:
    """Opening a DatasetStore creates all three tables."""
    with DatasetStore(db_path) as s:
        conn = s._conn
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        # sqlite_sequence is an internal SQLite table for AUTOINCREMENT tracking
        names = {row[0] for row in cursor.fetchall()} - {"sqlite_sequence"}
    assert names == {"sheets", "pieces", "matches"}


def test_create_store_creates_indexes(db_path: Path) -> None:
    """Opening a DatasetStore creates the three match indexes."""
    with DatasetStore(db_path) as s:
        conn = s._conn
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        names = {row[0] for row in cursor.fetchall()}
    assert "idx_matches_seg1" in names
    assert "idx_matches_seg2" in names
    assert "idx_matches_sim" in names


def test_context_manager(db_path: Path) -> None:
    """DatasetStore works as a context manager and closes cleanly."""
    with DatasetStore(db_path) as s:
        s.save_sheets([_make_sheet(0)])
    # After exiting, the connection is closed; further use would raise
    with pytest.raises(sqlite3.ProgrammingError):
        s._conn.execute("SELECT 1")


def test_db_file_created(db_path: Path) -> None:
    """The .db file is written to disk upon creation."""
    assert not db_path.exists()
    with DatasetStore(db_path):
        pass
    assert db_path.exists()


def test_parent_dir_created(tmp_path: Path) -> None:
    """Missing parent directories are created automatically."""
    nested = tmp_path / "a" / "b" / "c" / "dataset.db"
    with DatasetStore(nested):
        pass
    assert nested.exists()


# ---------------------------------------------------------------------------
# Sheets tests
# ---------------------------------------------------------------------------


def test_save_load_sheets_round_trip(
    store: DatasetStore, sheets: list[SheetRecord]
) -> None:
    """SheetRecords survive a full save/load round-trip."""
    store.save_sheets(sheets)
    loaded = store.load_sheets()

    assert len(loaded) == len(sheets)
    by_id = {r.sheet_id: r for r in loaded}
    for original in sheets:
        reloaded = by_id[original.sheet_id]
        assert reloaded.img_path == original.img_path
        assert reloaded.piece_count == original.piece_count
        assert reloaded.threshold == original.threshold
        assert reloaded.min_area == original.min_area
        assert reloaded.created_at == original.created_at


def test_load_sheet_by_id(store: DatasetStore, sheets: list[SheetRecord]) -> None:
    """load_sheet returns the correct record for a given id."""
    store.save_sheets(sheets)
    target = sheets[1]
    result = store.load_sheet(target.sheet_id)
    assert result is not None
    assert result.sheet_id == target.sheet_id
    assert result.piece_count == target.piece_count


def test_load_sheet_missing_returns_none(store: DatasetStore) -> None:
    """load_sheet returns None for an unknown sheet_id."""
    assert store.load_sheet("does_not_exist.jpg") is None


def test_save_sheets_idempotent(store: DatasetStore) -> None:
    """Saving the same sheet twice does not create duplicates."""
    sheet = _make_sheet(0)
    store.save_sheets([sheet])
    store.save_sheets([sheet])
    assert len(store.load_sheets()) == 1


def test_save_load_sheet_with_metadata(store: DatasetStore) -> None:
    """SheetRecord with metadata round-trips correctly."""
    sheet = _make_sheet(0, with_metadata=True)
    store.save_sheets([sheet])
    loaded = store.load_sheet(sheet.sheet_id)
    assert loaded is not None
    assert loaded.metadata is not None
    assert loaded.metadata.tag_name == "oca"
    assert loaded.metadata.sheet_index == 0
    assert loaded.metadata.total_sheets == 3
    assert loaded.metadata.board_config_id == "oca"


def test_save_load_sheet_without_metadata(store: DatasetStore) -> None:
    """SheetRecord with metadata=None round-trips correctly."""
    sheet = _make_sheet(0, with_metadata=False)
    store.save_sheets([sheet])
    loaded = store.load_sheet(sheet.sheet_id)
    assert loaded is not None
    assert loaded.metadata is None


# ---------------------------------------------------------------------------
# Pieces tests
# ---------------------------------------------------------------------------


def test_save_load_pieces_round_trip(
    store: DatasetStore, pieces: list[PieceRecord]
) -> None:
    """PieceRecords survive a full save/load round-trip including JSON fields."""
    store.save_pieces(pieces)
    loaded = store.load_pieces()

    assert len(loaded) == len(pieces)
    by_id = {str(r.piece_id): r for r in loaded}
    for original in pieces:
        reloaded = by_id[str(original.piece_id)]
        assert reloaded.piece_id == original.piece_id
        assert reloaded.corners == original.corners
        assert reloaded.segment_shapes == original.segment_shapes
        assert reloaded.flat_edges == original.flat_edges
        assert reloaded.contour_point_count == original.contour_point_count
        assert reloaded.contour_region == original.contour_region
        assert reloaded.label == original.label
        assert reloaded.sheet_origin == original.sheet_origin


def test_save_load_piece_with_oriented_piece_type(store: DatasetStore) -> None:
    """PieceRecord with a non-None oriented_piece_type round-trips correctly."""
    piece = _make_piece("s.jpg", 0, with_opt=True)
    store.save_pieces([piece])
    loaded = store.load_piece(str(piece.piece_id))

    assert loaded is not None
    assert loaded.oriented_piece_type == piece.oriented_piece_type


def test_save_load_piece_with_none_oriented_piece_type(store: DatasetStore) -> None:
    """PieceRecord with oriented_piece_type=None round-trips correctly."""
    piece = _make_piece("s.jpg", 0, with_opt=False)
    store.save_pieces([piece])
    loaded = store.load_piece(str(piece.piece_id))

    assert loaded is not None
    assert loaded.oriented_piece_type is None


def test_save_load_piece_with_label(store: DatasetStore) -> None:
    """PieceRecord with a label round-trips correctly."""
    piece = _make_piece("s.jpg", 0, label="A1", sheet_origin=(120, 340))
    store.save_pieces([piece])
    loaded = store.load_piece(str(piece.piece_id))

    assert loaded is not None
    assert loaded.label == "A1"
    assert loaded.sheet_origin == (120, 340)


def test_save_load_piece_without_label(store: DatasetStore) -> None:
    """PieceRecord with label=None and default sheet_origin round-trips correctly."""
    piece = _make_piece("s.jpg", 0)
    store.save_pieces([piece])
    loaded = store.load_piece(str(piece.piece_id))

    assert loaded is not None
    assert loaded.label is None
    assert loaded.sheet_origin == (0, 0)
    assert loaded.padded_size == (0, 0)


def test_save_load_piece_with_padded_size(store: DatasetStore) -> None:
    """PieceRecord with padded_size round-trips correctly."""
    piece = _make_piece("s.jpg", 0, sheet_origin=(50, 60), padded_size=(140, 160))
    store.save_pieces([piece])
    loaded = store.load_piece(str(piece.piece_id))

    assert loaded is not None
    assert loaded.padded_size == (140, 160)
    assert loaded.sheet_origin == (50, 60)


def test_load_piece_by_id(store: DatasetStore, pieces: list[PieceRecord]) -> None:
    """load_piece returns the correct PieceRecord for a given piece_id string."""
    store.save_pieces(pieces)
    target = pieces[1]
    result = store.load_piece(str(target.piece_id))
    assert result is not None
    assert result.piece_id == target.piece_id


def test_load_piece_missing_returns_none(store: DatasetStore) -> None:
    """load_piece returns None for an unknown piece_id."""
    assert store.load_piece("no_such_sheet.jpg:99") is None


def test_load_pieces_for_sheet(store: DatasetStore, pieces: list[PieceRecord]) -> None:
    """load_pieces_for_sheet returns only pieces belonging to the given sheet."""
    store.save_pieces(pieces)
    result = store.load_pieces_for_sheet("sheet_0.jpg")
    assert len(result) == 2
    assert all(r.piece_id.sheet_id == "sheet_0.jpg" for r in result)


def test_load_pieces_for_sheet_other(
    store: DatasetStore, pieces: list[PieceRecord]
) -> None:
    """load_pieces_for_sheet isolates the correct sheet."""
    store.save_pieces(pieces)
    result = store.load_pieces_for_sheet("sheet_1.jpg")
    assert len(result) == 1
    assert result[0].piece_id.sheet_id == "sheet_1.jpg"


# ---------------------------------------------------------------------------
# Matches tests
# ---------------------------------------------------------------------------


def test_save_load_matches_round_trip(
    store: DatasetStore, matches: list[MatchResult]
) -> None:
    """MatchResults survive a full save/load round-trip."""
    store.save_matches(matches)
    loaded = store.load_matches()

    assert len(loaded) == len(matches)
    loaded_pairs = {r.pair for r in loaded}
    for original in matches:
        assert original.pair in loaded_pairs


def test_save_load_matches_similarity_manual(store: DatasetStore) -> None:
    """similarity_manual_ alias is preserved through the save/load cycle."""
    match_with_manual = _make_match(
        "s1.jpg", 0, EdgePos.LEFT, "s2.jpg", 0, EdgePos.RIGHT, 5.0, sim_manual=3.0
    )
    match_without_manual = _make_match(
        "s1.jpg", 0, EdgePos.TOP, "s2.jpg", 0, EdgePos.BOTTOM, 7.0
    )
    store.save_matches([match_with_manual, match_without_manual])
    loaded = {r.pair: r for r in store.load_matches()}

    reloaded_with = loaded[match_with_manual.pair]
    assert reloaded_with.similarity_manual_ == 3.0

    reloaded_without = loaded[match_without_manual.pair]
    assert reloaded_without.similarity_manual_ is None


def test_save_matches_overwrites(store: DatasetStore) -> None:
    """Calling save_matches twice replaces the previous set entirely."""
    first_batch = [
        _make_match("s1.jpg", 0, EdgePos.LEFT, "s2.jpg", 0, EdgePos.RIGHT, 5.0),
        _make_match("s1.jpg", 0, EdgePos.TOP, "s2.jpg", 0, EdgePos.BOTTOM, 2.0),
    ]
    second_batch = [
        _make_match("s3.jpg", 0, EdgePos.LEFT, "s4.jpg", 0, EdgePos.RIGHT, 1.0),
    ]
    store.save_matches(first_batch)
    store.save_matches(second_batch)

    loaded = store.load_matches()
    assert len(loaded) == 1
    assert loaded[0].seg_id1.piece_id.sheet_id == "s3.jpg"


def test_match_count(store: DatasetStore, matches: list[MatchResult]) -> None:
    """match_count returns the correct total number of rows."""
    assert store.match_count() == 0
    store.save_matches(matches)
    assert store.match_count() == len(matches)


def test_load_matches_with_limit(store: DatasetStore) -> None:
    """load_matches(limit=N) returns at most N records."""
    many = [
        _make_match("s1.jpg", i, EdgePos.LEFT, "s2.jpg", i, EdgePos.RIGHT, float(i))
        for i in range(20)
    ]
    store.save_matches(many)
    result = store.load_matches(limit=5)
    assert len(result) == 5


def test_load_matches_sorted_by_similarity(store: DatasetStore) -> None:
    """load_matches returns records in ascending similarity order."""
    unordered = [
        _make_match("s1.jpg", 0, EdgePos.LEFT, "s2.jpg", 0, EdgePos.RIGHT, 9.0),
        _make_match("s1.jpg", 0, EdgePos.TOP, "s2.jpg", 0, EdgePos.BOTTOM, 1.0),
        _make_match("s1.jpg", 1, EdgePos.LEFT, "s2.jpg", 1, EdgePos.RIGHT, 5.0),
    ]
    store.save_matches(unordered)
    sims = [r.similarity for r in store.load_matches()]
    assert sims == sorted(sims)


def test_load_matches_with_min_similarity(store: DatasetStore) -> None:
    """load_matches(min_similarity=T) excludes records below the threshold."""
    data = [
        _make_match("s1.jpg", 0, EdgePos.LEFT, "s2.jpg", 0, EdgePos.RIGHT, 1.0),
        _make_match("s1.jpg", 0, EdgePos.TOP, "s2.jpg", 0, EdgePos.BOTTOM, 5.0),
        _make_match("s1.jpg", 1, EdgePos.LEFT, "s2.jpg", 1, EdgePos.RIGHT, 10.0),
    ]
    store.save_matches(data)
    result = store.load_matches(min_similarity=5.0)
    assert all(r.similarity >= 5.0 for r in result)
    assert len(result) == 2


def test_query_matches_for_piece(store: DatasetStore) -> None:
    """query_matches_for_piece returns only matches involving the piece."""
    target_sid = "target.jpg"
    data = [
        _make_match(target_sid, 0, EdgePos.LEFT, "other.jpg", 0, EdgePos.RIGHT, 3.0),
        _make_match(target_sid, 0, EdgePos.TOP, "other.jpg", 1, EdgePos.BOTTOM, 1.0),
        _make_match(
            "unrelated.jpg", 5, EdgePos.LEFT, "other.jpg", 2, EdgePos.RIGHT, 2.0
        ),
    ]
    store.save_matches(data)
    result = store.query_matches_for_piece(f"{target_sid}:0")
    assert len(result) == 2
    for r in result:
        piece_ids = {r.seg_id1.piece_id, r.seg_id2.piece_id}
        target_pid = PieceId(sheet_id=target_sid, piece_id=0)
        assert target_pid in piece_ids


def test_query_matches_for_piece_sorted_and_limited(store: DatasetStore) -> None:
    """query_matches_for_piece returns top-N in ascending similarity order."""
    data = [
        _make_match(
            "s.jpg", 0, EdgePos.LEFT, f"o{i}.jpg", 0, EdgePos.RIGHT, float(10 - i)
        )
        for i in range(8)
    ]
    store.save_matches(data)
    result = store.query_matches_for_piece("s.jpg:0", limit=3)
    assert len(result) == 3
    sims = [r.similarity for r in result]
    assert sims == sorted(sims)


def test_query_matches_for_segment(store: DatasetStore) -> None:
    """query_matches_for_segment filters by both piece and edge position."""
    pid = PieceId(sheet_id="s.jpg", piece_id=0)
    data = [
        _make_match("s.jpg", 0, EdgePos.LEFT, "o.jpg", 0, EdgePos.RIGHT, 1.0),
        _make_match("s.jpg", 0, EdgePos.TOP, "o.jpg", 0, EdgePos.BOTTOM, 2.0),
        _make_match("s.jpg", 1, EdgePos.LEFT, "o.jpg", 1, EdgePos.RIGHT, 3.0),
    ]
    store.save_matches(data)
    result = store.query_matches_for_segment(str(pid), "left")
    assert len(result) == 1
    seg_ids = {result[0].seg_id1, result[0].seg_id2}
    matching_segs = [
        s for s in seg_ids if s.piece_id == pid and s.edge_pos == EdgePos.LEFT
    ]
    assert len(matching_segs) == 1


def test_query_matches_for_piece_as_second_segment(store: DatasetStore) -> None:
    """query_matches_for_piece finds matches where the piece is seg_id2."""
    data = [
        _make_match("other.jpg", 0, EdgePos.LEFT, "target.jpg", 0, EdgePos.RIGHT, 4.0),
    ]
    store.save_matches(data)
    result = store.query_matches_for_piece("target.jpg:0")
    assert len(result) == 1
