#!/usr/bin/env python3
"""
OpenAlex Local - Quickstart Demo

Key features for AI research assistants:
1. ABSTRACTS - Full text for LLM context (~45-60% availability)
2. CONCEPTS/TOPICS - Built-in classification
3. AUTHOR IDs - Disambiguation
4. SPEED - 284M records in milliseconds, no rate limits

Usage:
    python examples/01_quickstart.py
"""

import sys
import time
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openalex_local import search, get, count, info


def section(title: str) -> None:
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}\n")


def demo():
    try:
        db = info()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the database is accessible or relay server is running.")
        return

    print("\n" + "━" * 70)
    print("  📚 OPENALEX LOCAL - 284M Scholarly Works for the LLM Era")
    print("━" * 70)
    print(f"\n  📊 {db.get('work_count', db.get('works', 0)):,} works indexed\n")

    # =========================================================================
    # 1. ABSTRACTS - The key differentiator for LLMs
    # =========================================================================
    section("1️⃣  ABSTRACTS - Full Text for LLM Context")

    print("  OpenAlex has ~45-60% abstract availability - essential for LLMs.\n")

    results = search("hippocampal memory consolidation", limit=3)

    for work in results.works:
        print(f"  📄 {work.title[:65]}...")
        print(f"     {work.source or 'N/A'} ({work.year})")
        print()
        if work.abstract:
            abstract_preview = work.abstract[:200].replace("\n", " ")
            print(f"     📝 Abstract: {abstract_preview}...")
        else:
            print("     📝 Abstract: [Not available]")
        print()

    print("  → LLMs can understand paper content, not just metadata!\n")

    # =========================================================================
    # 2. CONCEPTS & TOPICS - Built-in Classification
    # =========================================================================
    section("2️⃣  CONCEPTS & TOPICS - Built-in Classification")

    print("  OpenAlex classifies papers with concepts and topics.\n")

    work = get("W2741809807")  # Example work
    if work:
        print(f"  📄 {work.title[:60]}...")
        print()
        if work.concepts:
            print("  Concepts:")
            for c in work.concepts[:5]:
                score = c.get("score", 0)
                print(f"     • {c.get('name', 'N/A')} (score: {score:.2f})")
        if work.topics:
            print("\n  Topics:")
            for t in work.topics[:3]:
                subfield = t.get("subfield", "N/A")
                print(f"     • {t.get('name', 'N/A')} ({subfield})")

    print("\n  → Filter papers by topic for focused research!\n")

    # =========================================================================
    # 3. SPEED - No Rate Limits
    # =========================================================================
    section("3️⃣  SPEED - 284M Records, No Rate Limits")

    print("  Process thousands of papers without API throttling.\n")

    queries = [
        "machine learning",
        "CRISPR cas9",
        "climate model",
        "neural network",
        "protein folding",
    ]

    total_time = 0
    total_matches = 0

    print(f"  {'Query':<30} {'Matches':>12} {'Time':>10}")
    print(f"  {'-' * 54}")

    for q in queries:
        start = time.perf_counter()
        n = count(q)
        elapsed = (time.perf_counter() - start) * 1000
        total_time += elapsed
        total_matches += n
        print(f"  {q:<30} {n:>12,} {elapsed:>8.0f}ms")

    print(f"  {'-' * 54}")
    print(f"  {'TOTAL':<30} {total_matches:>12,} {total_time:>8.0f}ms")

    print(f"\n  → {total_matches:,} papers indexed in {total_time:.0f}ms!")
    print("  → Online API would need minutes + hit rate limits\n")

    # =========================================================================
    # Summary
    # =========================================================================
    print("━" * 70)
    print("  🚀 WHY OPENALEX LOCAL FOR LLM APPLICATIONS?")
    print("━" * 70)
    print(
        """
  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                 │
  │  📝 ABSTRACTS      ~45-60% availability for semantic search    │
  │  🏷️ CONCEPTS       Built-in topic classification               │
  │  👤 AUTHORS        Disambiguated with institution links        │
  │  ⚡ SPEED          No rate limits, instant results             │
  │  🔓 OPEN ACCESS    OA status and direct URLs                   │
  │                                                                 │
  │  Perfect for: RAG systems, research assistants, paper          │
  │  recommendation, literature review automation                  │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘
"""
    )


if __name__ == "__main__":
    demo()
