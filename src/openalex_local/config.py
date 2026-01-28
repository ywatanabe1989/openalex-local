"""Configuration for openalex_local."""

import os
from pathlib import Path
from typing import Optional

# Default database locations (checked in order)
DEFAULT_DB_PATHS = [
    Path("/home/ywatanabe/proj/openalex-local/data/openalex.db"),
    Path("/home/ywatanabe/proj/openalex_local/data/openalex.db"),
    Path("/mnt/nas_ug/openalex_local/data/openalex.db"),
    Path.home() / ".openalex_local" / "openalex.db",
    Path.cwd() / "data" / "openalex.db",
]


def get_db_path() -> Path:
    """
    Get database path from environment or auto-detect.

    Priority:
    1. OPENALEX_LOCAL_DB environment variable
    2. First existing path from DEFAULT_DB_PATHS

    Returns:
        Path to the database file

    Raises:
        FileNotFoundError: If no database found
    """
    # Check environment variable first
    env_path = os.environ.get("OPENALEX_LOCAL_DB")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
        raise FileNotFoundError(f"OPENALEX_LOCAL_DB path not found: {env_path}")

    # Auto-detect from default locations
    for path in DEFAULT_DB_PATHS:
        if path.exists():
            return path

    raise FileNotFoundError(
        "OpenAlex database not found. Set OPENALEX_LOCAL_DB environment variable "
        f"or place database at one of: {[str(p) for p in DEFAULT_DB_PATHS]}"
    )


# Default port (SciTeX port scheme: 31292 for openalex)
DEFAULT_PORT = 31292
DEFAULT_HOST = "0.0.0.0"


class Config:
    """Configuration container."""

    _db_path: Optional[Path] = None
    _api_url: Optional[str] = None
    _mode: Optional[str] = None  # "db" or "http"
    _port: Optional[int] = None
    _host: Optional[str] = None

    @classmethod
    def get_db_path(cls) -> Path:
        """Get or auto-detect database path."""
        if cls._db_path is None:
            cls._db_path = get_db_path()
        return cls._db_path

    @classmethod
    def set_db_path(cls, path: str | Path) -> None:
        """Set database path explicitly."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Database not found: {path}")
        cls._db_path = path
        cls._mode = "db"

    @classmethod
    def get_api_url(cls) -> str:
        """Get API URL for HTTP mode."""
        if cls._api_url:
            return cls._api_url

        # Check environment variables (scitex priority)
        for var in [
            "SCITEX_SCHOLAR_OPENALEX_API_URL",
            "OPENALEX_LOCAL_API_URL",
        ]:
            url = os.environ.get(var)
            if url:
                return url

        return "http://localhost:31292"

    @classmethod
    def set_api_url(cls, url: str) -> None:
        """Set API URL explicitly."""
        cls._api_url = url
        cls._mode = "http"

    @classmethod
    def get_mode(cls) -> str:
        """
        Get current mode.

        Priority:
        1. Explicitly set mode
        2. OPENALEX_LOCAL_MODE environment variable
        3. Auto-detect based on available config

        Returns:
            "db" or "http"
        """
        if cls._mode:
            return cls._mode

        # Check environment variable
        env_mode = os.environ.get("OPENALEX_LOCAL_MODE", "").lower()
        if env_mode in ("db", "http"):
            return env_mode

        # Check if API URL is set
        if os.environ.get("OPENALEX_LOCAL_API_URL"):
            return "http"

        # Default to db mode (will raise FileNotFoundError if no database)
        return "db"

    @classmethod
    def get_port(cls) -> int:
        """Get server port."""
        if cls._port:
            return cls._port

        # Check environment variables (scitex priority)
        for var in [
            "SCITEX_SCHOLAR_OPENALEX_PORT",
            "OPENALEX_LOCAL_PORT",
        ]:
            port = os.environ.get(var)
            if port:
                return int(port)

        return DEFAULT_PORT

    @classmethod
    def set_port(cls, port: int) -> None:
        """Set server port explicitly."""
        cls._port = port

    @classmethod
    def get_host(cls) -> str:
        """Get server host."""
        if cls._host:
            return cls._host

        # Check environment variables (scitex priority)
        for var in [
            "SCITEX_SCHOLAR_OPENALEX_HOST",
            "OPENALEX_LOCAL_HOST",
        ]:
            host = os.environ.get(var)
            if host:
                return host

        return DEFAULT_HOST

    @classmethod
    def set_host(cls, host: str) -> None:
        """Set server host explicitly."""
        cls._host = host

    @classmethod
    def reset(cls) -> None:
        """Reset configuration (for testing)."""
        cls._db_path = None
        cls._api_url = None
        cls._mode = None
        cls._port = None
        cls._host = None
