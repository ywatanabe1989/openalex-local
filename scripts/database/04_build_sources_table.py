#!/usr/bin/env python3
# Timestamp: 2026-02-03
"""Build sources table from OpenAlex snapshot for journal metrics (impact factor, h-index, etc).

This script reads the sources entity from the OpenAlex snapshot and builds
a sources table with journal-level metrics including impact factor (2yr_mean_citedness),
h-index, citation counts, and other bibliometrics.

Usage:
    python 04_build_sources_table.py [--snapshot-dir PATH] [--db-path PATH]

Example:
    python scripts/database/04_build_sources_table.py
"""

import argparse
import gzip
import json
import logging
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SNAPSHOT_DIR = PROJECT_ROOT / "data" / "snapshot" / "sources"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "openalex.db"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# Schema definition for sources
SOURCES_SCHEMA_SQL = """
-- Sources table: journal/venue metadata with impact metrics
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    openalex_id TEXT UNIQUE NOT NULL,
    issn_l TEXT,
    issns TEXT,  -- JSON array of all ISSNs
    display_name TEXT,
    display_name_lower TEXT,  -- For case-insensitive search
    type TEXT,  -- journal, repository, conference, etc.
    host_organization TEXT,
    country_code TEXT,
    homepage_url TEXT,

    -- Bibliometrics
    works_count INTEGER DEFAULT 0,
    oa_works_count INTEGER DEFAULT 0,
    cited_by_count INTEGER DEFAULT 0,

    -- Impact metrics (from summary_stats)
    two_year_mean_citedness REAL,  -- Impact Factor equivalent
    h_index INTEGER,
    i10_index INTEGER,

    -- OA status
    is_oa INTEGER DEFAULT 0,
    is_in_doaj INTEGER DEFAULT 0,
    is_core INTEGER DEFAULT 0,

    -- Temporal info
    first_publication_year INTEGER,
    last_publication_year INTEGER,

    -- APC
    apc_usd INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ISSN lookup table for fast journal lookup by ISSN
CREATE TABLE IF NOT EXISTS issn_lookup (
    issn TEXT PRIMARY KEY,
    source_id INTEGER NOT NULL,
    FOREIGN KEY (source_id) REFERENCES sources(id)
);

-- Indices for common queries
CREATE INDEX IF NOT EXISTS idx_sources_issn_l ON sources(issn_l);
CREATE INDEX IF NOT EXISTS idx_sources_display_name_lower ON sources(display_name_lower);
CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(type);
CREATE INDEX IF NOT EXISTS idx_sources_two_year_mean_citedness ON sources(two_year_mean_citedness);
CREATE INDEX IF NOT EXISTS idx_sources_h_index ON sources(h_index);
CREATE INDEX IF NOT EXISTS idx_sources_cited_by_count ON sources(cited_by_count);
CREATE INDEX IF NOT EXISTS idx_sources_works_count ON sources(works_count);

-- Progress tracking for sources build
CREATE TABLE IF NOT EXISTS _sources_build_progress (
    file_path TEXT PRIMARY KEY,
    records_processed INTEGER,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def parse_source(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse OpenAlex source JSON into database record."""
    # Extract OpenAlex ID (remove URL prefix)
    openalex_id = data.get("id", "").replace("https://openalex.org/", "")

    # Extract ISSNs
    issns = data.get("issn") or []
    issn_l = data.get("issn_l")

    # Extract summary stats
    summary_stats = data.get("summary_stats") or {}

    # Display name
    display_name = data.get("display_name")

    return {
        "openalex_id": openalex_id,
        "issn_l": issn_l,
        "issns": json.dumps(issns) if issns else None,
        "display_name": display_name,
        "display_name_lower": display_name.lower() if display_name else None,
        "type": data.get("type"),
        "host_organization": data.get("host_organization_name"),
        "country_code": data.get("country_code"),
        "homepage_url": data.get("homepage_url"),

        # Bibliometrics
        "works_count": data.get("works_count", 0),
        "oa_works_count": data.get("oa_works_count", 0),
        "cited_by_count": data.get("cited_by_count", 0),

        # Impact metrics
        "two_year_mean_citedness": summary_stats.get("2yr_mean_citedness"),
        "h_index": summary_stats.get("h_index"),
        "i10_index": summary_stats.get("i10_index"),

        # OA status
        "is_oa": 1 if data.get("is_oa") else 0,
        "is_in_doaj": 1 if data.get("is_in_doaj") else 0,
        "is_core": 1 if data.get("is_core") else 0,

        # Temporal
        "first_publication_year": data.get("first_publication_year"),
        "last_publication_year": data.get("last_publication_year"),

        # APC
        "apc_usd": data.get("apc_usd"),
    }


