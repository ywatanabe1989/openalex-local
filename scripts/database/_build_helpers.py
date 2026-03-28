#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shared helpers for OpenAlex database build and update scripts.

Extracted from 02_build_database.py for reuse in 10_differential_update.py.
"""

import json
from typing import Any, Dict, List, Optional


def reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
    """Reconstruct abstract from OpenAlex inverted index format."""
    if not inverted_index:
        return None
    try:
        words = sorted(
            [(pos, word) for word, positions in inverted_index.items() for pos in positions]
        )
        return " ".join(word for _, word in words)
    except Exception:
        return None


def extract_authors(authorships: List[Dict]) -> List[str]:
    """Extract author names from authorships list."""
    authors = []
    for authorship in authorships or []:
        author = authorship.get("author", {})
        name = author.get("display_name")
        if name:
            authors.append(name)
    return authors


def extract_concepts(concepts: List[Dict], limit: int = 5) -> List[Dict[str, Any]]:
    """Extract top concepts with name and score."""
    return [
        {"name": c.get("display_name"), "score": c.get("score")}
        for c in (concepts or [])[:limit]
    ]


def extract_topics(topics: List[Dict], limit: int = 3) -> List[Dict[str, Any]]:
    """Extract top topics with name and subfield."""
    return [
        {
            "name": t.get("display_name"),
            "subfield": t.get("subfield", {}).get("display_name") if t.get("subfield") else None,
            "field": t.get("field", {}).get("display_name") if t.get("field") else None,
        }
        for t in (topics or [])[:limit]
    ]


def parse_work(data: Dict[str, Any], store_raw: bool = False) -> Dict[str, Any]:
    """Parse OpenAlex work JSON into database record."""
    openalex_id = data.get("id", "").replace("https://openalex.org/", "")

    doi = data.get("doi", "").replace("https://doi.org/", "") if data.get("doi") else None

    primary_location = data.get("primary_location") or {}
    source_info = primary_location.get("source") or {}
    source = source_info.get("display_name")
    source_id = (source_info.get("id") or "").replace("https://openalex.org/", "") if source_info.get("id") else None
    issns = source_info.get("issn") or []
    issn = issns[0] if issns else None
    publisher = source_info.get("host_organization_name")

    biblio = data.get("biblio") or {}
    oa_info = data.get("open_access") or {}

    authors = extract_authors(data.get("authorships", []))
    concepts = extract_concepts(data.get("concepts", []))
    topics = extract_topics(data.get("topics", []))
    referenced_works = [
        r.replace("https://openalex.org/", "") for r in (data.get("referenced_works") or [])
    ]

    return {
        "openalex_id": openalex_id,
        "doi": doi,
        "title": data.get("title") or data.get("display_name"),
        "abstract": reconstruct_abstract(data.get("abstract_inverted_index")),
        "year": data.get("publication_year"),
        "publication_date": data.get("publication_date"),
        "type": data.get("type"),
        "language": data.get("language"),
        "source": source,
        "source_id": source_id,
        "issn": issn,
        "volume": biblio.get("volume"),
        "issue": biblio.get("issue"),
        "first_page": biblio.get("first_page"),
        "last_page": biblio.get("last_page"),
        "publisher": publisher,
        "cited_by_count": data.get("cited_by_count", 0),
        "is_oa": 1 if oa_info.get("is_oa") else 0,
        "oa_status": oa_info.get("oa_status"),
        "oa_url": oa_info.get("oa_url"),
        "authors_json": json.dumps(authors) if authors else None,
        "concepts_json": json.dumps(concepts) if concepts else None,
        "topics_json": json.dumps(topics) if topics else None,
        "referenced_works_json": json.dumps(referenced_works) if referenced_works else None,
        "raw_json": json.dumps(data) if store_raw else None,
    }


# EOF
