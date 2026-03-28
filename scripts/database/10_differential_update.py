#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Differential update for OpenAlex database.

Downloads only snapshot directories newer than the last sync date,
then merges new/updated records into the existing database.

Usage:
    python 10_differential_update.py [--db-path PATH] [--snapshot-dir PATH]
    python 10_differential_update.py --since 2026-03-01
    python 10_differential_update.py --dry-run

Steps:
    1. Read last sync date from _metadata table
    2. List S3 directories with updated_date > last sync
    3. Download only those directories (aws s3 sync with --include filter)
    4. Parse and upsert records (INSERT OR REPLACE)
    5. Update last_sync_date in _metadata
"""

import argparse
import gzip
import json
import logging
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# Reuse parse_work from build script
sys.path.insert(0, str(Path(__file__).parent))
from _build_helpers import parse_work  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SNAPSHOT_DIR = PROJECT_ROOT / "data" / "snapshot" / "works"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "openalex.db"
OPENALEX_S3_BASE = "s3://openalex/data/works/"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def get_last_sync_date(conn: sqlite3.Connection) -> Optional[str]:
    """Get last sync date from metadata."""
    try:
        cursor = conn.execute(
            "SELECT value FROM _metadata WHERE key = 'last_sync_date'"
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        return None


def set_last_sync_date(conn: sqlite3.Connection, date_str: str) -> None:
    """Set last sync date in metadata."""
    conn.execute(
        "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
        ("last_sync_date", date_str),
    )
    conn.commit()


def list_s3_updated_dates(since: Optional[str] = None) -> List[str]:
    """List updated_date directories from S3.

    Parameters
    ----------
    since : str, optional
        Only return dates after this (YYYY-MM-DD format).

    Returns
    -------
    list[str]
        Sorted list of date strings (YYYY-MM-DD).
    """
    logger.info("Listing S3 directories...")
    cmd = [
        "aws", "s3", "ls", OPENALEX_S3_BASE,
        "--no-sign-request",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to list S3: {e}")
        return []

    dates = []
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if "updated_date=" in line:
            # Format: "PRE updated_date=2026-03-15/"
            part = line.split("updated_date=")[-1].rstrip("/")
            if part:
                dates.append(part)

    dates.sort()

    if since:
        dates = [d for d in dates if d > since]

    logger.info(f"Found {len(dates)} directories" + (f" since {since}" if since else ""))
    return dates


def download_date_directories(
    dates: List[str],
    snapshot_dir: Path,
) -> List[Path]:
    """Download specific updated_date directories from S3.

    Returns list of downloaded directory paths.
    """
    downloaded = []
    for i, date in enumerate(dates):
        s3_path = f"{OPENALEX_S3_BASE}updated_date={date}/"
        local_path = snapshot_dir / f"updated_date={date}"
        local_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"[{i+1}/{len(dates)}] Downloading updated_date={date}...")

        cmd = [
            "aws", "s3", "sync",
            s3_path, str(local_path),
            "--no-sign-request",
        ]
        try:
            subprocess.run(cmd, check=True)
            downloaded.append(local_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to download {date}: {e}")

    return downloaded


def upsert_batch(conn: sqlite3.Connection, records: list) -> int:
    """Upsert a batch of records (INSERT OR REPLACE)."""
    if not records:
        return 0

    columns = list(records[0].keys())
    placeholders = ", ".join(["?" for _ in columns])
    column_names = ", ".join(columns)

    sql = f"INSERT OR REPLACE INTO works ({column_names}) VALUES ({placeholders})"
    values = [tuple(r[col] for col in columns) for r in records]

    cursor = conn.executemany(sql, values)
    conn.commit()
    return cursor.rowcount


def process_date_directory(
    date_dir: Path,
    conn: sqlite3.Connection,
    batch_size: int = 10000,
    store_raw: bool = False,
) -> int:
    """Process all .gz files in a date directory and upsert into DB."""
    gz_files = sorted(date_dir.glob("*.gz"))
    if not gz_files:
        return 0

    total = 0
    for gz_file in gz_files:
        batch = []
        file_records = 0

        with gzip.open(gz_file, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    record = parse_work(data, store_raw=store_raw)
                    batch.append(record)
                    file_records += 1

                    if len(batch) >= batch_size:
                        upserted = upsert_batch(conn, batch)
                        total += upserted
                        batch = []
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"Error processing record in {gz_file.name}: {e}")
                    continue

        if batch:
            upserted = upsert_batch(conn, batch)
            total += upserted

        total += 0  # file_records already counted via upsert

    return total


def update_fts_for_changes(conn: sqlite3.Connection) -> None:
    """Rebuild FTS index for recently changed works.

    FTS triggers handle new inserts, but for REPLACE operations
    we need to ensure FTS stays in sync.
    """
    logger.info("Rebuilding FTS index for updated records...")
    try:
        conn.execute("INSERT INTO works_fts(works_fts) VALUES('rebuild')")
        conn.commit()
        logger.info("FTS rebuild complete.")
    except sqlite3.OperationalError as e:
        logger.warning(f"FTS rebuild skipped (table may not exist): {e}")


def differential_update(
    db_path: Path,
    snapshot_dir: Path,
    since: Optional[str] = None,
    batch_size: int = 10000,
    store_raw: bool = False,
    dry_run: bool = False,
    skip_download: bool = False,
    rebuild_fts: bool = True,
) -> dict:
    """Run differential update.

    Parameters
    ----------
    db_path : Path
        Path to SQLite database.
    snapshot_dir : Path
        Path to snapshot works directory.
    since : str, optional
        Override: only update from this date (YYYY-MM-DD).
    batch_size : int
        Records per database batch.
    store_raw : bool
        Store raw JSON in database.
    dry_run : bool
        List what would be downloaded without doing it.
    skip_download : bool
        Skip download, process existing files only.
    rebuild_fts : bool
        Rebuild FTS index after update.

    Returns
    -------
    dict
        Statistics: dates_processed, records_upserted, elapsed_seconds.
    """
    # Determine start date (may need DB for last sync date)
    conn = None
    if since is None and db_path.exists():
        conn = sqlite3.connect(db_path)
        since = get_last_sync_date(conn)
        if since:
            logger.info(f"Last sync date: {since}")

    if since is None:
        since = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        logger.info(f"No sync history — defaulting to last 30 days ({since})")

    # List available updates
    new_dates = list_s3_updated_dates(since=since)

    if not new_dates:
        logger.info("No new updates available.")
        if conn:
            conn.close()
        return {"dates_processed": 0, "records_upserted": 0, "elapsed_seconds": 0}

    logger.info(f"Updates available: {len(new_dates)} date directories")
    logger.info(f"  From: {new_dates[0]}")
    logger.info(f"  To:   {new_dates[-1]}")

    if dry_run:
        logger.info("DRY RUN — no changes will be made.")
        for d in new_dates:
            logger.info(f"  Would download: updated_date={d}")
        if conn:
            conn.close()
        return {"dates_processed": 0, "records_upserted": 0, "elapsed_seconds": 0, "dry_run": True}

    # Open DB connection for actual processing
    if conn is None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-2000000")

    # Ensure metadata table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()

    start_time = time.time()

    # Download new directories
    if not skip_download:
        downloaded = download_date_directories(new_dates, snapshot_dir)
        logger.info(f"Downloaded {len(downloaded)} directories.")
    else:
        downloaded = [
            snapshot_dir / f"updated_date={d}"
            for d in new_dates
            if (snapshot_dir / f"updated_date={d}").exists()
        ]
        logger.info(f"Skipping download — found {len(downloaded)} existing directories.")

    # Process and upsert
    total_upserted = 0
    for i, date_dir in enumerate(downloaded):
        date = date_dir.name.replace("updated_date=", "")
        logger.info(f"[{i+1}/{len(downloaded)}] Processing {date}...")

        upserted = process_date_directory(
            date_dir, conn,
            batch_size=batch_size,
            store_raw=store_raw,
        )
        total_upserted += upserted
        logger.info(f"  Upserted {upserted:,} records.")

    # Update last sync date
    if new_dates:
        set_last_sync_date(conn, new_dates[-1])
        logger.info(f"Updated last_sync_date to {new_dates[-1]}")

    # Rebuild FTS
    if rebuild_fts and total_upserted > 0:
        update_fts_for_changes(conn)

    # Update metadata
    conn.execute(
        "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
        ("last_update_completed", time.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.execute(
        "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
        ("last_update_records", str(total_upserted)),
    )
    conn.commit()

    elapsed = time.time() - start_time

    logger.info("=" * 60)
    logger.info("Differential update complete!")
    logger.info(f"  Dates processed: {len(downloaded)}")
    logger.info(f"  Records upserted: {total_upserted:,}")
    logger.info(f"  Elapsed: {elapsed / 60:.1f} minutes")

    conn.close()
    return {
        "dates_processed": len(downloaded),
        "records_upserted": total_upserted,
        "elapsed_seconds": elapsed,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Differential update for OpenAlex database"
    )
    parser.add_argument(
        "--db-path", type=Path, default=DEFAULT_DB_PATH,
        help=f"Database path (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR,
        help=f"Snapshot directory (default: {DEFAULT_SNAPSHOT_DIR})",
    )
    parser.add_argument(
        "--since", type=str, default=None,
        help="Override start date (YYYY-MM-DD). Default: read from DB.",
    )
    parser.add_argument(
        "--batch-size", type=int, default=10000,
        help="Batch size for inserts (default: 10000)",
    )
    parser.add_argument(
        "--store-raw", action="store_true",
        help="Store raw JSON in database",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List updates without downloading or processing",
    )
    parser.add_argument(
        "--skip-download", action="store_true",
        help="Skip download, process existing snapshot files only",
    )
    parser.add_argument(
        "--no-fts-rebuild", action="store_true",
        help="Skip FTS index rebuild after update",
    )

    args = parser.parse_args()

    stats = differential_update(
        db_path=args.db_path,
        snapshot_dir=args.snapshot_dir,
        since=args.since,
        batch_size=args.batch_size,
        store_raw=args.store_raw,
        dry_run=args.dry_run,
        skip_download=args.skip_download,
        rebuild_fts=not args.no_fts_rebuild,
    )

    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

# EOF
