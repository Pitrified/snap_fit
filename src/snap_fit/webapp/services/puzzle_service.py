"""Service layer for puzzle operations.

Integrates with DatasetStore for match data access.
"""

from pathlib import Path
import time
from typing import Any

from loguru import logger as lg

from snap_fit.config.aruco.sheet_aruco_config import SheetArucoConfig
from snap_fit.data_models.match_result import MatchResult
from snap_fit.persistence.sqlite_store import DatasetStore
from snap_fit.puzzle.piece_matcher import PieceMatcher
from snap_fit.puzzle.sheet_aruco import SheetAruco
from snap_fit.puzzle.sheet_manager import SheetManager


class PuzzleService:
    """Service for puzzle solving and match operations."""

    def __init__(
        self,
        cache_dir: Path,
        data_dir: Path | None = None,
        dataset_tag: str | None = None,
    ) -> None:
        """Initialize service with cache directory.

        Args:
            cache_dir: Root cache directory.  Dataset databases live under
                ``cache_dir / sheets_tag / dataset.db``.
            data_dir: Root data directory used to resolve config and sheet images.
            dataset_tag: When set, all queries are scoped to this dataset only.
        """
        self.cache_dir = cache_dir
        self.data_dir = data_dir
        self.dataset_tag = dataset_tag

    def _all_db_paths(self) -> list[Path]:
        """Return dataset.db paths to query.

        When dataset_tag is set, returns only that tag's database.
        Otherwise returns all database files found across sub-directories.
        """
        if not self.cache_dir.exists():
            return []
        if self.dataset_tag is not None:
            db = self.cache_dir / self.dataset_tag / "dataset.db"
            return [db] if db.exists() else []
        return [
            p / "dataset.db"
            for p in self.cache_dir.iterdir()
            if p.is_dir() and (p / "dataset.db").exists()
        ]

    def list_matches(
        self,
        limit: int = 100,
        min_similarity: float | None = None,
    ) -> list[MatchResult]:
        """Return match results aggregated from all cached dataset matches.

        Args:
            limit: Maximum number of matches to return.
            min_similarity: Filter to matches with similarity >= this value.

        Returns:
            List of MatchResult objects sorted by similarity (ascending).
        """
        all_db_paths = self._all_db_paths()
        if not all_db_paths:
            return []

        results: list[MatchResult] = []
        for db_path in all_db_paths:
            with DatasetStore(db_path) as store:
                results.extend(store.load_matches(min_similarity=min_similarity))

        results.sort(key=lambda r: r.similarity)
        return results[:limit]

    def get_matches_for_piece(
        self,
        piece_id: str,
        limit: int = 10,
    ) -> list[MatchResult]:
        """Return top matches involving a specific piece, across all datasets.

        Args:
            piece_id: The piece ID (format: sheet_id:piece_idx).
            limit: Maximum number of matches to return.

        Returns:
            List of MatchResult objects involving the piece.
        """
        all_db_paths = self._all_db_paths()
        if not all_db_paths:
            return []

        results: list[MatchResult] = []
        for db_path in all_db_paths:
            with DatasetStore(db_path) as store:
                results.extend(store.query_matches_for_piece(piece_id, limit))
        results.sort(key=lambda r: r.similarity)
        return results[:limit]

    def get_matches_for_segment(
        self,
        piece_id: str,
        edge_pos: str,
        limit: int = 5,
    ) -> list[MatchResult]:
        """Return top matches for a specific segment, across all datasets.

        Args:
            piece_id: The piece ID.
            edge_pos: The edge position (TOP, RIGHT, BOTTOM, LEFT).
            limit: Maximum number of matches to return.

        Returns:
            List of MatchResult objects for the segment.
        """
        all_db_paths = self._all_db_paths()
        if not all_db_paths:
            return []

        results: list[MatchResult] = []
        for db_path in all_db_paths:
            with DatasetStore(db_path) as store:
                results.extend(
                    store.query_matches_for_segment(piece_id, edge_pos, limit)
                )
        results.sort(key=lambda r: r.similarity)
        return results[:limit]

    def solve_puzzle(
        self,
        piece_ids: list[str] | None = None,
        config_path: str | None = None,
    ) -> dict[str, Any]:
        """Attempt to solve a puzzle.

        Args:
            piece_ids: Optional list of piece IDs to include in solve.
            config_path: Optional path to puzzle configuration.

        Returns:
            Dict with success, message, layout, piece_count.
        """
        # Placeholder - will integrate with snap_fit.solver
        count = len(piece_ids) if piece_ids else 0
        lg.info(f"Solve puzzle request: {count} pieces, config={config_path}")
        return {
            "success": False,
            "message": "Solver integration pending",
            "layout": None,
            "piece_count": count,
        }

    def match_count(self) -> int:
        """Return the total number of cached matches across all datasets."""
        total = 0
        for db_path in self._all_db_paths():
            with DatasetStore(db_path) as store:
                total += store.match_count()
        return total

    def run_matching(self, dataset_tag: str, *, force: bool = False) -> dict[str, Any]:
        """Execute segment matching for a dataset and persist results.

        Loads sheets from ``data_dir/{dataset_tag}/``, runs
        ``PieceMatcher.match_all()``, and writes results to the dataset's
        SQLite database.

        Args:
            dataset_tag: Dataset identifier (e.g. "oca", "demo").
            force: When False, skip matching if matches already exist.

        Returns:
            Dict with success, message, match_count, duration_seconds.

        Raises:
            RuntimeError: If data_dir was not provided.
            FileNotFoundError: If config or image folder is missing.
        """
        if self.data_dir is None:
            msg = "data_dir is required for run_matching"
            raise RuntimeError(msg)

        db_path = self.cache_dir / dataset_tag / "dataset.db"

        if not force and db_path.exists():
            with DatasetStore(db_path) as store:
                count = store.match_count()
            if count > 0:
                return {
                    "success": True,
                    "message": "Matches already exist; use force=True to re-run",
                    "match_count": count,
                    "duration_seconds": 0.0,
                }

        config_name = f"{dataset_tag}_SheetArucoConfig.json"
        config_path = self.data_dir / dataset_tag / config_name
        img_dir = self.data_dir / dataset_tag / "sheets"

        if not config_path.exists():
            msg = f"SheetArucoConfig not found: {config_path}"
            raise FileNotFoundError(msg)
        if not img_dir.is_dir():
            msg = f"Image folder not found: {img_dir}"
            raise FileNotFoundError(msg)

        sheet_config = SheetArucoConfig.model_validate_json(config_path.read_text())
        sheet_aruco = SheetAruco(sheet_config)
        manager = SheetManager()
        manager.add_sheets(
            folder_path=img_dir, pattern="*.jpg", loader_func=sheet_aruco.load_sheet
        )

        lg.info(f"Running match_all() for dataset '{dataset_tag}'")
        t0 = time.monotonic()
        matcher = PieceMatcher(manager)
        matcher.match_all()
        matcher.save_matches_db(db_path)
        duration = time.monotonic() - t0

        match_count = len(matcher.results)
        lg.info(f"Matching done: {match_count} pairs in {duration:.1f}s")
        return {
            "success": True,
            "message": f"Matched {match_count} pairs in {duration:.1f}s",
            "match_count": match_count,
            "duration_seconds": round(duration, 2),
        }
