"""Database connection handling for openalex_local."""

import json as _json
import sqlite3 as _sqlite3
from contextlib import contextmanager as _contextmanager
from pathlib import Path as _Path
from typing import Any, Dict, Generator, List, Optional

from .config import Config as _Config

__all__ = [
    "Database",
    "get_db",
    "close_db",
    "connection",
]


class Database:
    """
    Database connection manager.

    Supports both direct usage and context manager pattern.
    """

    def __init__(self, db_path: Optional[str | _Path] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to database. If None, auto-detects.
        """
        if db_path:
            self.db_path = _Path(db_path)
        else:
            self.db_path = _Config.get_db_path()

        self.conn: Optional[_sqlite3.Connection] = None
        self._connect()

    def _connect(self) -> None:
        """Establish database connection."""
        self.conn = _sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = _sqlite3.Row

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def execute(self, query: str, params: tuple = ()) -> _sqlite3.Cursor:
        """Execute SQL query."""
        return self.conn.execute(query, params)

    def fetchone(self, query: str, params: tuple = ()) -> Optional[_sqlite3.Row]:
        """Execute query and fetch one result."""
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()) -> List[_sqlite3.Row]:
        """Execute query and fetch all results."""
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def get_work(self, openalex_id: str) -> Optional[Dict[str, Any]]:
        """
        Get work data by OpenAlex ID.

        Args:
            openalex_id: OpenAlex ID (e.g., W2741809807)

        Returns:
            Work data dictionary or None
        """
        row = self.fetchone("SELECT * FROM works WHERE openalex_id = ?", (openalex_id,))
        if row:
            return self._row_to_dict(row)
        return None

    def get_work_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get work data by DOI.

        Args:
            doi: DOI string

        Returns:
            Work data dictionary or None
        """
        row = self.fetchone("SELECT * FROM works WHERE doi = ?", (doi,))
        if row:
            return self._row_to_dict(row)
        return None

    def _row_to_dict(self, row: _sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary, parsing JSON fields."""
        result = dict(row)

        # Parse JSON fields
        for field in ["authors_json", "concepts_json", "topics_json"]:
            if field in result and result[field]:
                try:
                    result[field.replace("_json", "")] = _json.loads(result[field])
                except (TypeError, _json.JSONDecodeError):
                    result[field.replace("_json", "")] = []

        # Parse raw_json if present
        if "raw_json" in result and result["raw_json"]:
            try:
                result["raw"] = _json.loads(result["raw_json"])
            except (TypeError, _json.JSONDecodeError):
                result["raw"] = {}

        return result

    def get_source_metrics(self, issn: str) -> Optional[Dict[str, Any]]:
        """
        Get source/journal metrics by ISSN.

        Uses SciTeX Impact Factor (OpenAlex) from precomputed table when available,
        combined with source metrics in a single optimized query.

        Args:
            issn: Journal ISSN

        Returns:
            Dictionary with scitex_if, h_index, cited_by_count or None
        """
        if not issn:
            return None

        # Single optimized query with LEFT JOIN to get both SciTeX IF and source metrics
        row = self.fetchone(
            """
            SELECT
                jif.impact_factor as scitex_if,
                jif.year as if_year,
                s.h_index as source_h_index,
                s.cited_by_count as source_cited_by_count,
                COALESCE(s.display_name, jif.journal_name) as source_name
            FROM issn_lookup l
            JOIN sources s ON l.source_id = s.id
            LEFT JOIN (
                SELECT issn, impact_factor, journal_name, year
                FROM journal_impact_factors
                WHERE issn = ?
                ORDER BY year DESC
                LIMIT 1
            ) jif ON jif.issn = l.issn
            WHERE l.issn = ?
            """,
            (issn, issn),
        )
        if row:
            return dict(row)

        # Fallback: check journal_impact_factors only (journal may not be in sources)
        row = self.fetchone(
            """
            SELECT impact_factor as scitex_if, journal_name as source_name, year as if_year
            FROM journal_impact_factors
            WHERE issn = ?
            ORDER BY year DESC
            LIMIT 1
            """,
            (issn,),
        )
        if row:
            return dict(row)

        # Final fallback: search in sources.issns JSON field
        row = self.fetchone(
            """
            SELECT h_index as source_h_index,
                   cited_by_count as source_cited_by_count,
                   display_name as source_name
            FROM sources
            WHERE issn_l = ? OR issns LIKE ?
            """,
            (issn, f'%"{issn}"%'),
        )
        if row:
            return dict(row)

        return None

    def has_sources_table(self) -> bool:
        """Check if sources table exists."""
        row = self.fetchone(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='sources'"
        )
        return row is not None


# Singleton connection for convenience functions
_db: Optional[Database] = None


def get_db() -> Database:
    """Get or create singleton database connection."""
    global _db
    if _db is None:
        _db = Database()
    return _db


def close_db() -> None:
    """Close singleton database connection."""
    global _db
    if _db:
        _db.close()
        _db = None


@_contextmanager
def connection(
    db_path: Optional[str | _Path] = None,
) -> Generator[Database, None, None]:
    """
    Context manager for database connection.

    Args:
        db_path: Path to database. If None, auto-detects.

    Yields:
        Database instance
    """
    db = Database(db_path)
    try:
        yield db
    finally:
        db.close()
