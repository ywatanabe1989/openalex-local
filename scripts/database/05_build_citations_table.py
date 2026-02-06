#!/usr/bin/env python3
# Timestamp: 2026-02-03
"""Build citations table from OpenAlex works for impact factor calculation.

This script extracts citation relationships from the referenced_works_json field
in the works table and builds an indexed citations table for fast IF calculation.

Usage:
    python 05_build_citations_table.py [--db-path PATH] [--batch-size N]

Example:
    python scripts/database/05_build_citations_table.py
    python scripts/database/05_build_citations_table.py --batch-size 50000
"""

import argparse
import json
import logging
import sqlite3
import sys
import time
from pathlib import Path
from typing import List, Tuple, Optional

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


# Schema definition for citations
CITATIONS_SCHEMA_SQL = """
-- Citations table: tracks which works cite which other works
-- Used for accurate impact factor calculation
CREATE TABLE IF NOT EXISTS citations (
    citing_id TEXT NOT NULL,      -- OpenAlex ID of citing work (e.g., W1234567890)
    cited_id TEXT NOT NULL,       -- OpenAlex ID of cited work
    citing_year INTEGER NOT NULL  -- Year when the citation occurred
);

-- Progress tracking for citations build
CREATE TABLE IF NOT EXISTS _citations_build_progress (
    last_rowid INTEGER PRIMARY KEY,
    records_processed INTEGER,
    citations_inserted INTEGER,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Indexes created after data insertion for better performance
CITATIONS_INDEXES_SQL = """
-- Index for finding all citations TO a work in a specific year (for IF calculation)
CREATE INDEX IF NOT EXISTS idx_citations_cited_year ON citations(cited_id, citing_year);

-- Index for finding all citations FROM a work
CREATE INDEX IF NOT EXISTS idx_citations_citing ON citations(citing_id);

