"""
OpenAlex Local - Local OpenAlex database with 284M+ works and semantic search.

Example:
    >>> from openalex_local import search, get
    >>> results = search("machine learning neural networks")
    >>> work = get("W2741809807")  # OpenAlex ID
    >>> work = get("10.1038/nature12373")  # or DOI
"""

__version__ = "0.3.0"

from ._core import (
    SearchResult,
    Work,
    configure,
    count,
    enrich,
    enrich_ids,
    exists,
    get,
    get_many,
    get_mode,
    info,
    search,
)

# Jobs module (public functions only)
from . import jobs

# Async module
from . import aio

# Cache module
from . import cache

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
    # Models
    "Work",
    "SearchResult",
    # Jobs
    "jobs",
    # Async
    "aio",
    # Cache
    "cache",
]
