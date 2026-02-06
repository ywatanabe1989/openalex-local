#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-02-06 (ywatanabe)"
# File: /home/ywatanabe/proj/openalex-local/examples/01_quickstart.py

"""OpenAlex Local - Quickstart Demo.

Key features for AI research assistants:
1. ABSTRACTS - Full text for LLM context (~45-60% availability)
2. CONCEPTS/TOPICS - Built-in classification
3. AUTHOR IDs - Disambiguation
4. SPEED - 284M records in milliseconds, no rate limits

Usage:
    python examples/01_quickstart.py
"""

import time

import scitex as stx
from openalex_local import search, get, count, info


def section(title: str, logger) -> None:
    logger.info(f"\n{'─' * 70}")
    logger.info(f"  {title}")
    logger.info(f"{'─' * 70}\n")


@stx.session
def main(
    CONFIG=stx.session.INJECTED,
    logger=stx.session.INJECTED,
):
    """OpenAlex Local quickstart demo."""
    try:
        db = info()
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error("Make sure the database is accessible or relay server is running.")
        return 1

    logger.info("\n" + "=" * 70)
    logger.info("  OPENALEX LOCAL - 284M Scholarly Works for the LLM Era")
    logger.info("=" * 70)
    logger.info(f"\n  {db.get('work_count', db.get('works', 0)):,} works indexed\n")

    # =========================================================================
    # 1. ABSTRACTS - The key differentiator for LLMs
    # =========================================================================
    section("1. ABSTRACTS - Full Text for LLM Context", logger)

    logger.info("  OpenAlex has ~45-60% abstract availability - essential for LLMs.\n")

    results = search("hippocampal memory consolidation", limit=3)

    for work in results.works:
        logger.info(f"  {work.title[:65]}...")
        logger.info(f"     {work.source or 'N/A'} ({work.year})")
        if work.abstract:
            abstract_preview = work.abstract[:200].replace("\n", " ")
            logger.info(f"     Abstract: {abstract_preview}...")
        else:
            logger.info("     Abstract: [Not available]")
        logger.info("")

    logger.info("  -> LLMs can understand paper content, not just metadata!\n")

    # =========================================================================
    # 2. CONCEPTS & TOPICS - Built-in Classification
    # =========================================================================
    section("2. CONCEPTS & TOPICS - Built-in Classification", logger)

    logger.info("  OpenAlex classifies papers with concepts and topics.\n")

    work = get("W2741809807")
    if work:
        logger.info(f"  {work.title[:60]}...")
        logger.info("")
        if work.concepts:
            logger.info("  Concepts:")
            for c in work.concepts[:5]:
                score = c.get("score", 0)
                logger.info(f"     - {c.get('name', 'N/A')} (score: {score:.2f})")
        if work.topics:
            logger.info("\n  Topics:")
            for t in work.topics[:3]:
                subfield = t.get("subfield", "N/A")
                logger.info(f"     - {t.get('name', 'N/A')} ({subfield})")

    logger.info("\n  -> Filter papers by topic for focused research!\n")

    # =========================================================================
    # 3. SPEED - No Rate Limits
    # =========================================================================
    section("3. SPEED - 284M Records, No Rate Limits", logger)

    logger.info("  Process thousands of papers without API throttling.\n")

    queries = [
        "machine learning",
        "CRISPR cas9",
        "climate model",
        "neural network",
        "protein folding",
    ]

    total_time = 0
    total_matches = 0

    logger.info(f"  {'Query':<30} {'Matches':>12} {'Time':>10}")
    logger.info(f"  {'-' * 54}")

    for q in queries:
        start = time.perf_counter()
        n = count(q)
        elapsed = (time.perf_counter() - start) * 1000
        total_time += elapsed
        total_matches += n
        logger.info(f"  {q:<30} {n:>12,} {elapsed:>8.0f}ms")

    logger.info(f"  {'-' * 54}")
    logger.info(f"  {'TOTAL':<30} {total_matches:>12,} {total_time:>8.0f}ms")

    logger.info(f"\n  -> {total_matches:,} papers indexed in {total_time:.0f}ms!")
    logger.info("  -> Online API would need minutes + hit rate limits\n")

    # =========================================================================
    # Summary
    # =========================================================================
    logger.info("=" * 70)
    logger.info("  WHY OPENALEX LOCAL FOR LLM APPLICATIONS?")
    logger.info("=" * 70)
    logger.info("")
    logger.info("  ABSTRACTS      ~45-60% availability for semantic search")
    logger.info("  CONCEPTS       Built-in topic classification")
    logger.info("  AUTHORS        Disambiguated with institution links")
    logger.info("  SPEED          No rate limits, instant results")
    logger.info("  OPEN ACCESS    OA status and direct URLs")
    logger.info("")
    logger.info("  Perfect for: RAG systems, research assistants, paper")
    logger.info("  recommendation, literature review automation")
    logger.info("")

    return 0


if __name__ == "__main__":
    main()

# EOF
