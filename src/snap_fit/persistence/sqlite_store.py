"""SQLite-backed persistence store for a single dataset."""

import contextlib
import json
from pathlib import Path
import sqlite3
from sqlite3 import Row

from loguru import logger as lg

from snap_fit.aruco.sheet_metadata import SheetMetadata
from snap_fit.data_models.match_result import MatchResult
from snap_fit.data_models.piece_record import PieceRecord
from snap_fit.data_models.sheet_record import SheetRecord
from snap_fit.grid.orientation import OrientedPieceType

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
    created_at  TEXT    NOT NULL,
    metadata    TEXT
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
    contour_region       TEXT    NOT NULL,
    label                TEXT,
    sheet_origin         TEXT,
    padded_size          TEXT
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

_DDL_SESSIONS = """\
CREATE TABLE IF NOT EXISTS sessions (
    session_id          TEXT    PRIMARY KEY,
    dataset_tag         TEXT    NOT NULL,
    grid_rows           INTEGER NOT NULL,
    grid_cols           INTEGER NOT NULL,
    placement           TEXT    NOT NULL DEFAULT '{}',
    rejected            TEXT    NOT NULL DEFAULT '{}',
    undo_stack          TEXT    NOT NULL DEFAULT '[]',
    complete            INTEGER NOT NULL DEFAULT 0,
    score               REAL,
    pending_suggestion  TEXT,
    created_at          TEXT    NOT NULL,
    updated_at          TEXT    NOT NULL
)"""

# Migrations for existing databases that lack new columns.
_MIGRATE_SHEETS_METADATA = "ALTER TABLE sheets ADD COLUMN metadata TEXT"
_MIGRATE_PIECES_LABEL = "ALTER TABLE pieces ADD COLUMN label TEXT"
_MIGRATE_PIECES_SHEET_ORIGIN = "ALTER TABLE pieces ADD COLUMN sheet_origin TEXT"
_MIGRATE_PIECES_PADDED_SIZE = "ALTER TABLE pieces ADD COLUMN padded_size TEXT"
_MIGRATE_SESSIONS_PENDING = "ALTER TABLE sessions ADD COLUMN pending_suggestion TEXT"

_DDL_ALL = (
    _DDL_SHEETS,
    _DDL_PIECES,
    _DDL_MATCHES,
    _DDL_SESSIONS,
    _DDL_IDX_SEG1,
    _DDL_IDX_SEG2,
    _DDL_IDX_SIM,
)

# ---------------------------------------------------------------------------
# DML
# ---------------------------------------------------------------------------

_INS_SHEET = """\
INSERT OR REPLACE INTO sheets
  (sheet_id, img_path, piece_count, threshold, min_area, created_at, metadata)
  VALUES (?, ?, ?, ?, ?, ?, ?)"""

