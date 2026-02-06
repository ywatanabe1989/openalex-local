"""Export functionality for Work and SearchResult objects.

Supports multiple output formats:
- text: Human-readable formatted text
- json: JSON format with all fields
- bibtex: BibTeX bibliography format
"""

import json as _json
from pathlib import Path as _Path
from typing import TYPE_CHECKING, List, Optional, Union

if TYPE_CHECKING:
    from .models import SearchResult, Work

__all__ = [
    "save",
    "export_text",
    "export_json",
    "export_bibtex",
    "SUPPORTED_FORMATS",
]

SUPPORTED_FORMATS = ["text", "json", "bibtex"]


def work_to_text(work: "Work", include_abstract: bool = False) -> str:
    """Convert a Work to human-readable text format.

    Args:
        work: Work object to convert
        include_abstract: Whether to include abstract

    Returns:
        Formatted text string
    """
    lines = []

    # Title
    title = work.title or "Untitled"
    year = f"({work.year})" if work.year else ""
    lines.append(f"{title} {year}".strip())

    # Authors
    if work.authors:
        authors_str = ", ".join(work.authors[:5])
        if len(work.authors) > 5:
            authors_str += f" et al. ({len(work.authors)} authors)"
        lines.append(f"Authors: {authors_str}")

    # Journal and identifiers
    if work.source:
        source_line = f"Journal: {work.source}"
        if work.volume:
            source_line += f", {work.volume}"
            if work.issue:
                source_line += f"({work.issue})"
        if work.pages:
            source_line += f", {work.pages}"
        lines.append(source_line)

    if work.doi:
        lines.append(f"DOI: {work.doi}")

    lines.append(f"OpenAlex ID: {work.openalex_id}")

    # Citation count and impact factor
    if work.cited_by_count is not None:
        lines.append(f"Citations: {work.cited_by_count}")
    if work.scitex_if is not None:
        lines.append(f"SciTeX IF (OpenAlex): {work.scitex_if:.1f}")

    # Open access
    if work.is_oa:
        lines.append(f"Open Access: {work.oa_url or 'Yes'}")

    # Abstract
    if include_abstract and work.abstract:
        lines.append(f"Abstract: {work.abstract}")

    return "\n".join(lines)


def export_text(
    works: List["Work"],
    include_abstract: bool = False,
    query: Optional[str] = None,
    total: Optional[int] = None,
    elapsed_ms: Optional[float] = None,
) -> str:
    """Export works to text format.

    Args:
        works: List of Work objects
        include_abstract: Whether to include abstracts
        query: Original search query (for header)
        total: Total number of matches
        elapsed_ms: Search time in milliseconds

    Returns:
        Formatted text string
    """
    lines = []

    # Header
    if query is not None:
        lines.append(f"Search: {query}")
        if total is not None:
            lines.append(f"Found: {total:,} matches")
        if elapsed_ms is not None:
            lines.append(f"Time: {elapsed_ms:.1f}ms")
        lines.append("")
        lines.append("=" * 60)
        lines.append("")

    # Works
    for i, work in enumerate(works, 1):
        lines.append(f"[{i}]")
        lines.append(work_to_text(work, include_abstract=include_abstract))
        lines.append("")
        lines.append("-" * 40)
        lines.append("")

    return "\n".join(lines)


def export_json(
    works: List["Work"],
    query: Optional[str] = None,
    total: Optional[int] = None,
    elapsed_ms: Optional[float] = None,
    indent: int = 2,
) -> str:
    """Export works to JSON format.

    Args:
        works: List of Work objects
        query: Original search query
        total: Total number of matches
        elapsed_ms: Search time in milliseconds
        indent: JSON indentation

    Returns:
        JSON string
    """
    data = {
        "works": [w.to_dict() for w in works],
    }

    if query is not None:
        data["query"] = query
    if total is not None:
        data["total"] = total
    if elapsed_ms is not None:
        data["elapsed_ms"] = elapsed_ms

    return _json.dumps(data, indent=indent, ensure_ascii=False)


def export_bibtex(works: List["Work"]) -> str:
    """Export works to BibTeX format.

    Args:
        works: List of Work objects

    Returns:
        BibTeX string with all entries
    """
    entries = [w.citation("bibtex") for w in works]
    return "\n\n".join(entries)


def save(
    data: Union["Work", "SearchResult", List["Work"]],
    path: Union[str, _Path],
    format: str = "json",
    include_abstract: bool = True,
) -> str:
    """Save Work(s) or SearchResult to a file.

    Args:
        data: Work, SearchResult, or list of Works to save
        path: Output file path
        format: Output format ("text", "json", "bibtex")
        include_abstract: Include abstracts in text format

    Returns:
        Path to saved file

    Raises:
        ValueError: If format is not supported

    Examples:
        >>> from openalex_local import search, save
        >>> results = search("machine learning", limit=10)
        >>> save(results, "results.json")
        >>> save(results, "results.bib", format="bibtex")
        >>> save(results, "results.txt", format="text")
    """
    from .models import SearchResult, Work

    if format not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format: {format}. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )

    path = _Path(path)

    # Extract works and metadata
    if isinstance(data, Work):
        works = [data]
        query = None
        total = None
        elapsed_ms = None
    elif isinstance(data, SearchResult):
        works = data.works
        query = data.query
        total = data.total
        elapsed_ms = data.elapsed_ms
    elif isinstance(data, list):
        works = data
        query = None
        total = len(data)
        elapsed_ms = None
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")

    # Generate content
    if format == "text":
        content = export_text(
            works,
            include_abstract=include_abstract,
            query=query,
            total=total,
            elapsed_ms=elapsed_ms,
        )
    elif format == "json":
        content = export_json(
            works,
            query=query,
            total=total,
            elapsed_ms=elapsed_ms,
        )
    elif format == "bibtex":
        content = export_bibtex(works)
    else:
        raise ValueError(f"Unsupported format: {format}")

    # Write to file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    return str(path)
