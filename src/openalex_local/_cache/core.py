"""Core cache operations."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import CacheInfo
from .utils import (
    ensure_cache_dir,
    get_cache_dir,
    get_cache_path,
    validate_cache_name,
)


def _load_cache_raw(name: str) -> Dict[str, Any]:
    """Load raw cache data."""
    path = get_cache_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Cache not found: {name}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_cache_raw(name: str, data: Dict[str, Any]) -> Path:
    """Save raw cache data."""
    ensure_cache_dir()
    path = get_cache_path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def create(
    name: str,
    query: Optional[str] = None,
    ids: Optional[List[str]] = None,
    papers: Optional[List[Dict]] = None,
    limit: int = 1000,
) -> CacheInfo:
    """
    Create a new cache.

    Args:
        name: Cache name (will be sanitized for filesystem)
        query: Search query to populate cache
        ids: List of OpenAlex IDs or DOIs to cache
        papers: Pre-fetched paper dictionaries to cache
        limit: Maximum papers to cache from query

    Returns:
        CacheInfo with cache details
    """
    from .. import search, get_many

    error = validate_cache_name(name)
    if error:
        raise ValueError(error)

    works_data = []
    queries = []

    if query:
        results = search(query, limit=limit)
        works_data.extend([w.to_dict() for w in results.works])
        queries.append(query)

    if ids:
        works = get_many(ids)
        works_data.extend([w.to_dict() for w in works])

    if papers:
        works_data.extend(papers)

    # Remove duplicates by openalex_id
    seen = set()
    unique_works = []
    for w in works_data:
        oid = w.get("openalex_id")
        if oid and oid not in seen:
            seen.add(oid)
            unique_works.append(w)

    now = datetime.utcnow().isoformat()
    cache_data = {
        "name": name,
        "created_at": now,
        "updated_at": now,
        "queries": queries,
        "works": unique_works,
    }

    path = _save_cache_raw(name, cache_data)

    return CacheInfo(
        name=name,
        path=str(path),
        count=len(unique_works),
        created_at=now,
        updated_at=now,
        queries=queries,
        size_bytes=path.stat().st_size,
    )


def append(
    name: str,
    query: Optional[str] = None,
    ids: Optional[List[str]] = None,
    limit: int = 1000,
) -> CacheInfo:
    """Append works to an existing cache."""
    from .. import search, get_many

    cache_data = _load_cache_raw(name)
    existing_ids = {w.get("openalex_id") for w in cache_data.get("works", [])}

    new_works = []
    queries = cache_data.get("queries", [])

    if query:
        results = search(query, limit=limit)
        for w in results.works:
            if w.openalex_id not in existing_ids:
                new_works.append(w.to_dict())
                existing_ids.add(w.openalex_id)
        if query not in queries:
            queries.append(query)

    if ids:
        works = get_many(ids)
        for w in works:
            if w.openalex_id not in existing_ids:
                new_works.append(w.to_dict())
                existing_ids.add(w.openalex_id)

    cache_data["works"].extend(new_works)
    cache_data["queries"] = queries
    cache_data["updated_at"] = datetime.utcnow().isoformat()

    path = _save_cache_raw(name, cache_data)

    return CacheInfo(
        name=name,
        path=str(path),
        count=len(cache_data["works"]),
        created_at=cache_data.get("created_at", ""),
        updated_at=cache_data["updated_at"],
        queries=queries,
        size_bytes=path.stat().st_size,
    )


def load(name: str) -> List[Dict]:
    """Load all works from a cache."""
    cache_data = _load_cache_raw(name)
    return cache_data.get("works", [])


def query(
    name: str,
    fields: Optional[List[str]] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    cited_min: Optional[int] = None,
    has_abstract: Optional[bool] = None,
    is_oa: Optional[bool] = None,
    source: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict]:
    """Query a cache with filters."""
    works = load(name)
    results = []

    for w in works:
        if year_min and (w.get("year") or 0) < year_min:
            continue
        if year_max and (w.get("year") or 9999) > year_max:
            continue
        if cited_min and (w.get("cited_by_count") or 0) < cited_min:
            continue
        if has_abstract is not None:
            has_abs = bool(w.get("abstract"))
            if has_abstract != has_abs:
                continue
        if is_oa is not None and w.get("is_oa") != is_oa:
            continue
        if source and source.lower() not in (w.get("source") or "").lower():
            continue

        if fields:
            w = {k: w.get(k) for k in fields}

        results.append(w)

        if limit and len(results) >= limit:
            break

    return results


def query_ids(name: str) -> List[str]:
    """Get all OpenAlex IDs from a cache."""
    works = load(name)
    return [w.get("openalex_id") for w in works if w.get("openalex_id")]


def stats(name: str) -> Dict[str, Any]:
    """Get statistics for a cache."""
    cache_data = _load_cache_raw(name)
    works = cache_data.get("works", [])

    if not works:
        return {
            "name": name, "total": 0, "year_min": None, "year_max": None,
            "citations_total": 0, "citations_mean": 0,
            "with_abstract": 0, "open_access": 0, "sources": [],
        }

    years = [w.get("year") for w in works if w.get("year")]
    citations = [w.get("cited_by_count") or 0 for w in works]
    abstracts = sum(1 for w in works if w.get("abstract"))
    oa_count = sum(1 for w in works if w.get("is_oa"))

    source_counts: Dict[str, int] = {}
    for w in works:
        src = w.get("source")
        if src:
            source_counts[src] = source_counts.get(src, 0) + 1
    top_sources = sorted(source_counts.items(), key=lambda x: -x[1])[:10]

    return {
        "name": name,
        "total": len(works),
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "citations_total": sum(citations),
        "citations_mean": sum(citations) / len(works) if works else 0,
        "with_abstract": abstracts,
        "with_abstract_pct": round(100 * abstracts / len(works), 1) if works else 0,
        "open_access": oa_count,
        "open_access_pct": round(100 * oa_count / len(works), 1) if works else 0,
        "sources": top_sources,
        "queries": cache_data.get("queries", []),
        "created_at": cache_data.get("created_at"),
        "updated_at": cache_data.get("updated_at"),
    }


def info(name: str) -> CacheInfo:
    """Get cache info."""
    path = get_cache_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Cache not found: {name}")

    cache_data = _load_cache_raw(name)

    return CacheInfo(
        name=name,
        path=str(path),
        count=len(cache_data.get("works", [])),
        created_at=cache_data.get("created_at", ""),
        updated_at=cache_data.get("updated_at", ""),
        queries=cache_data.get("queries", []),
        size_bytes=path.stat().st_size,
    )


def exists(name: str) -> bool:
    """Check if a cache exists."""
    return get_cache_path(name).exists()


def list_caches() -> List[CacheInfo]:
    """List all caches."""
    cache_dir = get_cache_dir()
    if not cache_dir.exists():
        return []

    caches = []
    for path in cache_dir.glob("*.json"):
        try:
            cache_info = info(path.stem)
            caches.append(cache_info)
        except (json.JSONDecodeError, KeyError):
            continue

    return sorted(caches, key=lambda c: c.updated_at, reverse=True)


def delete(name: str) -> bool:
    """Delete a cache."""
    path = get_cache_path(name)
    if path.exists():
        path.unlink()
        return True
    return False
