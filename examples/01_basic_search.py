#!/usr/bin/env python3
"""Example: Basic search functionality.

Demonstrates:
- Full-text search across works
- Accessing work metadata
"""

from openalex_local import search

# Search for papers
results = search("machine learning neural networks", limit=5)

print(f"Found {results.total:,} matches in {results.elapsed_ms:.1f}ms\n")

for i, work in enumerate(results.works, 1):
    print(f"{i}. {work.title} ({work.year})")
    print(f"   DOI: {work.doi or 'N/A'}")
    print(f"   Journal: {work.source or 'N/A'}")
    if work.authors:
        print(f"   Authors: {', '.join(work.authors[:3])}")
    print()
