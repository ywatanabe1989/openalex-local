#!/usr/bin/env python3
# Timestamp: 2026-01-29
"""Configuration for openalex_local."""

import os as _os
from pathlib import Path as _Path
from typing import Optional as _Optional

# Default database locations (checked in order)
DEFAULT_DB_PATHS = [
    _Path("/home/ywatanabe/proj/openalex-local/data/openalex.db"),
    _Path("/home/ywatanabe/proj/openalex_local/data/openalex.db"),
    _Path("/mnt/nas_ug/openalex_local/data/openalex.db"),
    _Path.home() / ".openalex_local" / "openalex.db",
    _Path.cwd() / "data" / "openalex.db",
]


def get_db_path() -> _Path:
    """Get database path from environment or auto-detect."""
    env_path = _os.environ.get("OPENALEX_LOCAL_DB")
    if env_path:
        path = _Path(env_path)
        if path.exists():
            return path
        raise FileNotFoundError(f"OPENALEX_LOCAL_DB path not found: {env_path}")

    for path in DEFAULT_DB_PATHS:
        if path.exists():
            return path

    raise FileNotFoundError(
        "OpenAlex database not found. Set OPENALEX_LOCAL_DB environment variable."
    )


DEFAULT_PORT = 31292
DEFAULT_HOST = "0.0.0.0"


class Config:
    """Configuration container."""

    _db_path: _Optional[_Path] = None
    _api_url: _Optional[str] = None
    _mode: str = "auto"  # "auto", "db", or "http"

    @classmethod
    def get_db_path(cls) -> _Path:
        if cls._db_path is None:
            cls._db_path = get_db_path()
        return cls._db_path

    @classmethod
    def set_db_path(cls, path: str) -> None:
        p = _Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Database not found: {path}")
        cls._db_path = p
        cls._mode = "db"

    @classmethod
    def get_api_url(cls) -> str:
        if cls._api_url:
            return cls._api_url
        return _os.environ.get(
            "OPENALEX_LOCAL_API_URL", f"http://localhost:{DEFAULT_PORT}"
        )

    @classmethod
    def set_api_url(cls, url: str) -> None:
        cls._api_url = url.rstrip("/")
        cls._mode = "http"

    @classmethod
    def set_mode(cls, mode: str) -> None:
        """Set mode explicitly: 'db', 'http', or 'auto'."""
        if mode not in ("auto", "db", "http"):
            raise ValueError(f"Invalid mode: {mode}. Use 'auto', 'db', or 'http'")
        cls._mode = mode

    @classmethod
    def get_mode(cls) -> str:
        """
        Get current mode.

        Returns:
            "db" if using direct database access
            "http" if using HTTP API
        """
        if cls._mode == "auto":
            # Check environment variable for explicit mode
            env_mode = _os.environ.get("OPENALEX_LOCAL_MODE", "").lower()
            if env_mode in ("http", "remote", "api"):
                return "http"
            if env_mode in ("db", "local"):
                return "db"

            # Check if API URL is set explicitly
            if cls._api_url or _os.environ.get("OPENALEX_LOCAL_API_URL"):
                return "http"

            # Check if local database exists
            try:
                get_db_path()
                return "db"
            except FileNotFoundError:
                # No local DB, try http
                return "http"

        return cls._mode

    @classmethod
    def reset(cls) -> None:
        cls._db_path = None
        cls._api_url = None
        cls._mode = "auto"


# EOF
