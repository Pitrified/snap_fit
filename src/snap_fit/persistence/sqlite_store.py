"""SQLite-backed persistence store for a single dataset."""

import json
from pathlib import Path
import sqlite3
from sqlite3 import Row

from loguru import logger as lg

from snap_fit.data_models.match_result import MatchResult
from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.data_models.sheet_record import SheetRecord

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_DDL_SHEETS = """\
CREATE TABLE IF NOT EXISTS sheets (
    sheet_id    TEXT    PRIMARY KEY,
    img_path    TEXT    NOT NULL,
    piece_count INTEGER NOT NULL,
    threshold   INTEGER NOT NULL,
    min_area    INTEGER NOT NULL,
    created_at  TEXT    NOT NULL
)"""

_DDL_PIECES = """\
CREATE TABLE IF NOT EXISTS pieces (
    piece_id             TEXT    PRIMARY KEY,
    sheet_id             TEXT    NOT NULL REFERENCES sheets (sheet_id),
    piece_idx            INTEGER NOT NULL,
    corners              TEXT    NOT NULL,
    segment_shapes       TEXT    NOT NULL,
    oriented_piece_type  TEXT,
    flat_edges           TEXT    NOT NULL,
    contour_point_count  INTEGER NOT NULL,
    contour_region       TEXT    NOT NULL
)"""

_DDL_MATCHES = """\
CREATE TABLE IF NOT EXISTS matches (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    seg_id1_sheet_id   TEXT    NOT NULL,
    seg_id1_piece_idx  INTEGER NOT NULL,
    seg_id1_edge_pos   TEXT    NOT NULL,
    seg_id2_sheet_id   TEXT    NOT NULL,
    seg_id2_piece_idx  INTEGER NOT NULL,
    seg_id2_edge_pos   TEXT    NOT NULL,
    similarity         REAL    NOT NULL,
    similarity_manual  REAL
)"""

_DDL_IDX_SEG1 = (
    "CREATE INDEX IF NOT EXISTS idx_matches_seg1"
    " ON matches (seg_id1_sheet_id, seg_id1_piece_idx)"
)
_DDL_IDX_SEG2 = (
    "CREATE INDEX IF NOT EXISTS idx_matches_seg2"
    " ON matches (seg_id2_sheet_id, seg_id2_piece_idx)"
)
_DDL_IDX_SIM = "CREATE INDEX IF NOT EXISTS idx_matches_sim ON matches (similarity)"

_DDL_ALL = (
    _DDL_SHEETS,
    _DDL_PIECES,
    _DDL_MATCHES,
    _DDL_IDX_SEG1,
    _DDL_IDX_SEG2,
    _DDL_IDX_SIM,
)

# ---------------------------------------------------------------------------
# DML
# ---------------------------------------------------------------------------

_INS_SHEET = """\
INSERT OR REPLACE INTO sheets
  (sheet_id, img_path, piece_count, threshold, min_area, created_at)
  VALUES (?, ?, ?, ?, ?, ?)"""

_INS_PIECE = """\
INSERT OR REPLACE INTO pieces
  (piece_id, sheet_id, piece_idx, corners, segment_shapes,
   oriented_piece_type, flat_edges, contour_point_count, contour_region)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""

_INS_MATCH = """\
INSERT INTO matches
  (seg_id1_sheet_id, seg_id1_piece_idx, seg_id1_edge_pos,
   seg_id2_sheet_id, seg_id2_piece_idx, seg_id2_edge_pos,
   similarity, similarity_manual)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""

_DEL_MATCHES = "DELETE FROM matches"

# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

_SEL_SHEETS = "SELECT * FROM sheets"
_SEL_SHEET = "SELECT * FROM sheets WHERE sheet_id = ?"
_SEL_PIECES = "SELECT * FROM pieces"
_SEL_PIECE = "SELECT * FROM pieces WHERE piece_id = ?"
_SEL_PIECES_FOR_SHEET = "SELECT * FROM pieces WHERE sheet_id = ?"
_SEL_MATCH_COUNT = "SELECT COUNT(*) FROM matches"

