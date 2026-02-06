#!/usr/bin/env python3
# Timestamp: 2026-02-04
"""Build indexes required for fast Impact Factor calculation.

This script creates the indexes needed for efficient IF calculation:
- Works table: issn, issn+year composite, source_id
- Citations table: verifies existing indexes

Run this AFTER 05_build_citations_table.py completes.

Usage:
    python 06_build_if_indexes.py [--db-path PATH]

Example:
    python scripts/database/06_build_if_indexes.py
"""

import argparse
import logging
import sqlite3
import sys
import time
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "openalex.db"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# Indexes for IF calculation
IF_INDEXES = [
    # Works table indexes
    {
        "name": "idx_works_issn",
        "table": "works",
        "sql": "CREATE INDEX IF NOT EXISTS idx_works_issn ON works(issn)",
        "purpose": "Fast ISSN lookup for journal identification",
    },
    {
        "name": "idx_works_issn_year",
        "table": "works",
        "sql": "CREATE INDEX IF NOT EXISTS idx_works_issn_year ON works(issn, year)",
        "purpose": "KEY: Find all works by journal in year range (IF denominator)",
    },
    {
        "name": "idx_works_source_id",
        "table": "works",
        "sql": "CREATE INDEX IF NOT EXISTS idx_works_source_id ON works(source_id)",
        "purpose": "Alternative journal lookup by OpenAlex source ID",
    },
    {
        "name": "idx_works_source_id_year",
        "table": "works",
        "sql": "CREATE INDEX IF NOT EXISTS idx_works_source_id_year ON works(source_id, year)",
        "purpose": "Find works by source_id + year (alternative to ISSN)",
    },
]

# Citation indexes (verify they exist)
CITATION_INDEXES = [
    {
        "name": "idx_citations_cited_year",
        "table": "citations",
        "sql": "CREATE INDEX IF NOT EXISTS idx_citations_cited_year ON citations(cited_id, citing_year)",
        "purpose": "KEY: Find citations TO a work IN a specific year (IF numerator)",
    },
    {
        "name": "idx_citations_citing",
        "table": "citations",
        "sql": "CREATE INDEX IF NOT EXISTS idx_citations_citing ON citations(citing_id)",
        "purpose": "Find all references FROM a work (forward citation graph)",
    },
    {
        "name": "idx_citations_year",
        "table": "citations",
        "sql": "CREATE INDEX IF NOT EXISTS idx_citations_year ON citations(citing_year)",
        "purpose": "Year-based aggregations and trends",
    },
]


def index_exists(conn: sqlite3.Connection, index_name: str) -> bool:
    """Check if an index exists."""
    cursor = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",
        (index_name,)
    )
    return cursor.fetchone() is not None


def create_index(conn: sqlite3.Connection, index_info: dict) -> float:
    """Create an index and return time taken in minutes."""
    name = index_info["name"]
    sql = index_info["sql"]
    purpose = index_info["purpose"]

    if index_exists(conn, name):
        logger.info(f"  ✓ {name} already exists")
        return 0.0

    logger.info(f"  Creating {name}...")
    logger.info(f"    Purpose: {purpose}")

    start = time.time()
    conn.execute(sql)
    conn.commit()
    elapsed = (time.time() - start) / 60

    logger.info(f"    Done in {elapsed:.1f} minutes")
    return elapsed


def build_if_indexes(db_path: Path) -> None:
    """Build all indexes needed for IF calculation."""
    logger.info(f"Building IF indexes in: {db_path}")

    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-2000000")  # 2GB cache

    total_time = 0.0

    # Check citations table exists
    cursor = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='citations'"
    )
    has_citations = cursor.fetchone() is not None

    if not has_citations:
        logger.warning("Citations table not found!")
        logger.warning("Run: python scripts/database/05_build_citations_table.py first")

    # Build works indexes
    logger.info("")
    logger.info("=" * 60)
    logger.info("WORKS TABLE INDEXES (for finding journal articles by ISSN/year)")
    logger.info("=" * 60)

    for idx in IF_INDEXES:
        total_time += create_index(conn, idx)

    # Build/verify citations indexes
    if has_citations:
        logger.info("")
        logger.info("=" * 60)
        logger.info("CITATIONS TABLE INDEXES (for counting citations by year)")
        logger.info("=" * 60)

        for idx in CITATION_INDEXES:
            total_time += create_index(conn, idx)

    # Run ANALYZE
    logger.info("")
    logger.info("Running ANALYZE for query optimization...")
    conn.execute("ANALYZE works")
    if has_citations:
        conn.execute("ANALYZE citations")
    conn.commit()

    # Update metadata
    conn.execute(
        "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
        ("if_indexes_completed", time.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()

    conn.close()

    logger.info("")
    logger.info("=" * 60)
    logger.info("IF INDEXES BUILD COMPLETE")
    logger.info(f"Total time: {total_time:.1f} minutes")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Impact Factor calculation is now available:")
    logger.info("  openalex-local search 'query' -if")


def main():
    parser = argparse.ArgumentParser(
        description="Build indexes for Impact Factor calculation"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to database (default: {DEFAULT_DB_PATH})",
    )

    args = parser.parse_args()
    build_if_indexes(args.db_path)


if __name__ == "__main__":
    main()
