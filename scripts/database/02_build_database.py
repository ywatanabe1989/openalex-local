#!/usr/bin/env python3
# Timestamp: 2026-01-29
"""Build SQLite database from OpenAlex snapshot.

This script reads gzipped JSON Lines files from the OpenAlex snapshot
and builds a SQLite database with works data.

Usage:
    python 02_build_database.py [--snapshot-dir PATH] [--db-path PATH] [--batch-size N]

Example:
    python scripts/database/02_build_database.py
    python scripts/database/02_build_database.py --batch-size 50000
"""

import argparse
import gzip
import json
import logging
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Tuple

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SNAPSHOT_DIR = PROJECT_ROOT / "data" / "snapshot" / "works"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "openalex.db"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# Schema definition
SCHEMA_SQL = """
-- Works table: core metadata for each scholarly work
CREATE TABLE IF NOT EXISTS works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    openalex_id TEXT UNIQUE NOT NULL,
    doi TEXT,
    title TEXT,
    abstract TEXT,
    year INTEGER,
    publication_date TEXT,
    type TEXT,
    language TEXT,
    source TEXT,
    source_id TEXT,
    issn TEXT,
    volume TEXT,
    issue TEXT,
    first_page TEXT,
    last_page TEXT,
    publisher TEXT,
    cited_by_count INTEGER DEFAULT 0,
    is_oa INTEGER DEFAULT 0,
    oa_status TEXT,
    oa_url TEXT,
    authors_json TEXT,
    concepts_json TEXT,
    topics_json TEXT,
    referenced_works_json TEXT,
    raw_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices for common queries
CREATE INDEX IF NOT EXISTS idx_works_doi ON works(doi);
CREATE INDEX IF NOT EXISTS idx_works_year ON works(year);
CREATE INDEX IF NOT EXISTS idx_works_source ON works(source);
CREATE INDEX IF NOT EXISTS idx_works_type ON works(type);
CREATE INDEX IF NOT EXISTS idx_works_language ON works(language);
CREATE INDEX IF NOT EXISTS idx_works_cited_by_count ON works(cited_by_count);
CREATE INDEX IF NOT EXISTS idx_works_is_oa ON works(is_oa);

-- Progress tracking table
CREATE TABLE IF NOT EXISTS _build_progress (
    file_path TEXT PRIMARY KEY,
    records_processed INTEGER,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metadata table
CREATE TABLE IF NOT EXISTS _metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
    """Reconstruct abstract from OpenAlex inverted index format."""
    if not inverted_index:
        return None
    try:
        words = sorted(
            [(pos, word) for word, positions in inverted_index.items() for pos in positions]
        )
        return " ".join(word for _, word in words)
    except Exception:
        return None


def extract_authors(authorships: List[Dict]) -> List[str]:
    """Extract author names from authorships list."""
    authors = []
    for authorship in authorships or []:
        author = authorship.get("author", {})
        name = author.get("display_name")
        if name:
            authors.append(name)
    return authors


def extract_concepts(concepts: List[Dict], limit: int = 5) -> List[Dict[str, Any]]:
    """Extract top concepts with name and score."""
    return [
        {"name": c.get("display_name"), "score": c.get("score")}
        for c in (concepts or [])[:limit]
    ]


def extract_topics(topics: List[Dict], limit: int = 3) -> List[Dict[str, Any]]:
    """Extract top topics with name and subfield."""
    return [
        {
            "name": t.get("display_name"),
            "subfield": t.get("subfield", {}).get("display_name") if t.get("subfield") else None,
            "field": t.get("field", {}).get("display_name") if t.get("field") else None,
        }
        for t in (topics or [])[:limit]
    ]


def parse_work(data: Dict[str, Any], store_raw: bool = False) -> Dict[str, Any]:
    """Parse OpenAlex work JSON into database record."""
    # Extract OpenAlex ID (remove URL prefix)
    openalex_id = data.get("id", "").replace("https://openalex.org/", "")

    # Extract DOI (remove URL prefix)
    doi = data.get("doi", "").replace("https://doi.org/", "") if data.get("doi") else None

    # Extract source info
    primary_location = data.get("primary_location") or {}
    source_info = primary_location.get("source") or {}
    source = source_info.get("display_name")
    source_id = (source_info.get("id") or "").replace("https://openalex.org/", "") if source_info.get("id") else None
    issns = source_info.get("issn") or []
    issn = issns[0] if issns else None
    publisher = source_info.get("host_organization_name")

    # Extract biblio info
    biblio = data.get("biblio") or {}

    # Extract OA info
    oa_info = data.get("open_access") or {}

    # Extract and serialize complex fields
    authors = extract_authors(data.get("authorships", []))
    concepts = extract_concepts(data.get("concepts", []))
    topics = extract_topics(data.get("topics", []))
    referenced_works = [
        r.replace("https://openalex.org/", "") for r in (data.get("referenced_works") or [])
    ]

    return {
        "openalex_id": openalex_id,
        "doi": doi,
        "title": data.get("title") or data.get("display_name"),
        "abstract": reconstruct_abstract(data.get("abstract_inverted_index")),
        "year": data.get("publication_year"),
        "publication_date": data.get("publication_date"),
        "type": data.get("type"),
        "language": data.get("language"),
        "source": source,
        "source_id": source_id,
        "issn": issn,
        "volume": biblio.get("volume"),
        "issue": biblio.get("issue"),
        "first_page": biblio.get("first_page"),
        "last_page": biblio.get("last_page"),
        "publisher": publisher,
        "cited_by_count": data.get("cited_by_count", 0),
        "is_oa": 1 if oa_info.get("is_oa") else 0,
        "oa_status": oa_info.get("oa_status"),
        "oa_url": oa_info.get("oa_url"),
        "authors_json": json.dumps(authors) if authors else None,
        "concepts_json": json.dumps(concepts) if concepts else None,
        "topics_json": json.dumps(topics) if topics else None,
        "referenced_works_json": json.dumps(referenced_works) if referenced_works else None,
        "raw_json": json.dumps(data) if store_raw else None,
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
    """Get all .gz files from snapshot directory, sorted."""
    files = []
    for date_dir in sorted(snapshot_dir.iterdir()):
        if date_dir.is_dir() and date_dir.name.startswith("updated_date="):
            for gz_file in sorted(date_dir.glob("*.gz")):
                files.append(gz_file)
    return files


def get_processed_files(conn: sqlite3.Connection) -> set:
    """Get set of already processed file paths."""
    cursor = conn.execute("SELECT file_path FROM _build_progress")
    return {row[0] for row in cursor.fetchall()}


def mark_file_processed(conn: sqlite3.Connection, file_path: str, records: int) -> None:
    """Mark a file as processed."""
    conn.execute(
        "INSERT OR REPLACE INTO _build_progress (file_path, records_processed) VALUES (?, ?)",
        (file_path, records),
    )
    conn.commit()


def insert_batch(conn: sqlite3.Connection, records: List[Dict[str, Any]]) -> int:
    """Insert a batch of records into the database."""
    if not records:
        return 0

    columns = list(records[0].keys())
    placeholders = ", ".join(["?" for _ in columns])
    column_names = ", ".join(columns)

    sql = f"INSERT OR IGNORE INTO works ({column_names}) VALUES ({placeholders})"

    values = [tuple(r[col] for col in columns) for r in records]

    cursor = conn.executemany(sql, values)
    conn.commit()
    return cursor.rowcount


def build_database(
    snapshot_dir: Path,
    db_path: Path,
    batch_size: int = 10000,
    store_raw: bool = False,
) -> None:
    """Build SQLite database from OpenAlex snapshot."""
    logger.info(f"Building database: {db_path}")
    logger.info(f"Snapshot directory: {snapshot_dir}")
    logger.info(f"Batch size: {batch_size}")

    # Ensure output directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-2000000")  # 2GB cache
    conn.execute("PRAGMA temp_store=MEMORY")

    # Create schema
    conn.executescript(SCHEMA_SQL)
    conn.commit()

    # Get files to process
    all_files = get_all_gz_files(snapshot_dir)
    processed_files = get_processed_files(conn)

    files_to_process = [f for f in all_files if str(f) not in processed_files]

    logger.info(f"Total files: {len(all_files)}")
    logger.info(f"Already processed: {len(processed_files)}")
    logger.info(f"Files to process: {len(files_to_process)}")

    if not files_to_process:
        logger.info("All files already processed!")
        conn.close()
        return

    # Process files
    total_records = 0
    start_time = time.time()

    for file_idx, gz_file in enumerate(files_to_process):
        file_start = time.time()
        batch = []
        file_records = 0

        logger.info(f"[{file_idx + 1}/{len(files_to_process)}] Processing: {gz_file.name}")

        for data in iter_jsonl_gz(gz_file):
            try:
                record = parse_work(data, store_raw=store_raw)
                batch.append(record)
                file_records += 1

                if len(batch) >= batch_size:
                    inserted = insert_batch(conn, batch)
                    total_records += inserted
                    batch = []

                    # Progress update
                    if file_records % 100000 == 0:
                        elapsed = time.time() - start_time
                        rate = total_records / elapsed if elapsed > 0 else 0
                        logger.info(
                            f"  Progress: {file_records:,} records | "
                            f"Total: {total_records:,} | "
                            f"Rate: {rate:.0f}/s"
                        )

            except Exception as e:
                logger.warning(f"Error processing record: {e}")
                continue

        # Insert remaining batch
        if batch:
            inserted = insert_batch(conn, batch)
            total_records += inserted

        # Mark file as processed
        mark_file_processed(conn, str(gz_file), file_records)

        file_elapsed = time.time() - file_start
        logger.info(
            f"  Completed: {file_records:,} records in {file_elapsed:.1f}s "
            f"({file_records / file_elapsed:.0f}/s)"
        )

    # Final stats
    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"Build completed!")
    logger.info(f"Total records: {total_records:,}")
    logger.info(f"Total time: {elapsed / 3600:.1f} hours")
    logger.info(f"Average rate: {total_records / elapsed:.0f} records/s")

    # Update metadata
    conn.execute(
        "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
        ("build_completed", time.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.execute(
        "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
        ("total_works", str(total_records)),
    )
    conn.commit()

    # Analyze for query optimization
    logger.info("Running ANALYZE for query optimization...")
    conn.execute("ANALYZE")
    conn.commit()

    conn.close()
    logger.info(f"Database saved: {db_path}")
    logger.info(f"Database size: {db_path.stat().st_size / (1024**3):.2f} GB")


def main():
    parser = argparse.ArgumentParser(
        description="Build SQLite database from OpenAlex snapshot"
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=DEFAULT_SNAPSHOT_DIR,
        help=f"Path to snapshot works directory (default: {DEFAULT_SNAPSHOT_DIR})",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to output database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10000,
        help="Batch size for database inserts (default: 10000)",
    )
    parser.add_argument(
        "--store-raw",
        action="store_true",
        help="Store raw JSON in database (increases size significantly)",
    )

    args = parser.parse_args()

    if not args.snapshot_dir.exists():
        logger.error(f"Snapshot directory not found: {args.snapshot_dir}")
        sys.exit(1)

    build_database(
        snapshot_dir=args.snapshot_dir,
        db_path=args.db_path,
        batch_size=args.batch_size,
        store_raw=args.store_raw,
    )


if __name__ == "__main__":
    main()
