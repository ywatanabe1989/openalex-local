"""Cache data models."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class CacheInfo:
    """Information about a cache."""

    name: str
    path: str
    count: int
    created_at: str
    updated_at: str
    queries: List[str] = field(default_factory=list)
    size_bytes: int = 0
