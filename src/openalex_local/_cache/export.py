"""Cache export functionality."""

import csv
import json
from pathlib import Path
from typing import List, Dict

from .core import load


def export(
    name: str,
    output_path: str,
    format: str = "json",
) -> str:
    """
    Export a cache to a file.

    Args:
        name: Cache name
        output_path: Output file path
        format: Export format ("json", "csv", "bibtex")

    Returns:
        Path to exported file
    """
    works = load(name)
    output = Path(output_path)

    if format == "json":
        _export_json(works, output)
    elif format == "csv":
        _export_csv(works, output)
    elif format == "bibtex":
        _export_bibtex(works, output)
    else:
        raise ValueError(f"Unknown format: {format}. Use 'json', 'csv', or 'bibtex'")

    return str(output)


def _export_json(works: List[Dict], output: Path) -> None:
    """Export to JSON format."""
    with open(output, "w", encoding="utf-8") as f:
        json.dump(works, f, ensure_ascii=False, indent=2)


def _export_csv(works: List[Dict], output: Path) -> None:
    """Export to CSV format."""
    if not works:
        output.write_text("")
        return

    # Get all unique keys
    keys = set()
    for w in works:
        keys.update(w.keys())

    # Prioritize common fields
    priority = ["openalex_id", "doi", "title", "authors", "year", "source", "cited_by_count"]
    fieldnames = [k for k in priority if k in keys]
    fieldnames.extend(sorted(k for k in keys if k not in priority))

    with open(output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for w in works:
            row = {}
            for k, v in w.items():
                if isinstance(v, list):
                    row[k] = "; ".join(str(x) for x in v)
                else:
                    row[k] = v
            writer.writerow(row)


def _export_bibtex(works: List[Dict], output: Path) -> None:
    """Export to BibTeX format."""
    from .._core.models import Work

    lines = []
    for w in works:
        work = Work(
            openalex_id=w.get("openalex_id", ""),
            doi=w.get("doi"),
            title=w.get("title"),
            authors=w.get("authors", []),
            year=w.get("year"),
            source=w.get("source"),
            volume=w.get("volume"),
            issue=w.get("issue"),
            pages=w.get("pages"),
            publisher=w.get("publisher"),
            type=w.get("type"),
            oa_url=w.get("oa_url"),
        )
        lines.append(work.citation("bibtex"))
        lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")
