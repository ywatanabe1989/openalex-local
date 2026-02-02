"""Main API for openalex_local.

Supports two modes:
- db: Direct database access (requires database file)
- http: HTTP API access (requires API server)

Mode is auto-detected or can be set explicitly via:
- OPENALEX_LOCAL_MODE environment variable ("db" or "http")
- OPENALEX_LOCAL_API_URL environment variable (API URL)
- configure() or configure_http() functions
"""

from typing import List, Optional

from . import fts
from .config import Config
from .db import close_db, get_db
from .models import SearchResult, Work

__all__ = [
    # Core functions
    "search",
    "count",
    "get",
    "get_many",
    "exists",
    "info",
    # Enrich functions
    "enrich",
    "enrich_ids",
    # Configuration
    "configure",
    "get_mode",
    # Models (public)
    "Work",
    "SearchResult",
]


def _get_http_client():
    """Get HTTP client (lazy import to avoid circular dependency)."""
    try:
        from .remote import RemoteClient

        return RemoteClient(Config.get_api_url())
    except ImportError:
        raise NotImplementedError(
            "HTTP mode not yet implemented. Use database mode by setting "
            "OPENALEX_LOCAL_DB environment variable."
        )


def search(
    query: str,
    limit: int = 20,
    offset: int = 0,
) -> SearchResult:
    """
    Full-text search across works.

    Uses FTS5 index for fast searching across titles and abstracts.

    Args:
        query: Search query (supports FTS5 syntax)
        limit: Maximum results to return
        offset: Skip first N results (for pagination)

    Returns:
        SearchResult with matching works

    Example:
        >>> from openalex_local import search
        >>> results = search("machine learning")
        >>> print(f"Found {results.total} matches")
    """
    if Config.get_mode() == "http":
        client = _get_http_client()
        return client.search(query=query, limit=limit, offset=offset)
    return fts.search(query, limit, offset)


def count(query: str) -> int:
    """
    Count matching works without fetching results.

    Args:
        query: FTS5 search query

    Returns:
        Number of matching works
    """
    if Config.get_mode() == "http":
        client = _get_http_client()
        result = client.search(query=query, limit=1)
        return result.total
    return fts.count(query)


def get(id_or_doi: str) -> Optional[Work]:
    """
    Get a work by OpenAlex ID or DOI.

    Args:
        id_or_doi: OpenAlex ID (e.g., W2741809807) or DOI

    Returns:
        Work object or None if not found

    Example:
        >>> from openalex_local import get
        >>> work = get("W2741809807")
        >>> work = get("10.1038/nature12373")
        >>> print(work.title)
    """
    if Config.get_mode() == "http":
        client = _get_http_client()
        return client.get(id_or_doi)

    db = get_db()

    # Try as OpenAlex ID first
    if id_or_doi.startswith("W") or id_or_doi.startswith("w"):
        data = db.get_work(id_or_doi.upper())
        if data:
            return Work.from_db_row(data)

    # Try as DOI
    data = db.get_work_by_doi(id_or_doi)
    if data:
        return Work.from_db_row(data)

    return None


def get_many(ids: List[str]) -> List[Work]:
    """
    Get multiple works by OpenAlex ID or DOI.

    Args:
        ids: List of OpenAlex IDs or DOIs

    Returns:
        List of Work objects (missing IDs are skipped)
    """
    if Config.get_mode() == "http":
        client = _get_http_client()
        return client.get_many(ids)

    works = []
    for id_or_doi in ids:
        work = get(id_or_doi)
        if work:
            works.append(work)
    return works


def exists(id_or_doi: str) -> bool:
    """
    Check if a work exists in the database.

    Args:
        id_or_doi: OpenAlex ID or DOI

    Returns:
        True if work exists
    """
    if Config.get_mode() == "http":
        client = _get_http_client()
        return client.exists(id_or_doi)

    db = get_db()

    # Try as OpenAlex ID first
    if id_or_doi.startswith("W") or id_or_doi.startswith("w"):
        row = db.fetchone(
            "SELECT 1 FROM works WHERE openalex_id = ?", (id_or_doi.upper(),)
        )
        if row:
            return True

    # Try as DOI
    row = db.fetchone("SELECT 1 FROM works WHERE doi = ?", (id_or_doi,))
    return row is not None


