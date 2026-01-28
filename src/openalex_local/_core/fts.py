"""Full-text search using FTS5."""

import re as _re
import time as _time
from typing import List, Optional

from .db import Database, get_db
from .models import SearchResult, Work

__all__ = [
    "search",
    "count",
    "search_ids",
]


def _sanitize_query(query: str) -> str:
    """
    Sanitize query for FTS5.

    Handles special characters that FTS5 interprets as operators.
    """
    if query.startswith('"') and query.endswith('"'):
        return query

    has_hyphenated_word = _re.search(r"\w+-\w+", query)
    has_special = _re.search(r"[/\\@#$%^&]", query)

    if has_hyphenated_word or has_special:
        words = query.split()
        quoted = " ".join(f'"{w}"' for w in words)
        return quoted

    return query


def search(
    query: str,
    limit: int = 20,
    offset: int = 0,
    db: Optional[Database] = None,
) -> SearchResult:
    """
    Full-text search across works.

    Uses FTS5 index for fast searching across titles and abstracts.

    Args:
        query: Search query (supports FTS5 syntax like AND, OR, NOT, "phrases")
        limit: Maximum results to return
        offset: Skip first N results (for pagination)
        db: Database connection (uses singleton if not provided)

    Returns:
        SearchResult with matching works

    Example:
        >>> results = search("machine learning neural networks")
        >>> print(f"Found {results.total} matches in {results.elapsed_ms:.1f}ms")
    """
    if db is None:
        db = get_db()

    start = _time.perf_counter()
    safe_query = _sanitize_query(query)

    # Get total count
    count_row = db.fetchone(
        "SELECT COUNT(*) as total FROM works_fts WHERE works_fts MATCH ?",
        (safe_query,),
    )
    total = count_row["total"] if count_row else 0

    # Get matching works
    rows = db.fetchall(
        """
        SELECT w.*
        FROM works_fts f
        JOIN works w ON f.rowid = w.rowid
        WHERE works_fts MATCH ?
        LIMIT ? OFFSET ?
        """,
        (safe_query, limit, offset),
    )

    elapsed_ms = (_time.perf_counter() - start) * 1000

    # Convert to Work objects
    works = []
    for row in rows:
        data = db._row_to_dict(row)
        works.append(Work.from_db_row(data))

    return SearchResult(
        works=works,
        total=total,
        query=query,
        elapsed_ms=elapsed_ms,
    )


def count(query: str, db: Optional[Database] = None) -> int:
    """
    Count matching works without fetching results.

    Args:
        query: FTS5 search query
        db: Database connection

    Returns:
        Number of matching works
    """
    if db is None:
        db = get_db()

    safe_query = _sanitize_query(query)
    row = db.fetchone(
        "SELECT COUNT(*) as total FROM works_fts WHERE works_fts MATCH ?",
        (safe_query,),
    )
    return row["total"] if row else 0


def search_ids(
    query: str,
    limit: int = 1000,
    db: Optional[Database] = None,
) -> List[str]:
    """
    Search and return only OpenAlex IDs (faster than full search).

    Args:
        query: FTS5 search query
        limit: Maximum IDs to return
        db: Database connection

    Returns:
        List of matching OpenAlex IDs
    """
    if db is None:
        db = get_db()

    safe_query = _sanitize_query(query)
    rows = db.fetchall(
        """
        SELECT w.openalex_id
        FROM works_fts f
        JOIN works w ON f.rowid = w.rowid
        WHERE works_fts MATCH ?
        LIMIT ?
        """,
        (safe_query, limit),
    )

    return [row["openalex_id"] for row in rows]


def _search_with_db(db: Database, query: str, limit: int, offset: int) -> SearchResult:
    """Search with explicit database connection (for thread-safe async)."""
    return search(query, limit, offset, db=db)


def _count_with_db(db: Database, query: str) -> int:
    """Count with explicit database connection (for thread-safe async)."""
    return count(query, db=db)
