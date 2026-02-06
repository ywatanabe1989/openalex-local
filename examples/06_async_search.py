#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-02-03 (ywatanabe)"
# File: /home/ywatanabe/proj/openalex-local/examples/05_async_search.py

"""Async concurrent search with openalex-local.

Demonstrates:
- Async API for non-blocking database access
- Concurrent search with search_many()
- Concurrent count with count_many()
"""

import asyncio

try:
    import scitex as stx
    HAS_SCITEX = True
except ImportError:
    HAS_SCITEX = False
    import logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

from openalex_local import aio


async def run_async_demo(logger):
    """Run async demonstration."""

    # --- Single async search ---
    logger.info("=== Single Async Search ===")
    results = await aio.search("quantum computing", limit=5)
    logger.info(f"Found {results.total:,} matches")
    for w in results.works[:3]:
        logger.info(f"  - {w.title[:50]}... ({w.year})")
    logger.info("")

    # --- Concurrent searches ---
    logger.info("=== Concurrent Searches ===")
    queries = ["machine learning", "neural networks", "deep learning"]
    logger.info(f"Running {len(queries)} searches concurrently...")

    results_list = await aio.search_many(queries, limit=3)

    for query, result in zip(queries, results_list):
        logger.info(f"  '{query}': {result.total:,} matches")
    logger.info("")

    # --- Concurrent counts ---
    logger.info("=== Concurrent Counts ===")
    counts = await aio.count_many(queries)

    for query, count in counts.items():
        logger.info(f"  '{query}': {count:,}")
    logger.info("")

    # --- Get work by ID ---
    logger.info("=== Async Get ===")
    work = await aio.get("10.7717/peerj.4375")
    if work:
        logger.info(f"Title: {work.title}")
        logger.info(f"Citations: {work.cited_by_count:,}")
    logger.info("")


def _main(logger):
    """Core logic."""
    logger.info("OpenAlex Local - Async API Demo")
    logger.info("")
    asyncio.run(run_async_demo(logger))
    return 0


if HAS_SCITEX:
    @stx.session
    def main(CONFIG=stx.INJECTED, logger=stx.INJECTED):
        """Run async search demonstrations."""
        return _main(logger)
else:
    def main():
        """Run async search demonstrations."""
        logger = logging.getLogger(__name__)
        return _main(logger)


if __name__ == "__main__":
    main()

# EOF
