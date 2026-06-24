#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seed ``last_sync_date`` from DB metadata for the incremental updater.

The differential-update script (``scripts/database/10_differential_update.py``)
reads ``_metadata.last_sync_date`` to know where to resume from. When that
row is missing, the script falls back to ``today - 30 days`` which silently
*skips* any backlog older than 30 days.

For an OpenAlex database that was last bulk-built months earlier, that
default is wrong: the first scheduled run would only see the last 30 days
of S3 directories and pretend everything older is already current.

This helper plants the correct starting cursor BEFORE the diff script runs:

* If ``_metadata.last_sync_date`` is already set, do nothing (idempotent —
  safe to run on every scheduled invocation).
* Otherwise, derive a sensible cursor from the same ``_metadata`` table
  (``data_cutoff_date``, ``snapshot_date``, ``last_built_date``,
  ``build_date``, or ``created_at`` — whichever is present first), and
  write it back as ``last_sync_date``.

Only the ``_metadata`` table is touched. ``works`` is never read or
written. The function is intended to be called from the cron-driven
JobSpec command before the diff-update script.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Optional

_logger = logging.getLogger(__name__)

# Order matters: prefer the most explicit cursor first.
_CANDIDATE_KEYS: tuple[str, ...] = (
    "data_cutoff_date",
    "snapshot_date",
    "last_built_date",
    "build_date",
    "created_at",
)


def _read_metadata(conn: sqlite3.Connection, key: str) -> Optional[str]:
    """Return the value of ``_metadata[key]`` or ``None`` if missing."""
    try:
        cursor = conn.execute("SELECT value FROM _metadata WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        # _metadata table doesn't exist yet (fresh / empty DB).
        return None


def _normalize_date(value: str) -> str:
    """Trim a metadata value to a ``YYYY-MM-DD`` date prefix.

    Callers store both bare dates (``2026-01-14``) and timestamps
    (``2026-01-14 03:42:11``). The diff-update script compares as plain
    string ``YYYY-MM-DD``, so the first 10 chars is what it needs.
    """
    return value.strip()[:10]


def seed_last_sync_date(
    db_path: Path,
    *,
    fallback: Optional[str] = None,
) -> Optional[str]:
    """Plant ``last_sync_date`` in ``_metadata`` if it isn't already set.

    Parameters
    ----------
    db_path : Path
        Path to the SQLite database to seed.
    fallback : str, optional
        Date string used when no candidate key is present in
        ``_metadata``. Pass ``None`` (the default) to leave the row unset
        when nothing reasonable can be derived — the diff-update script
        will then apply its built-in 30-day fallback.

    Returns
    -------
    str or None
        The date that was written into ``last_sync_date`` by THIS call,
        or ``None`` if no change was made (already set, or no candidate
        available).
    """
    if not db_path.exists():
        _logger.warning("seed_last_sync_date: db not found at %s", db_path)
        return None

    conn = sqlite3.connect(db_path)
    try:
        existing = _read_metadata(conn, "last_sync_date")
        if existing:
            _logger.info(
                "seed_last_sync_date: last_sync_date already set to %r — no-op",
                existing,
            )
            return None

        # Ensure _metadata exists for the upcoming write (the diff-update
        # script creates it lazily; we do too so this helper is safe to
        # call against a fresh DB).
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _metadata (key TEXT PRIMARY KEY, value TEXT)"
        )

        seed: Optional[str] = None
        for key in _CANDIDATE_KEYS:
            raw = _read_metadata(conn, key)
            if raw:
                seed = _normalize_date(raw)
                _logger.info(
                    "seed_last_sync_date: derived %r from _metadata[%r]=%r",
                    seed,
                    key,
                    raw,
                )
                break

        if seed is None:
            if fallback is None:
                _logger.warning(
                    "seed_last_sync_date: no candidate key found and no "
                    "fallback supplied — leaving last_sync_date unset"
                )
                return None
            seed = _normalize_date(fallback)
            _logger.info(
                "seed_last_sync_date: no candidate key found — using fallback %r",
                seed,
            )

        conn.execute(
            "INSERT OR REPLACE INTO _metadata (key, value) VALUES (?, ?)",
            ("last_sync_date", seed),
        )
        conn.commit()
        return seed
    finally:
        conn.close()


def main() -> int:
    """CLI entry-point: ``python -m openalex_local._seed_last_sync DB_PATH``."""
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Idempotently seed _metadata.last_sync_date so the "
            "incremental updater catches up the full backlog on first run."
        )
    )
    parser.add_argument("db_path", type=Path, help="Path to openalex.db")
    parser.add_argument(
        "--fallback",
        type=str,
        default=None,
        help=(
            "Fallback date (YYYY-MM-DD) when no candidate key is present "
            "in _metadata. Leave unset to defer to the diff-update "
            "script's own 30-day fallback."
        ),
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    written = seed_last_sync_date(args.db_path, fallback=args.fallback)
    if written:
        print(f"seeded last_sync_date = {written}")
    else:
        print("no-op (already set, or nothing to derive)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# EOF
