"""Cache module for openalex_local.

Provides local caching of search results and works for offline analysis.

Example:
    >>> from openalex_local import cache
    >>> # Create a cache from search
    >>> info = cache.create("ml_papers", query="machine learning", limit=1000)
    >>> print(f"Cached {info.count} papers")
    >>>
    >>> # Query the cache
    >>> papers = cache.query("ml_papers", year_min=2020)
    >>> # Get IDs for further processing
    >>> ids = cache.query_ids("ml_papers")
"""

from .models import CacheInfo
from .core import (
    create,
    append,
    load,
    query,
    query_ids,
    stats,
    info,
    exists,
    list_caches,
    delete,
)
from .export import export

__all__ = [
    "CacheInfo",
    "create",
    "append",
    "load",
    "query",
    "query_ids",
    "stats",
    "info",
    "exists",
    "list_caches",
    "delete",
    "export",
]
