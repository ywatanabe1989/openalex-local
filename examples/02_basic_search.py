#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-02-03 (ywatanabe)"
# File: /home/ywatanabe/proj/openalex-local/examples/01_basic_search.py

"""Basic search functionality with openalex-local.

Demonstrates:
- Full-text search across 459M+ works
- Accessing work metadata (title, authors, DOI, etc.)
- Pagination with limit and offset

Outputs saved to ./script_out/FINISHED_*/ (when using scitex)
"""

try:
    import scitex as stx
    HAS_SCITEX = True
except ImportError:
    HAS_SCITEX = False
    import logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

from openalex_local import search


def _main(query, limit, logger):
    """Core logic."""
    logger.info(f"Searching for: '{query}'")
    logger.info(f"Limit: {limit}")

    results = search(query, limit=limit)

    logger.info(f"Found {results.total:,} matches in {results.elapsed_ms:.1f}ms")
    logger.info("")

    for i, work in enumerate(results.works, 1):
        logger.info(f"{i}. {work.title} ({work.year})")
        logger.info(f"   DOI: {work.doi or 'N/A'}")
        logger.info(f"   Journal: {work.source or 'N/A'}")
        if work.authors:
            authors_str = ", ".join(work.authors[:3])
            if len(work.authors) > 3:
                authors_str += f" (+{len(work.authors) - 3} more)"
            logger.info(f"   Authors: {authors_str}")
        logger.info("")

    return 0


if HAS_SCITEX:
    @stx.session
    def main(
        query: str = "machine learning neural networks",
        limit: int = 5,
        CONFIG=stx.INJECTED,
        logger=stx.INJECTED,
    ):
        """Search OpenAlex database for scholarly works."""
        return _main(query, limit, logger)
else:
    def main(query="machine learning neural networks", limit=5):
        """Search OpenAlex database for scholarly works."""
        logger = logging.getLogger(__name__)
        return _main(query, limit, logger)


if __name__ == "__main__":
    main()

# EOF
