#!/usr/bin/env python3
# Timestamp: 2026-01-29
"""Build FTS5 full-text search index for OpenAlex database.

This script creates an FTS5 virtual table for fast full-text search
across titles and abstracts.

Usage:
    python 03_build_fts_index.py [--db-path PATH] [--batch-size N]

Example:
    python scripts/database/03_build_fts_index.py
    python scripts/database/03_build_fts_index.py --batch-size 100000

Note:
    Run this AFTER 02_build_database.py has completed.
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


# FTS5 schema
FTS_SCHEMA_SQL = """
-- Drop existing FTS table if rebuilding
DROP TABLE IF EXISTS works_fts;

-- Create FTS5 virtual table for full-text search
-- Using external content table to avoid data duplication
CREATE VIRTUAL TABLE works_fts USING fts5(
    openalex_id,
    title,
    abstract,
    content='works',
    content_rowid='id',
    tokenize='porter unicode61'
);

-- Create triggers to keep FTS in sync with works table
DROP TRIGGER IF EXISTS works_ai;
DROP TRIGGER IF EXISTS works_ad;
DROP TRIGGER IF EXISTS works_au;

CREATE TRIGGER works_ai AFTER INSERT ON works BEGIN
    INSERT INTO works_fts(rowid, openalex_id, title, abstract)
    VALUES (new.id, new.openalex_id, new.title, new.abstract);
END;

CREATE TRIGGER works_ad AFTER DELETE ON works BEGIN
    INSERT INTO works_fts(works_fts, rowid, openalex_id, title, abstract)
    VALUES ('delete', old.id, old.openalex_id, old.title, old.abstract);
END;

CREATE TRIGGER works_au AFTER UPDATE ON works BEGIN
    INSERT INTO works_fts(works_fts, rowid, openalex_id, title, abstract)
    VALUES ('delete', old.id, old.openalex_id, old.title, old.abstract);
    INSERT INTO works_fts(rowid, openalex_id, title, abstract)
    VALUES (new.id, new.openalex_id, new.title, new.abstract);
END;
"""


def get_total_works(conn: sqlite3.Connection) -> int:
    """Get total number of works in database."""
    cursor = conn.execute("SELECT COUNT(*) FROM works")
    return cursor.fetchone()[0]


def get_fts_count(conn: sqlite3.Connection) -> int:
    """Get count of records in FTS index."""
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM works_fts")
        return cursor.fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def build_fts_index(
    db_path: Path,
    batch_size: int = 50000,
    rebuild: bool = False,
) -> None:
    """Build FTS5 full-text search index."""
    logger.info(f"Building FTS index for: {db_path}")

    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        logger.error("Run 02_build_database.py first!")
        sys.exit(1)

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-2000000")  # 2GB cache
    conn.execute("PRAGMA temp_store=MEMORY")

    total_works = get_total_works(conn)
    logger.info(f"Total works in database: {total_works:,}")

    if total_works == 0:
        logger.error("No works in database! Run 02_build_database.py first.")
        conn.close()
        sys.exit(1)

    # Check if FTS already exists and is complete
    fts_count = get_fts_count(conn)
    if fts_count > 0 and not rebuild:
        logger.info(f"FTS index already contains {fts_count:,} records")
        if fts_count >= total_works * 0.99:  # Allow 1% tolerance
            logger.info("FTS index appears complete. Use --rebuild to force rebuild.")
            conn.close()
            return
        else:
            logger.info("FTS index incomplete. Rebuilding...")
            rebuild = True

    # Create FTS schema (drops existing if rebuilding)
    logger.info("Creating FTS5 virtual table...")
    conn.executescript(FTS_SCHEMA_SQL)
    conn.commit()

    # Populate FTS index in batches
    logger.info(f"Populating FTS index (batch size: {batch_size:,})...")
    start_time = time.time()

    # Use INSERT ... SELECT for bulk population
    logger.info("Inserting records into FTS index...")

    # For very large datasets, do it in batches to show progress
    offset = 0
    total_inserted = 0

    while True:
        batch_start = time.time()

        # Insert batch
        cursor = conn.execute(
            """
            INSERT INTO works_fts(rowid, openalex_id, title, abstract)
            SELECT id, openalex_id, title, abstract
            FROM works
            WHERE id > ?
            ORDER BY id
            LIMIT ?
            """,
            (offset, batch_size),
        )
        conn.commit()

        rows_inserted = cursor.rowcount
        if rows_inserted == 0:
            break

        total_inserted += rows_inserted
        offset += batch_size

        # Get actual max ID processed
        cursor = conn.execute(
            "SELECT MAX(id) FROM works WHERE id <= ?", (offset,)
        )
        result = cursor.fetchone()
        if result and result[0]:
            offset = result[0]

        batch_elapsed = time.time() - batch_start
        elapsed = time.time() - start_time
        rate = total_inserted / elapsed if elapsed > 0 else 0
        progress = (total_inserted / total_works) * 100

        logger.info(
            f"  Progress: {total_inserted:,}/{total_works:,} ({progress:.1f}%) | "
            f"Rate: {rate:.0f}/s | "
            f"Batch: {batch_elapsed:.1f}s"
        )

    # Final stats
    elapsed = time.time() - start_time
    final_count = get_fts_count(conn)

    logger.info("=" * 60)
    logger.info("FTS index build completed!")
    logger.info(f"Total indexed: {final_count:,}")
    logger.info(f"Total time: {elapsed / 60:.1f} minutes")
    logger.info(f"Average rate: {final_count / elapsed:.0f} records/s")

    # Update metadata
    conn.execute(
        "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
        ("fts_build_completed", time.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.execute(
        "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
        ("fts_total_indexed", str(final_count)),
    )
    conn.commit()

    # Optimize FTS index
    logger.info("Optimizing FTS index...")
    conn.execute("INSERT INTO works_fts(works_fts) VALUES('optimize')")
    conn.commit()

    conn.close()
    logger.info(f"Database size: {db_path.stat().st_size / (1024**3):.2f} GB")
    logger.info("FTS index ready for use!")


def verify_fts(db_path: Path) -> None:
    """Verify FTS index with a test search."""
    logger.info("Verifying FTS index...")

    conn = sqlite3.connect(db_path)

    # Test search
    test_query = "machine learning"
    cursor = conn.execute(
        """
        SELECT COUNT(*) FROM works_fts WHERE works_fts MATCH ?
        """,
        (test_query,),
    )
    count = cursor.fetchone()[0]
    logger.info(f"Test search '{test_query}': {count:,} results")

    # Get sample result
    cursor = conn.execute(
        """
        SELECT w.openalex_id, w.title, w.year
        FROM works_fts f
        JOIN works w ON f.rowid = w.id
        WHERE works_fts MATCH ?
        LIMIT 3
        """,
        (test_query,),
    )
    results = cursor.fetchall()

    if results:
        logger.info("Sample results:")
        for openalex_id, title, year in results:
            title_short = title[:60] + "..." if title and len(title) > 60 else title
            logger.info(f"  [{year}] {openalex_id}: {title_short}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Build FTS5 full-text search index for OpenAlex database"
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
        default=50000,
        help="Batch size for FTS population (default: 50000)",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild even if FTS index exists",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing FTS index",
    )

    args = parser.parse_args()

    if args.verify_only:
        verify_fts(args.db_path)
    else:
        build_fts_index(
            db_path=args.db_path,
            batch_size=args.batch_size,
            rebuild=args.rebuild,
        )
        verify_fts(args.db_path)


if __name__ == "__main__":
    main()