-- Index for year-based queries
CREATE INDEX IF NOT EXISTS idx_citations_year ON citations(citing_year);
"""


def get_last_progress(conn: sqlite3.Connection) -> Tuple[int, int, int]:
    """Get last progress checkpoint."""
    try:
        cursor = conn.execute(
            "SELECT last_rowid, records_processed, citations_inserted FROM _citations_build_progress ORDER BY last_rowid DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            return row[0], row[1], row[2]
    except sqlite3.OperationalError:
        pass
    return 0, 0, 0


def save_progress(conn: sqlite3.Connection, last_rowid: int, records: int, citations: int) -> None:
    """Save progress checkpoint."""
    conn.execute(
        "INSERT OR REPLACE INTO _citations_build_progress (last_rowid, records_processed, citations_inserted) VALUES (?, ?, ?)",
        (last_rowid, records, citations),
    )
    conn.commit()


def build_citations_table(
    db_path: Path,
    batch_size: int = 10000,
    commit_interval: int = 100000,
    rebuild: bool = False,
) -> None:
    """Build citations table from works' referenced_works_json field."""
    logger.info(f"Building citations table in: {db_path}")
    logger.info(f"Batch size: {batch_size}, Commit interval: {commit_interval}")

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-2000000")  # 2GB cache
    conn.execute("PRAGMA temp_store=MEMORY")

    # Drop existing tables if rebuild
    if rebuild:
        logger.info("Rebuilding: dropping existing citations table...")
        conn.execute("DROP TABLE IF EXISTS citations")
        conn.execute("DROP TABLE IF EXISTS _citations_build_progress")
        conn.commit()

    # Create schema (without indexes - add after data insertion)
    conn.executescript(CITATIONS_SCHEMA_SQL)
    conn.commit()

    # Get progress
    last_rowid, total_records, total_citations = get_last_progress(conn)

    if last_rowid > 0:
        logger.info(f"Resuming from rowid {last_rowid:,} ({total_records:,} records, {total_citations:,} citations)")

    # Get total works count
    cursor = conn.execute("SELECT MAX(rowid) FROM works")
    max_rowid = cursor.fetchone()[0] or 0
    logger.info(f"Total works to process: {max_rowid:,}")

    remaining = max_rowid - last_rowid
    logger.info(f"Remaining: {remaining:,}")

    if remaining <= 0:
        logger.info("All works already processed!")
        # Create indexes if not exist
        logger.info("Ensuring indexes exist...")
        conn.executescript(CITATIONS_INDEXES_SQL)
        conn.commit()
        conn.close()
        return

    # Process works in batches
    start_time = time.time()
    batch_citations = []
    records_in_batch = 0

    current_rowid = last_rowid

    while current_rowid < max_rowid:
        batch_start = current_rowid
        batch_end = min(current_rowid + batch_size, max_rowid)

        # Fetch batch of works
        cursor = conn.execute(
            """
            SELECT rowid, openalex_id, year, referenced_works_json
            FROM works
            WHERE rowid > ? AND rowid <= ?
            AND referenced_works_json IS NOT NULL
            AND referenced_works_json != '[]'
            """,
            (batch_start, batch_end),
        )

        for row in cursor:
            rowid, citing_id, citing_year, refs_json = row
            current_rowid = rowid
            total_records += 1
            records_in_batch += 1

            if not citing_year or not refs_json:
                continue

            try:
                referenced_works = json.loads(refs_json)
                for cited_id in referenced_works:
                    if cited_id:  # Skip empty strings
                        batch_citations.append((citing_id, cited_id, citing_year))
                        total_citations += 1
            except (json.JSONDecodeError, TypeError):
                continue

        # Update current_rowid to batch_end even if no works with refs in this batch
        current_rowid = batch_end

        # Insert citations when batch is large enough
        if len(batch_citations) >= commit_interval:
            conn.executemany(
                "INSERT INTO citations (citing_id, cited_id, citing_year) VALUES (?, ?, ?)",
                batch_citations,
            )
            conn.commit()
            save_progress(conn, current_rowid, total_records, total_citations)

            elapsed = time.time() - start_time
            rate = total_records / elapsed if elapsed > 0 else 0
            pct = 100 * current_rowid / max_rowid
            eta_sec = (max_rowid - current_rowid) / rate if rate > 0 else 0
            eta_hr = eta_sec / 3600

            logger.info(
                f"Progress: {current_rowid:,}/{max_rowid:,} ({pct:.1f}%) | "
                f"Records: {total_records:,} | Citations: {total_citations:,} | "
                f"Rate: {rate:.0f}/s | ETA: {eta_hr:.1f}h"
            )
            batch_citations = []
            records_in_batch = 0

    # Insert remaining citations
    if batch_citations:
        conn.executemany(
            "INSERT INTO citations (citing_id, cited_id, citing_year) VALUES (?, ?, ?)",
            batch_citations,
        )
        conn.commit()
        save_progress(conn, current_rowid, total_records, total_citations)

    elapsed = time.time() - start_time

    logger.info("=" * 60)
    logger.info("Data insertion completed!")
    logger.info(f"Total records processed: {total_records:,}")
    logger.info(f"Total citations inserted: {total_citations:,}")
    logger.info(f"Time: {elapsed / 3600:.1f} hours")

    # Create indexes
    logger.info("Creating indexes (this may take a while)...")
    index_start = time.time()
    conn.executescript(CITATIONS_INDEXES_SQL)
    conn.commit()
    index_elapsed = time.time() - index_start
    logger.info(f"Indexes created in {index_elapsed / 60:.1f} minutes")

    # Update metadata
    conn.execute(
        "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
        ("citations_build_completed", time.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.execute(
        "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
        ("total_citations", str(total_citations)),
    )
    conn.commit()

    # Analyze for query optimization
    logger.info("Running ANALYZE...")
    conn.execute("ANALYZE citations")
    conn.commit()

    conn.close()

    total_elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info("Citations table build completed!")
    logger.info(f"Total time: {total_elapsed / 3600:.1f} hours")


def main():
    parser = argparse.ArgumentParser(
        description="Build citations table from OpenAlex works"
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
        default=10000,
        help="Batch size for reading works (default: 10000)",
    )
    parser.add_argument(
        "--commit-interval",
        type=int,
        default=100000,
        help="Commit after this many citations (default: 100000)",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Drop and rebuild citations table from scratch",
    )

    args = parser.parse_args()

    if not args.db_path.exists():
        logger.error(f"Database not found: {args.db_path}")
        sys.exit(1)

    build_citations_table(
        db_path=args.db_path,
        batch_size=args.batch_size,
        commit_interval=args.commit_interval,
        rebuild=args.rebuild,
    )


if __name__ == "__main__":
    main()