_SEL_MATCHES_FOR_PIECE = """\
SELECT * FROM matches
WHERE (seg_id1_sheet_id = ? AND seg_id1_piece_idx = ?)
   OR (seg_id2_sheet_id = ? AND seg_id2_piece_idx = ?)
ORDER BY similarity LIMIT ?"""

_SEL_MATCHES_FOR_SEG = """\
SELECT * FROM matches
WHERE (seg_id1_sheet_id = ? AND seg_id1_piece_idx = ? AND seg_id1_edge_pos = ?)
   OR (seg_id2_sheet_id = ? AND seg_id2_piece_idx = ? AND seg_id2_edge_pos = ?)
ORDER BY similarity LIMIT ?"""

# load_matches assembles these fragments depending on active filters.
_SEL_MATCHES_BASE = "SELECT * FROM matches"
_SEL_MATCHES_SIM_COND = " WHERE similarity >= ?"
_SEL_MATCHES_ORDER = " ORDER BY similarity"
_SEL_MATCHES_LIMIT = " LIMIT ?"


def _parse_piece_id(piece_id: str) -> tuple[str, int]:
    """Split a piece ID string ``sheet_id:piece_idx`` into its two components."""
    sheet_id, piece_idx_str = piece_id.rsplit(":", 1)
    return sheet_id, int(piece_idx_str)


