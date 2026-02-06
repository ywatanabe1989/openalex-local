#!/usr/bin/env python3
"""Add ref_count column to works table for fast citable items filtering.

This adds a pre-computed reference count column and index for efficient
JCR-style IF calculation (which requires filtering by >20 references).

Usage:
    python 07c_add_ref_count_column.py [--db-path PATH]
"""

import argparse
import logging
import sqlite3
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "openalex.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def add_ref_count_column(db_path: Path, batch_size: int = 100000) -> None:
    """Add ref_count column to works table."""
    logger.info(f"Adding ref_count column to: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-2000000")

    # Check if column already exists
    cursor = conn.execute("PRAGMA table_info(works)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'ref_count' in columns:
        logger.info("ref_count column already exists")
    else:
        logger.info("Adding ref_count column...")
        conn.execute("ALTER TABLE works ADD COLUMN ref_count INTEGER DEFAULT 0")
        conn.commit()
        logger.info("Column added")

    # Check if we need to populate
    cursor = conn.execute("SELECT COUNT(*) FROM works WHERE ref_count IS NULL OR ref_count = 0")
    unpopulated = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM works WHERE referenced_works_json IS NOT NULL")
    total_with_refs = cursor.fetchone()[0]

    logger.info(f"Works with refs: {total_with_refs:,}")
    logger.info(f"Needs population: {unpopulated:,}")

    if unpopulated == 0:
        logger.info("All ref_count values already populated")
    else:
        logger.info("Populating ref_count values...")
        start_time = time.time()

        # Update in batches using rowid
        cursor = conn.execute("SELECT MAX(rowid) FROM works")
        max_rowid = cursor.fetchone()[0] or 0

        processed = 0
        current_rowid = 0

        while current_rowid < max_rowid:
            batch_end = min(current_rowid + batch_size, max_rowid)

            conn.execute("""
                UPDATE works
                SET ref_count = json_array_length(referenced_works_json)
                WHERE rowid > ? AND rowid <= ?
                AND referenced_works_json IS NOT NULL
            """, (current_rowid, batch_end))

            processed += batch_size
            current_rowid = batch_end

            if processed % 500000 == 0:
                conn.commit()
                elapsed = time.time() - start_time
                rate = processed / elapsed
                eta = (max_rowid - current_rowid) / rate / 60
                pct = 100 * current_rowid / max_rowid
                logger.info(f"Progress: {current_rowid:,}/{max_rowid:,} ({pct:.1f}%) | Rate: {rate:.0f}/s | ETA: {eta:.1f}m")

        conn.commit()
        elapsed = time.time() - start_time
        logger.info(f"Population completed in {elapsed/60:.1f} minutes")

    # Create index
    logger.info("Creating index on ref_count...")
    cursor = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name='idx_works_ref_count'"
    )
    if cursor.fetchone():
        logger.info("Index idx_works_ref_count already exists")
    else:
        start_time = time.time()
        conn.execute("CREATE INDEX idx_works_ref_count ON works(ref_count)")
        conn.commit()
        elapsed = time.time() - start_time
        logger.info(f"Index created in {elapsed/60:.1f} minutes")

    # Create composite index for IF calculation: (issn, year, ref_count)
    logger.info("Creating composite index for IF calculation...")
    cursor = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name='idx_works_issn_year_refcount'"
    )
    if cursor.fetchone():
        logger.info("Index idx_works_issn_year_refcount already exists")
    else:
        start_time = time.time()
        conn.execute("CREATE INDEX idx_works_issn_year_refcount ON works(issn, year, ref_count)")
        conn.commit()
        elapsed = time.time() - start_time
        logger.info(f"Composite index created in {elapsed/60:.1f} minutes")

    # Analyze
    logger.info("Running ANALYZE...")
    conn.execute("ANALYZE works")
    conn.commit()

    # Stats
    cursor = conn.execute("SELECT COUNT(*) FROM works WHERE ref_count > 20")
    citable = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM works")
    total = cursor.fetchone()[0]

    logger.info("=" * 60)
    logger.info("COMPLETED")
    logger.info(f"Total works: {total:,}")
    logger.info(f"Citable items (>20 refs): {citable:,} ({100*citable/total:.1f}%)")
    logger.info("=" * 60)

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Add ref_count column for fast IF calculation"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100000,
        help="Batch size for updates (default: 100000)",
    )

    args = parser.parse_args()

    if not args.db_path.exists():
        logger.error(f"Database not found: {args.db_path}")
        sys.exit(1)

    add_ref_count_column(args.db_path, args.batch_size)


if __name__ == "__main__":
    main()
