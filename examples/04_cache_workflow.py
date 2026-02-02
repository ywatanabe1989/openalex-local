#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-02-03 (ywatanabe)"
# File: /home/ywatanabe/proj/openalex-local/examples/04_cache_workflow.py

"""Local caching workflow for offline analysis.

Demonstrates:
- Creating caches from search queries
- Querying cached papers with filters
- Cache statistics and export
"""

from pathlib import Path

try:
    import scitex as stx
    HAS_SCITEX = True
except ImportError:
    HAS_SCITEX = False
    import logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

from openalex_local import cache


def _main(cache_name, query, limit, logger, output_dir=None):
    """Core logic."""
    if output_dir is None:
        output_dir = Path(".")

    # --- Create cache ---
    logger.info("=== Creating Cache ===")
    logger.info(f"Name: {cache_name}")
    logger.info(f"Query: '{query}'")
    logger.info(f"Limit: {limit}")

    if cache.exists(cache_name):
        cache.delete(cache_name)
        logger.info("Deleted existing cache")

    info = cache.create(cache_name, query=query, limit=limit)
    logger.info(f"Created cache with {info.count} papers")
    logger.info("")

    # --- Cache statistics ---
    logger.info("=== Cache Statistics ===")
    stats = cache.stats(cache_name)
    logger.info(f"Total papers: {stats['total']}")
    logger.info(f"Year range: {stats['year_min']} - {stats['year_max']}")
    logger.info(f"Total citations: {stats['citations_total']:,}")
    logger.info(f"Open access: {stats['open_access']} ({stats['open_access_pct']}%)")
    logger.info("")

    # --- Query cache with filters ---
    logger.info("=== Querying Cache ===")
    recent = cache.query(cache_name, year_min=2020, limit=10)
    logger.info(f"Recent (2020+): {len(recent)} papers")

    oa_papers = cache.query(cache_name, is_oa=True, limit=10)
    logger.info(f"Open access: {len(oa_papers)} papers")
    logger.info("")

    # --- Export ---
    logger.info("=== Exporting ===")
    csv_path = output_dir / f"{cache_name}.csv"
    cache.export(cache_name, str(csv_path), format="csv")
    logger.info(f"Exported CSV: {csv_path}")
    logger.info("")

    # --- Cleanup ---
    cache.delete(cache_name)
    logger.info(f"Deleted cache: {cache_name}")

    return 0


if HAS_SCITEX:
    @stx.session
    def main(
        cache_name: str = "example_cache",
        query: str = "machine learning healthcare",
        limit: int = 50,
        CONFIG=stx.INJECTED,
        logger=stx.INJECTED,
    ):
        """Demonstrate cache workflow."""
        output_dir = Path(CONFIG.SDIR_OUT)
        return _main(cache_name, query, limit, logger, output_dir)
else:
    def main(cache_name="example_cache", query="machine learning healthcare", limit=50):
        """Demonstrate cache workflow."""
        logger = logging.getLogger(__name__)
        return _main(cache_name, query, limit, logger)


if __name__ == "__main__":
    main()

# EOF
