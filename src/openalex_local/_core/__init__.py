#!/usr/bin/env python3
"""Internal core modules."""

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
from .config import Config
from .db import Database, close_db, get_db
from .fts import count as fts_count
from .fts import search as fts_search
from .models import SearchResult, Work

__all__ = [
    # API
    "search",
    "count",
    "get",
    "get_many",
    "exists",
    "configure",
    "configure_http",
    "get_mode",
    "info",
    # Models
    "Work",
    "SearchResult",
    # Config
    "Config",
    # DB
    "Database",
    "get_db",
    "close_db",
    # FTS
    "fts_search",
    "fts_count",
]

# EOF