def configure(db_path: str) -> None:
    """
    Configure for local database access.

    Args:
        db_path: Path to OpenAlex SQLite database

    Example:
        >>> from openalex_local import configure
        >>> configure("/path/to/openalex.db")
    """
    Config.set_db_path(db_path)
    close_db()


def configure_http(api_url: str = "http://localhost:31292") -> None:
    """
    Configure for HTTP API access.

    Args:
        api_url: URL of OpenAlex Local API server

    Example:
        >>> from openalex_local import configure_http
        >>> configure_http("http://localhost:31292")
    """
    Config.set_api_url(api_url)


def get_mode() -> str:
    """
    Get current mode.

    Returns:
        "db" or "http"
    """
    return Config.get_mode()


def info() -> dict:
    """
    Get database/API information.

    Returns:
        Dictionary with database stats and mode info

    Raises:
        FileNotFoundError: If no database configured and HTTP mode unavailable
    """
    mode = Config.get_mode()

    if mode == "http":
        client = _get_http_client()
        http_info = client.info()
        return {"mode": "http", "status": "ok", **http_info}

    # DB mode - will raise FileNotFoundError if no database
    db = get_db()

    # Get work count from metadata (fast) or fallback to MAX(rowid) approximation
    work_count = 0
    try:
        row = db.fetchone("SELECT value FROM _metadata WHERE key = 'total_works'")
        if row:
            work_count = int(row["value"])
    except Exception:
        pass

    if work_count == 0:
        # Fallback: use MAX(rowid) as approximation (much faster than COUNT(*))
        try:
            row = db.fetchone("SELECT MAX(rowid) as count FROM works")
            work_count = row["count"] if row else 0
        except Exception:
            work_count = 0

    # Get FTS count from metadata (fast) or fallback
    fts_count = 0
    try:
        row = db.fetchone("SELECT value FROM _metadata WHERE key = 'fts_total_indexed'")
        if row:
            fts_count = int(row["value"])
    except Exception:
        pass

    if fts_count == 0:
        try:
            row = db.fetchone("SELECT MAX(rowid) as count FROM works_fts")
            fts_count = row["count"] if row else 0
        except Exception:
            fts_count = 0

    return {
        "status": "ok",
        "mode": "db",
        "db_path": str(Config.get_db_path()),
        "work_count": work_count,
        "fts_indexed": fts_count,
    }


def enrich(
    results: SearchResult,
    include_abstract: bool = True,
    include_concepts: bool = True,
) -> SearchResult:
    """
    Enrich search results with full metadata.

    This function re-fetches works from the database to ensure all fields
    are populated, including abstract and concepts which may be truncated
    in search results.

    Args:
        results: SearchResult from a search query
        include_abstract: Include full abstract text (default True)
        include_concepts: Include concept/topic data (default True)

    Returns:
        SearchResult with enriched Work objects

    Example:
        >>> results = search("machine learning", limit=10)
        >>> enriched = enrich(results)
        >>> for work in enriched:
        ...     print(work.abstract)  # Full abstract available
    """
    if not results.works:
        return results

    # Get full work data for each work
    ids = [w.openalex_id for w in results.works]
    enriched_works = get_many(ids)

    # If concepts/abstract not wanted, clear them
    if not include_abstract:
        for work in enriched_works:
            work.abstract = None
    if not include_concepts:
        for work in enriched_works:
            work.concepts = []
            work.topics = []

    return SearchResult(
        works=enriched_works,
        total=results.total,
        query=results.query,
        elapsed_ms=results.elapsed_ms,
    )


def enrich_ids(
    ids: List[str],
    include_abstract: bool = True,
    include_concepts: bool = True,
) -> List[Work]:
    """
    Enrich a list of OpenAlex IDs or DOIs with full metadata.

    Args:
        ids: List of OpenAlex IDs (e.g., W2741809807) or DOIs
        include_abstract: Include full abstract text (default True)
        include_concepts: Include concept/topic data (default True)

    Returns:
        List of Work objects with full metadata

    Example:
        >>> ids = ["W2741809807", "10.1038/nature12373"]
        >>> works = enrich_ids(ids)
        >>> for work in works:
        ...     print(f"{work.title}: {work.cited_by_count} citations")
    """
    works = get_many(ids)

    if not include_abstract:
        for work in works:
            work.abstract = None
    if not include_concepts:
        for work in works:
            work.concepts = []
            work.topics = []

    return works
