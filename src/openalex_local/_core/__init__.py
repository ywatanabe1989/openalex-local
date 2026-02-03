#!/usr/bin/env python3
"""Internal core modules - public API only."""

from .api import (
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
from .export import SUPPORTED_FORMATS, save

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
    # Export
    "save",
    "SUPPORTED_FORMATS",
]

# EOF
