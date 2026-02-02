"""Remote API client for openalex_local.

Connects to an OpenAlex Local API server instead of direct database access.
Use this when the database is on a remote server accessible via HTTP.
"""

from typing import Optional

from .base import RemoteClient, DEFAULT_API_URL

# Module-level client singleton
_client: Optional[RemoteClient] = None


def get_client(base_url: str = DEFAULT_API_URL) -> RemoteClient:
    """Get or create singleton remote client."""
    global _client
    if _client is None or _client.base_url != base_url:
        _client = RemoteClient(base_url)
    return _client


def reset_client() -> None:
    """Reset singleton client."""
    global _client
    _client = None


__all__ = [
    "RemoteClient",
    "DEFAULT_API_URL",
    "get_client",
    "reset_client",
]
