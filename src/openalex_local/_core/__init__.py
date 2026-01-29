#!/usr/bin/env python3
"""Internal core modules - public API only."""

from .api import (
    SearchResult,
    Work,
    configure,
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
    "get_mode",
    # Models
    "Work",
    "SearchResult",
]

# EOF
