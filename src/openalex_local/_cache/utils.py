"""Cache utilities for openalex_local."""

import os
import re
from pathlib import Path
from typing import Optional

from .._core.paths import get_cache_dir as _get_scitex_cache_dir


def get_cache_dir() -> Path:
    """Get cache directory from environment or default.

    Respects ``$OPENALEX_LOCAL_CACHE_DIR`` (env override); falls back to
    the canonical scitex layout: ``~/.scitex/openalex-local/runtime/cache/``
    (or ``$SCITEX_DIR/openalex-local/runtime/cache/`` when ``$SCITEX_DIR`` is
    set).
    """
    env_dir = os.environ.get("OPENALEX_LOCAL_CACHE_DIR")
    if env_dir:
        return Path(env_dir)
    return _get_scitex_cache_dir()


def sanitize_cache_name(name: str) -> str:
    """
    Sanitize cache name for filesystem safety.

    Args:
        name: Raw cache name

    Returns:
        Sanitized cache name

    Example:
        >>> sanitize_cache_name("my cache/name!")
        'my_cache_name_'
    """
    # Replace non-alphanumeric characters (except - and _) with underscore
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")
    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    # Ensure not empty
    if not sanitized:
        sanitized = "cache"
    return sanitized


def get_cache_path(name: str) -> Path:
    """
    Get full path to cache file.

    Args:
        name: Cache name

    Returns:
        Path to cache JSON file
    """
    cache_dir = get_cache_dir()
    safe_name = sanitize_cache_name(name)
    return cache_dir / f"{safe_name}.json"


def ensure_cache_dir() -> Path:
    """Ensure cache directory exists."""
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def validate_cache_name(name: str) -> Optional[str]:
    """
    Validate cache name and return error message if invalid.

    Args:
        name: Cache name to validate

    Returns:
        Error message if invalid, None if valid
    """
    if not name:
        return "Cache name cannot be empty"
    if len(name) > 100:
        return "Cache name too long (max 100 characters)"
    if name.startswith("."):
        return "Cache name cannot start with '.'"
    return None