def iter_jsonl_gz(file_path: Path) -> Generator[Dict[str, Any], None, None]:
    """Iterate over gzipped JSON Lines file."""
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error in {file_path}: {e}")
                    continue


def get_all_gz_files(snapshot_dir: Path) -> List[Path]:
    """Get all .gz files from snapshot directory, sorted by date (newest first for dedup)."""
    files = []
    for date_dir in sorted(snapshot_dir.iterdir(), reverse=True):  # Newest first
        if date_dir.is_dir() and date_dir.name.startswith("updated_date="):
            for gz_file in sorted(date_dir.glob("*.gz")):
                files.append(gz_file)
    return files


def get_processed_files(conn: sqlite3.Connection) -> set:
    """Get set of already processed file paths."""
    try:
        cursor = conn.execute("SELECT file_path FROM _sources_build_progress")
        return {row[0] for row in cursor.fetchall()}
    except sqlite3.OperationalError:
        return set()


def mark_file_processed(conn: sqlite3.Connection, file_path: str, records: int) -> None:
    """Mark a file as processed."""
    conn.execute(
        "INSERT OR REPLACE INTO _sources_build_progress (file_path, records_processed) VALUES (?, ?)",
        (file_path, records),
    )
    conn.commit()


def build_issn_lookup(conn: sqlite3.Connection) -> int:
    """Build ISSN lookup table from sources."""
    logger.info("Building ISSN lookup table...")

    # Clear existing lookup
    conn.execute("DELETE FROM issn_lookup")

    # Get all sources with ISSNs
    cursor = conn.execute("SELECT id, issn_l, issns FROM sources WHERE issns IS NOT NULL OR issn_l IS NOT NULL")

    lookup_count = 0
    for row in cursor:
        source_id = row[0]
        issn_l = row[1]
        issns_json = row[2]

        issns_to_add = set()

        # Add linking ISSN
        if issn_l:
            issns_to_add.add(issn_l)

        # Add all ISSNs from array
        if issns_json:
            try:
                issns = json.loads(issns_json)
                for issn in issns:
                    if issn:
                        issns_to_add.add(issn)
            except json.JSONDecodeError:
                pass

        # Insert into lookup table
        for issn in issns_to_add:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO issn_lookup (issn, source_id) VALUES (?, ?)",
                    (issn, source_id)
                )
                lookup_count += 1
            except sqlite3.IntegrityError:
                pass  # Duplicate ISSN, skip

    conn.commit()
    logger.info(f"ISSN lookup table built with {lookup_count} entries")
    return lookup_count


