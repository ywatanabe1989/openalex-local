#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the ``scitex_dev.jobs`` provider and last-sync seeder.

Covers (one assertion each, AAA markers on their own lines):

* ``get_jobs()`` returns at least one JobSpec.
* The exported JobSpec uses the documented ``0 3 * * 0`` weekly schedule.
* ``seed_last_sync_date`` is a no-op when ``last_sync_date`` is already
  present in the ``_metadata`` table.
* ``seed_last_sync_date`` reads ``data_cutoff_date`` from ``_metadata``
  and writes it back as ``last_sync_date`` when the latter is unset.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def _make_db(path: Path, *, rows: dict[str, str] | None = None) -> Path:
    """Build a tiny SQLite DB with a populated ``_metadata`` table."""
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE _metadata (key TEXT PRIMARY KEY, value TEXT)")
        for k, v in (rows or {}).items():
            conn.execute("INSERT INTO _metadata (key, value) VALUES (?, ?)", (k, v))
        conn.commit()
    finally:
        conn.close()
    return path


def _read_metadata(path: Path, key: str) -> str | None:
    """Return ``_metadata[key]`` from ``path`` (or ``None``)."""
    conn = sqlite3.connect(path)
    try:
        cur = conn.execute("SELECT value FROM _metadata WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def test_get_jobs_returns_at_least_one_spec():
    # Arrange
    from openalex_local._jobs_provider import get_jobs

    # Act
    jobs = get_jobs()

    # Assert
    assert len(jobs) >= 1


def test_get_jobs_uses_weekly_sunday_3am_schedule():
    # Arrange
    from openalex_local._jobs_provider import CRON_SCHEDULE, get_jobs

    # Act
    schedule = get_jobs()[0].schedule

    # Assert
    assert schedule == CRON_SCHEDULE == "0 3 * * 0"


def test_seed_last_sync_is_noop_when_already_set(tmp_path):
    # Arrange
    from openalex_local._seed_last_sync import seed_last_sync_date

    db_path = _make_db(
        tmp_path / "openalex.db",
        rows={
            "last_sync_date": "2026-03-30",
            "data_cutoff_date": "2026-01-14",
        },
    )

    # Act
    result = seed_last_sync_date(db_path)

    # Assert
    assert result is None and _read_metadata(db_path, "last_sync_date") == "2026-03-30"


def test_seed_last_sync_reads_metadata_when_unset(tmp_path):
    # Arrange
    from openalex_local._seed_last_sync import seed_last_sync_date

    db_path = _make_db(
        tmp_path / "openalex.db",
        rows={"data_cutoff_date": "2026-01-14"},
    )

    # Act
    seed_last_sync_date(db_path)

    # Assert
    assert _read_metadata(db_path, "last_sync_date") == "2026-01-14"


# EOF