class DatasetStore:
    """SQLite store for a single dataset's sheets, pieces, and matches.

    One ``DatasetStore`` instance corresponds to one ``dataset.db`` file under
    a ``cache/{sheets_tag}/`` directory.  The class converts between Pydantic
    models and flat SQLite rows; callers never interact with raw SQL.

    Supports use as a context manager::

        with DatasetStore(db_path) as store:
            store.save_sheets(records)
    """

    def __init__(self, db_path: Path) -> None:
        """Open (or create) the SQLite database at ``db_path``.

        The parent directory is created if it does not exist.
        The schema (tables + indexes) is applied on first open.

        Args:
            db_path: Filesystem path for the ``.db`` file.
        """
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()

    def __enter__(self) -> "DatasetStore":
        """Return self to support use as a context manager."""
        return self

    def __exit__(self, *_: object) -> None:
        """Close the database connection when leaving the context."""
        self.close()

    # -------------------------------------------------------------------------
    # Schema
    # -------------------------------------------------------------------------

    def _ensure_schema(self) -> None:
        """Create tables and indexes if they do not yet exist."""
        with self._conn:
            for stmt in _DDL_ALL:
                self._conn.execute(stmt)

    # -------------------------------------------------------------------------
    # Row conversion helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _sheet_to_row(r: SheetRecord) -> tuple[str, str, int, int, int, str]:
        """Return a values tuple for an ``INSERT INTO sheets`` statement."""
        return (
            r.sheet_id,
            str(r.img_path),
            r.piece_count,
            r.threshold,
            r.min_area,
            r.created_at.isoformat(),
        )

    @staticmethod
    def _row_to_sheet(row: Row) -> SheetRecord:
        """Reconstruct a ``SheetRecord`` from a sheets table row."""
        return SheetRecord.model_validate(
            {
                "sheet_id": row["sheet_id"],
                "img_path": row["img_path"],
                "piece_count": row["piece_count"],
                "threshold": row["threshold"],
                "min_area": row["min_area"],
                "created_at": row["created_at"],
            }
        )

    @staticmethod
    def _piece_to_row(
        r: PieceRecord,
    ) -> tuple[str, str, int, str, str, str | None, str, int, str]:
        """Return a values tuple for an ``INSERT INTO pieces`` statement."""
        data = r.model_dump(mode="json")
        opt = data["oriented_piece_type"]
        return (
            str(r.piece_id),
            r.piece_id.sheet_id,
            r.piece_id.piece_id,
            json.dumps(data["corners"]),
            json.dumps(data["segment_shapes"]),
            json.dumps(opt) if opt is not None else None,
            json.dumps(data["flat_edges"]),
            r.contour_point_count,
            json.dumps(data["contour_region"]),
        )

    @staticmethod
    def _row_to_piece(row: Row) -> PieceRecord:
        """Reconstruct a ``PieceRecord`` from a pieces table row."""
        opt_raw: str | None = row["oriented_piece_type"]
        oriented = json.loads(opt_raw) if opt_raw is not None else None
        return PieceRecord.model_validate(
            {
                "piece_id": {
                    "sheet_id": row["sheet_id"],
                    "piece_id": row["piece_idx"],
                },
                "corners": json.loads(row["corners"]),
                "segment_shapes": json.loads(row["segment_shapes"]),
                "oriented_piece_type": oriented,
                "flat_edges": json.loads(row["flat_edges"]),
                "contour_point_count": row["contour_point_count"],
                "contour_region": json.loads(row["contour_region"]),
            }
        )

    @staticmethod
    def _match_to_row(
        m: MatchResult,
    ) -> tuple[str, int, str, str, int, str, float, float | None]:
        """Return a values tuple for an ``INSERT INTO matches`` statement."""
        return (
            m.seg_id1.piece_id.sheet_id,
            m.seg_id1.piece_id.piece_id,
            m.seg_id1.edge_pos.value,
            m.seg_id2.piece_id.sheet_id,
            m.seg_id2.piece_id.piece_id,
            m.seg_id2.edge_pos.value,
            m.similarity,
            m.similarity_manual_,
        )

    @staticmethod
    def _row_to_match(row: Row) -> MatchResult:
        """Reconstruct a ``MatchResult`` from a matches table row."""
        return MatchResult.model_validate(
            {
                "seg_id1": {
                    "piece_id": {
                        "sheet_id": row["seg_id1_sheet_id"],
                        "piece_id": row["seg_id1_piece_idx"],
                    },
                    "edge_pos": row["seg_id1_edge_pos"],
                },
                "seg_id2": {
                    "piece_id": {
                        "sheet_id": row["seg_id2_sheet_id"],
                        "piece_id": row["seg_id2_piece_idx"],
                    },
                    "edge_pos": row["seg_id2_edge_pos"],
                },
                "similarity": row["similarity"],
                "similarity_manual": row["similarity_manual"],
            }
        )

    # -------------------------------------------------------------------------
    # Sheets
    # -------------------------------------------------------------------------

    def save_sheets(self, records: list[SheetRecord]) -> None:
        """Persist sheet records, replacing any existing row with the same ``sheet_id``.

        Args:
            records: Sheet records to save.
        """
        rows = [self._sheet_to_row(r) for r in records]
        with self._conn:
            self._conn.executemany(_INS_SHEET, rows)
        lg.info(f"Saved {len(records)} sheets to database.")

    def load_sheets(self) -> list[SheetRecord]:
        """Return all sheet records from the database."""
        cursor = self._conn.execute(_SEL_SHEETS)
        return [self._row_to_sheet(row) for row in cursor.fetchall()]

    def load_sheet(self, sheet_id: str) -> SheetRecord | None:
        """Return a single sheet by ID, or ``None`` if not found.

        Args:
            sheet_id: The sheet identifier string.
        """
        cursor = self._conn.execute(_SEL_SHEET, (sheet_id,))
        row = cursor.fetchone()
        return self._row_to_sheet(row) if row is not None else None

    # -------------------------------------------------------------------------
    # Pieces
    # -------------------------------------------------------------------------

    def save_pieces(self, records: list[PieceRecord]) -> None:
        """Persist piece records, replacing any existing row with the same ``piece_id``.

        Args:
            records: Piece records to save.
        """
        rows = [self._piece_to_row(r) for r in records]
        with self._conn:
            self._conn.executemany(_INS_PIECE, rows)
        lg.info(f"Saved {len(records)} pieces to database.")

    def load_pieces(self) -> list[PieceRecord]:
        """Return all piece records from the database."""
        cursor = self._conn.execute(_SEL_PIECES)
        return [self._row_to_piece(row) for row in cursor.fetchall()]

    def load_piece(self, piece_id: str) -> PieceRecord | None:
        """Return a single piece by piece ID string, or ``None`` if not found.

        Args:
            piece_id: The piece ID string (format: ``sheet_id:piece_idx``).
        """
        cursor = self._conn.execute(_SEL_PIECE, (piece_id,))
        row = cursor.fetchone()
        return self._row_to_piece(row) if row is not None else None

    def load_pieces_for_sheet(self, sheet_id: str) -> list[PieceRecord]:
        """Return all piece records belonging to the given sheet.

        Args:
            sheet_id: The sheet identifier to filter by.
        """
        cursor = self._conn.execute(_SEL_PIECES_FOR_SHEET, (sheet_id,))
        return [self._row_to_piece(row) for row in cursor.fetchall()]

    # -------------------------------------------------------------------------
    # Matches
    # -------------------------------------------------------------------------

    def save_matches(self, results: list[MatchResult]) -> None:
        """Replace all match records atomically with the given results.

        All existing rows are deleted before the new batch is inserted,
        matching the full-overwrite semantics of the legacy JSON approach.

        Args:
            results: Match results to persist.
        """
        rows = [self._match_to_row(r) for r in results]
        with self._conn:
            self._conn.execute(_DEL_MATCHES)
            self._conn.executemany(_INS_MATCH, rows)
        lg.info(f"Saved {len(results)} matches to database.")

    def load_matches(
        self,
        limit: int | None = None,
        min_similarity: float | None = None,
    ) -> list[MatchResult]:
        """Return match records ordered by similarity with optional filtering.

        Args:
            limit: Maximum number of records to return.
            min_similarity: Exclude matches with similarity below this value.
        """
        sql = _SEL_MATCHES_BASE
        params: list[float | int] = []
        if min_similarity is not None:
            sql += _SEL_MATCHES_SIM_COND
            params.append(min_similarity)
        sql += _SEL_MATCHES_ORDER
        if limit is not None:
            sql += _SEL_MATCHES_LIMIT
            params.append(limit)
        cursor = self._conn.execute(sql, params)
        return [self._row_to_match(row) for row in cursor.fetchall()]

    def query_matches_for_piece(
        self,
        piece_id: str,
        limit: int = 10,
    ) -> list[MatchResult]:
        """Return top matches involving the given piece, sorted by similarity.

        Uses an indexed lookup on the flattened segment ID columns.

        Args:
            piece_id: Piece ID string (format: ``sheet_id:piece_idx``).
            limit: Maximum number of records to return.
        """
        sheet_id, piece_idx = _parse_piece_id(piece_id)
        cursor = self._conn.execute(
            _SEL_MATCHES_FOR_PIECE,
            (sheet_id, piece_idx, sheet_id, piece_idx, limit),
        )
        return [self._row_to_match(row) for row in cursor.fetchall()]

    def query_matches_for_segment(
        self,
        piece_id: str,
        edge_pos: str,
        limit: int = 5,
    ) -> list[MatchResult]:
        """Return top matches involving the given segment, sorted by similarity.

        Args:
            piece_id: Piece ID string (format: ``sheet_id:piece_idx``).
            edge_pos: Edge position value string (e.g. ``"left"``, ``"top"``).
            limit: Maximum number of records to return.
        """
        sheet_id, piece_idx = _parse_piece_id(piece_id)
        cursor = self._conn.execute(
            _SEL_MATCHES_FOR_SEG,
            (sheet_id, piece_idx, edge_pos, sheet_id, piece_idx, edge_pos, limit),
        )
        return [self._row_to_match(row) for row in cursor.fetchall()]

    def match_count(self) -> int:
        """Return the total number of match records in the database."""
        cursor = self._conn.execute(_SEL_MATCH_COUNT)
        row = cursor.fetchone()
        return int(row[0])