def build_sources_table(
    snapshot_dir: Path,
    db_path: Path,
    batch_size: int = 5000,
    rebuild: bool = False,
) -> None:
    """Build sources table from OpenAlex snapshot."""
    logger.info(f"Building sources table in: {db_path}")
    logger.info(f"Sources snapshot directory: {snapshot_dir}")

    if not snapshot_dir.exists():
        logger.error(f"Sources snapshot directory not found: {snapshot_dir}")
        logger.error("Run: python scripts/database/01_download_snapshot.py --entity sources")
        sys.exit(1)

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-500000")  # 500MB cache

    # Drop existing tables if rebuild
    if rebuild:
        logger.info("Rebuilding: dropping existing sources tables...")
        conn.execute("DROP TABLE IF EXISTS issn_lookup")
        conn.execute("DROP TABLE IF EXISTS sources")
        conn.execute("DROP TABLE IF EXISTS _sources_build_progress")
        conn.commit()

    # Create schema
    conn.executescript(SOURCES_SCHEMA_SQL)
    conn.commit()

    # Get files to process
    all_files = get_all_gz_files(snapshot_dir)
    processed_files = get_processed_files(conn)

    files_to_process = [f for f in all_files if str(f) not in processed_files]

    logger.info(f"Total source files: {len(all_files)}")
    logger.info(f"Already processed: {len(processed_files)}")
    logger.info(f"Files to process: {len(files_to_process)}")

    if not files_to_process:
        logger.info("All source files already processed!")
        # Still rebuild ISSN lookup in case it's needed
        build_issn_lookup(conn)
        conn.close()
        return

    # Process files
    total_records = 0
    total_inserted = 0
    start_time = time.time()

    # Prepare insert statement
    columns = [
        "openalex_id", "issn_l", "issns", "display_name", "display_name_lower",
        "type", "host_organization", "country_code", "homepage_url",
        "works_count", "oa_works_count", "cited_by_count",
        "two_year_mean_citedness", "h_index", "i10_index",
        "is_oa", "is_in_doaj", "is_core",
        "first_publication_year", "last_publication_year", "apc_usd"
    ]
    placeholders = ", ".join(["?" for _ in columns])
    column_names = ", ".join(columns)
    insert_sql = f"INSERT OR REPLACE INTO sources ({column_names}) VALUES ({placeholders})"

    for file_idx, gz_file in enumerate(files_to_process):
        file_start = time.time()
        batch = []
        file_records = 0

        logger.info(f"[{file_idx + 1}/{len(files_to_process)}] Processing: {gz_file}")

        for data in iter_jsonl_gz(gz_file):
            try:
                record = parse_source(data)
                batch.append(tuple(record[col] for col in columns))
                file_records += 1
                total_records += 1

                if len(batch) >= batch_size:
                    cursor = conn.executemany(insert_sql, batch)
                    total_inserted += cursor.rowcount
                    conn.commit()
                    batch = []

            except Exception as e:
                logger.warning(f"Error processing source record: {e}")
                continue

        # Insert remaining batch
        if batch:
            cursor = conn.executemany(insert_sql, batch)
            total_inserted += cursor.rowcount
            conn.commit()

        # Mark file as processed
        mark_file_processed(conn, str(gz_file), file_records)

        file_elapsed = time.time() - file_start
        logger.info(f"  Completed: {file_records:,} records in {file_elapsed:.1f}s")

    # Build ISSN lookup table
    build_issn_lookup(conn)

    # Final stats
    elapsed = time.time() - start_time

    # Count total sources
    cursor = conn.execute("SELECT COUNT(*) FROM sources")
    total_sources = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM issn_lookup")
    total_issns = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM sources WHERE two_year_mean_citedness IS NOT NULL")
    sources_with_if = cursor.fetchone()[0]

    logger.info("=" * 60)
    logger.info("Sources table build completed!")
    logger.info(f"Total sources: {total_sources:,}")
    logger.info(f"Sources with impact factor: {sources_with_if:,}")
    logger.info(f"Total ISSN lookups: {total_issns:,}")
    logger.info(f"Total time: {elapsed:.1f}s")

    # Update metadata
    conn.execute(
        "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
        ("sources_build_completed", time.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.execute(
        "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
        ("total_sources", str(total_sources)),
    )
    conn.commit()

    # Analyze for query optimization
    logger.info("Running ANALYZE for query optimization...")
    conn.execute("ANALYZE sources")
    conn.execute("ANALYZE issn_lookup")
    conn.commit()

    conn.close()
    logger.info("Sources table ready!")


def main():
    parser = argparse.ArgumentParser(
        description="Build sources table from OpenAlex snapshot"
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=DEFAULT_SNAPSHOT_DIR,
        help=f"Path to sources snapshot directory (default: {DEFAULT_SNAPSHOT_DIR})",
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
        default=5000,
        help="Batch size for database inserts (default: 5000)",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Drop and rebuild sources tables from scratch",
    )

    args = parser.parse_args()

    build_sources_table(
        snapshot_dir=args.snapshot_dir,
        db_path=args.db_path,
        batch_size=args.batch_size,
        rebuild=args.rebuild,
    )


if __name__ == "__main__":
    main()
