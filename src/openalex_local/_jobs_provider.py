#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SciTeX ecosystem ``scitex_dev.jobs`` provider for openalex-local.

Registered via ``pyproject.toml``::

    [project.entry-points."scitex_dev.jobs"]
    openalex-incremental-update = "openalex_local._jobs_provider:get_jobs"

``scitex-dev ecosystem cron install`` discovers this provider, calls
``get_jobs()``, and writes the returned ``JobSpec`` objects into the
user's crontab inside the managed block.

The single job exported here runs the differential update script on a
weekly cadence (Sun 03:00 UTC). Before the diff script runs, it seeds
``_metadata.last_sync_date`` from the DB's own data-cutoff metadata so
the first scheduled invocation catches up the FULL backlog instead of
silently falling back to the last 30 days.

Resolution rules (in order):

1. DB path:
   - ``$SCITEX_OPENALEX_DB_PATH`` if set.
   - ``~/proj/openalex-local.bak/data/openalex.db`` otherwise (the
     canonical NAS location; the repo's ``data/openalex.db`` is a
     1.3TB-too-small placeholder directory — see PR description).

2. Snapshot dir:
   - ``$SCITEX_OPENALEX_SNAPSHOT_DIR`` if set.
   - ``~/proj/openalex-local.bak/data/snapshot/works`` otherwise.

3. Log dir: ``~/.scitex/openalex-local/logs/``; one file per UTC date.

No AWS keys are required or referenced — the script uses
``aws s3 ... --no-sign-request`` against the public OpenAlex bucket.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# scitex-dev is a dev-time dependency of openalex-local (see [project.
# optional-dependencies].dev in pyproject.toml). The entry-point group
# is only consulted by scitex-dev itself, so importing JobSpec here is
# safe in any environment where the discovery code runs.
from scitex_dev.jobs import JobSpec

__all__ = ["get_jobs", "JOB_NAME", "CRON_SCHEDULE"]

#: Stable, package-prefixed job name (matches scitex_dev.jobs convention).
JOB_NAME = "openalex-local.incremental-update"

#: Weekly cadence — Sun 03:00 UTC. Chosen because OpenAlex's published
#: ``updated_date=YYYY-MM-DD/`` directories land daily, so weekly catch-up
#: keeps the working DB at most ~7 days stale while leaving plenty of
#: room for a multi-hour download/upsert window.
CRON_SCHEDULE = "0 3 * * 0"

# --- default paths --------------------------------------------------- #
# The 1.3TB canonical DB lives in the .bak tree on the operator's NAS;
# the in-repo ``data/openalex.db`` is a broken placeholder directory.
# We refuse to hard-code the bak path inside Python source — it leaks
# host-specific layout — but we DO carry it as a documented default so
# the job works out of the box on the only host where it currently
# runs. Override via $SCITEX_OPENALEX_DB_PATH.
_DEFAULT_DB_PATH = Path.home() / "proj/openalex-local.bak/data/openalex.db"
_DEFAULT_SNAPSHOT_DIR = Path.home() / "proj/openalex-local.bak/data/snapshot/works"
_DEFAULT_LOG_DIR = Path.home() / ".scitex/openalex-local/logs"


def _resolve_db_path() -> Path:
    env = os.environ.get("SCITEX_OPENALEX_DB_PATH")
    return Path(env).expanduser() if env else _DEFAULT_DB_PATH


def _resolve_snapshot_dir() -> Path:
    env = os.environ.get("SCITEX_OPENALEX_SNAPSHOT_DIR")
    return Path(env).expanduser() if env else _DEFAULT_SNAPSHOT_DIR


def _resolve_log_dir() -> Path:
    env = os.environ.get("SCITEX_OPENALEX_LOG_DIR")
    return Path(env).expanduser() if env else _DEFAULT_LOG_DIR


def _resolve_script_path() -> Path:
    """Locate the differential-update script ON-DISK.

    Resolution: the script is shipped under ``scripts/database/`` of the
    git checkout (not installed as a console script). We climb out of
    the source tree from this module to find it. The cron job runs the
    script as a child interpreter, so we need a real path string.
    """
    # src/openalex_local/_jobs_provider.py -> src/openalex_local ->
    # src -> repo_root
    repo_root = Path(__file__).resolve().parent.parent.parent
    return repo_root / "scripts" / "database" / "10_differential_update.py"


def _build_command(
    *,
    python: str,
    seed_module: str,
    script_path: Path,
    db_path: Path,
    snapshot_dir: Path,
    log_dir: Path,
) -> str:
    """Construct the full shell command string for the JobSpec.

    The command is a single shell line so crontab accepts it. It:

      1. Ensures the log dir exists.
      2. Seeds ``_metadata.last_sync_date`` (no-op if already set).
      3. Runs the diff-update script, streaming stdout+stderr into a
         per-day log file via ``tee -a``.

    ``set -o pipefail`` propagates a non-zero exit from the python
    process through ``tee`` so cron records the failure.
    """
    log_glob = "$(date -u +%Y-%m-%d).log"
    return (
        "/bin/bash -lc '"
        "set -o pipefail; "
        f"mkdir -p {log_dir} && "
        f"{python} -m {seed_module} {db_path} && "
        f"{python} {script_path} "
        f"--db-path {db_path} "
        f"--snapshot-dir {snapshot_dir} "
        f"2>&1 | tee -a {log_dir}/{log_glob}"
        "'"
    )


def get_jobs() -> list[JobSpec]:
    """Return the openalex-local jobs registered with scitex_dev.

    Currently a single weekly cron job that:

    * seeds ``_metadata.last_sync_date`` from the DB's data-cutoff
      metadata on the FIRST run (idempotent thereafter), so the catch-up
      covers the full backlog instead of only the last 30 days;
    * runs ``scripts/database/10_differential_update.py`` against the
      canonical DB and snapshot dir;
    * tees output into ``~/.scitex/openalex-local/logs/<UTC date>.log``.

    The job is upsert-only (the diff script uses ``INSERT OR REPLACE``);
    re-running it against a fully-current DB is a fast no-op (just an S3
    LIST + zero new dirs).
    """
    db_path = _resolve_db_path()
    snapshot_dir = _resolve_snapshot_dir()
    log_dir = _resolve_log_dir()
    script_path = _resolve_script_path()

    command = _build_command(
        python=sys.executable or "python3",
        seed_module="openalex_local._seed_last_sync",
        script_path=script_path,
        db_path=db_path,
        snapshot_dir=snapshot_dir,
        log_dir=log_dir,
    )

    return [
        JobSpec(
            name=JOB_NAME,
            kind="cron",
            schedule=CRON_SCHEDULE,
            command=command,
            description=(
                "Weekly OpenAlex incremental update: seed last_sync_date "
                "from DB metadata, then diff-sync new updated_date=… S3 "
                "dirs into the canonical DB (read-only S3, UPSERT-only)."
            ),
        )
    ]


# EOF
