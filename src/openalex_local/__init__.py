"""
OpenAlex Local - Local OpenAlex database with 284M+ works and semantic search.

Example:
    >>> from openalex_local import search, get
    >>> results = search("machine learning neural networks")
    >>> work = get("W2741809807")  # OpenAlex ID
    >>> work = get("10.1038/nature12373")  # or DOI
"""

__version__ = "0.2.0"

from .api import (
    Config,
    SearchResult,
    Work,
    configure,
    configure_http,
    count,
    exists,
    get,
    get_many,
    get_mode,
    info,
    search,
)

__all__ = [
    # Core functions
    "search",
    "count",
    "get",
    "get_many",
    "exists",
    "info",
    # Configuration
    "configure",
    "configure_http",
    "get_mode",
    # Classes
    "Work",
    "SearchResult",
    "Config",
]