_INS_PIECE = """\
INSERT OR REPLACE INTO pieces
  (piece_id, sheet_id, piece_idx, corners, segment_shapes,
   oriented_piece_type, flat_edges, contour_point_count, contour_region,
   label, sheet_origin, padded_size)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

_INS_SESSION = """\
INSERT OR REPLACE INTO sessions
  (session_id, dataset_tag, grid_rows, grid_cols,
   placement, rejected, undo_stack, complete, score,
   pending_suggestion, created_at, updated_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

_SEL_SESSION = "SELECT * FROM sessions WHERE session_id = ?"
_SEL_SESSIONS = "SELECT * FROM sessions ORDER BY updated_at DESC"
_DEL_SESSION = "DELETE FROM sessions WHERE session_id = ?"

_INS_MATCH = """\
INSERT INTO matches
  (seg_id1_sheet_id, seg_id1_piece_idx, seg_id1_edge_pos,
   seg_id2_sheet_id, seg_id2_piece_idx, seg_id2_edge_pos,
   similarity, similarity_manual)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""

_DEL_MATCHES = "DELETE FROM matches"

_UPD_PIECE_SEGMENTS = """\
UPDATE pieces
SET segment_shapes = ?, flat_edges = ?, oriented_piece_type = ?
WHERE piece_id = ?"""

_UPD_MATCH_MANUAL = """\
UPDATE matches
SET similarity_manual = ?
WHERE
  (seg_id1_sheet_id = ? AND seg_id1_piece_idx = ? AND seg_id1_edge_pos = ?
   AND seg_id2_sheet_id = ? AND seg_id2_piece_idx = ? AND seg_id2_edge_pos = ?)
  OR
  (seg_id1_sheet_id = ? AND seg_id1_piece_idx = ? AND seg_id1_edge_pos = ?
   AND seg_id2_sheet_id = ? AND seg_id2_piece_idx = ? AND seg_id2_edge_pos = ?)"""

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
            self._apply_migrations()

    def _apply_migrations(self) -> None:
        """Add columns that may be missing from an older schema."""
        for stmt in (
            _MIGRATE_SHEETS_METADATA,
            _MIGRATE_PIECES_LABEL,
            _MIGRATE_PIECES_SHEET_ORIGIN,
            _MIGRATE_PIECES_PADDED_SIZE,
            _MIGRATE_SESSIONS_PENDING,
        ):
            with contextlib.suppress(sqlite3.OperationalError):
                self._conn.execute(stmt)

    # -------------------------------------------------------------------------
    # Row conversion helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _sheet_to_row(
        r: SheetRecord,
    ) -> tuple[str, str, int, int, int, str, str | None]:
        """Return a values tuple for an ``INSERT INTO sheets`` statement."""
        metadata_json: str | None = None
        if r.metadata is not None:
            metadata_json = r.metadata.model_dump_json()
        return (
            r.sheet_id,
            str(r.img_path),
            r.piece_count,
            r.threshold,
            r.min_area,
            r.created_at.isoformat(),
            metadata_json,
        )

    @staticmethod
    def _row_to_sheet(row: Row) -> SheetRecord:
        """Reconstruct a ``SheetRecord`` from a sheets table row."""
        metadata_raw: str | None = row["metadata"]
        metadata = (
            SheetMetadata.model_validate_json(metadata_raw)
            if metadata_raw is not None
            else None
        )
        return SheetRecord.model_validate(
            {
                "sheet_id": row["sheet_id"],
                "img_path": row["img_path"],
                "piece_count": row["piece_count"],
                "threshold": row["threshold"],
                "min_area": row["min_area"],
                "created_at": row["created_at"],
                "metadata": metadata,
            }
        )

    @staticmethod
    def _piece_to_row(
        r: PieceRecord,
    ) -> tuple[
        str, str, int, str, str, str | None, str, int, str, str | None, str, str
    ]:
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
            r.label,
            json.dumps(data["sheet_origin"]),
            json.dumps(data["padded_size"]),
        )

    @staticmethod
    def _row_to_piece(row: Row) -> PieceRecord:
        """Reconstruct a ``PieceRecord`` from a pieces table row."""
        opt_raw: str | None = row["oriented_piece_type"]
        oriented = json.loads(opt_raw) if opt_raw is not None else None
        label: str | None = row["label"]
        origin_raw: str | None = row["sheet_origin"]
        sheet_origin = json.loads(origin_raw) if origin_raw is not None else (0, 0)
        padded_raw: str | None = row["padded_size"]
        padded_size = json.loads(padded_raw) if padded_raw is not None else (0, 0)
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
                "label": label,
                "sheet_origin": sheet_origin,
                "padded_size": padded_size,
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

    def update_piece_segments(
        self,
        piece_id: str,
        segment_shapes: dict[str, str],
        flat_edges: list[str],
        oriented_piece_type: OrientedPieceType | None,
    ) -> bool:
        """Update a piece's segment shapes, flat edges, and piece type.

        Args:
            piece_id: The piece identifier string (``sheet_id:piece_idx``).
            segment_shapes: Updated segment shapes dict.
            flat_edges: Updated flat edges list.
            oriented_piece_type: Recomputed oriented piece type (may be None).

        Returns:
            True if a row was updated, False if the piece was not found.
        """
        opt_json: str | None = None
        if oriented_piece_type is not None:
            opt_json = json.dumps(oriented_piece_type.model_dump(mode="json"))
        with self._conn:
            cursor = self._conn.execute(
                _UPD_PIECE_SEGMENTS,
                (
                    json.dumps(segment_shapes),
                    json.dumps(flat_edges),
                    opt_json,
                    piece_id,
                ),
            )
        return cursor.rowcount > 0

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

    # -------------------------------------------------------------------------
    # Sessions
    # -------------------------------------------------------------------------

    def save_session(self, data: dict[str, object]) -> None:
        """Insert or replace a session record.

        Args:
            data: Session dict with keys matching the sessions table columns.
                ``placement``, ``rejected``, ``undo_stack``, and
                ``pending_suggestion`` may be dicts/lists (they are
                JSON-serialized automatically).
        """
        ps = data.get("pending_suggestion")
        row = (
            data["session_id"],
            data["dataset_tag"],
            data["grid_rows"],
            data["grid_cols"],
            json.dumps(data.get("placement", {})),
            json.dumps(data.get("rejected", {})),
            json.dumps(data.get("undo_stack", [])),
            int(bool(data.get("complete", False))),
            data.get("score"),
            json.dumps(ps) if ps is not None else None,
            data["created_at"],
            data["updated_at"],
        )
        with self._conn:
            self._conn.execute(_INS_SESSION, row)

    def load_session(self, session_id: str) -> dict[str, object] | None:
        """Return a session dict by ID, or ``None`` if not found.

        Args:
            session_id: The session identifier.
        """
        cursor = self._conn.execute(_SEL_SESSION, (session_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_session_dict(row)

    def load_sessions(self) -> list[dict[str, object]]:
        """Return all session dicts ordered by most recently updated."""
        cursor = self._conn.execute(_SEL_SESSIONS)
        return [self._row_to_session_dict(row) for row in cursor.fetchall()]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID.

        Args:
            session_id: The session identifier.

        Returns:
            ``True`` if a row was deleted, ``False`` otherwise.
        """
        with self._conn:
            cursor = self._conn.execute(_DEL_SESSION, (session_id,))
        return cursor.rowcount > 0

    @staticmethod
    def _row_to_session_dict(row: Row) -> dict[str, object]:
        """Convert a sessions table row to a plain dict."""
        ps_raw: str | None = row["pending_suggestion"]
        return {
            "session_id": row["session_id"],
            "dataset_tag": row["dataset_tag"],
            "grid_rows": row["grid_rows"],
            "grid_cols": row["grid_cols"],
            "placement": json.loads(row["placement"]),
            "rejected": json.loads(row["rejected"]),
            "undo_stack": json.loads(row["undo_stack"]),
            "complete": bool(row["complete"]),
            "score": row["score"],
            "pending_suggestion": json.loads(ps_raw) if ps_raw is not None else None,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def update_match_manual_score(
        self,
        seg_id1: object,
        seg_id2: object,
        value: float,
    ) -> None:
        """Update ``similarity_manual`` for a specific segment pair.

        The pair is looked up in both orderings ``(seg1, seg2)`` and
        ``(seg2, seg1)``.  No error is raised if no matching row is found.

        Args:
            seg_id1: First ``SegmentId``.
            seg_id2: Second ``SegmentId``.
            value: The new ``similarity_manual`` value.
        """
        params = (
            value,
            seg_id1.piece_id.sheet_id,  # type: ignore[union-attr]
            seg_id1.piece_id.piece_id,  # type: ignore[union-attr]
            seg_id1.edge_pos.value,  # type: ignore[union-attr]
            seg_id2.piece_id.sheet_id,  # type: ignore[union-attr]
            seg_id2.piece_id.piece_id,  # type: ignore[union-attr]
            seg_id2.edge_pos.value,  # type: ignore[union-attr]
            seg_id2.piece_id.sheet_id,  # type: ignore[union-attr]
            seg_id2.piece_id.piece_id,  # type: ignore[union-attr]
            seg_id2.edge_pos.value,  # type: ignore[union-attr]
            seg_id1.piece_id.sheet_id,  # type: ignore[union-attr]
            seg_id1.piece_id.piece_id,  # type: ignore[union-attr]
            seg_id1.edge_pos.value,  # type: ignore[union-attr]
        )
        with self._conn:
            self._conn.execute(_UPD_MATCH_MANUAL, params)
