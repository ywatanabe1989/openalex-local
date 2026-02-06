#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-02-03 (ywatanabe)"
# File: /home/ywatanabe/proj/openalex-local/examples/06_enrich_workflow.py

"""Enrich search results with full metadata.

Demonstrates:
- enrich() to add full metadata to search results
- enrich_ids() to fetch complete works from IDs
"""

try:
    import scitex as stx
    HAS_SCITEX = True
except ImportError:
    HAS_SCITEX = False
    import logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

from openalex_local import search, enrich, enrich_ids


def _main(query, limit, logger):
    """Core logic."""
    # --- Search and enrich ---
    logger.info("=== Search and Enrich ===")
    logger.info(f"Query: '{query}'")
    logger.info(f"Limit: {limit}")
    logger.info("")

    results = search(query, limit=limit)
    logger.info(f"Found {results.total:,} matches in {results.elapsed_ms:.1f}ms")
    logger.info("")

    enriched = enrich(results, include_abstract=True, include_concepts=True)

    for i, work in enumerate(enriched.works, 1):
        logger.info(f"{i}. {work.title}")
        logger.info(f"   Year: {work.year}, Citations: {work.cited_by_count or 0:,}")

        if work.concepts:
            concept_names = [c.get("name", "") for c in work.concepts[:3]]
            logger.info(f"   Concepts: {', '.join(concept_names)}")

        if work.abstract:
            abstract_preview = work.abstract[:100]
            if len(work.abstract) > 100:
                abstract_preview += "..."
            logger.info(f"   Abstract: {abstract_preview}")
        logger.info("")

    # --- Enrich by IDs ---
    logger.info("=== Enrich by IDs ===")
    sample_ids = ["W2741809807", "10.1038/nature14539"]
    logger.info(f"IDs: {sample_ids}")
    logger.info("")

    works = enrich_ids(sample_ids)
    logger.info(f"Fetched {len(works)} works")
    for work in works:
        logger.info(f"  - {work.title[:50]}... ({work.year})")
    logger.info("")

    return 0


if HAS_SCITEX:
    @stx.session
    def main(
        query: str = "CRISPR therapeutics",
        limit: int = 3,
        CONFIG=stx.INJECTED,
        logger=stx.INJECTED,
    ):
        """Demonstrate enrich workflow."""
        return _main(query, limit, logger)
else:
    def main(query="CRISPR therapeutics", limit=3):
        """Demonstrate enrich workflow."""
        logger = logging.getLogger(__name__)
        return _main(query, limit, logger)


if __name__ == "__main__":
    main()

# EOF
