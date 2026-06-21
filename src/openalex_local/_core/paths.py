#!/usr/bin/env python3
# Timestamp: 2026-01-29
"""Path resolution for openalex-local local state directories.

Canonical layout per scitex-dev local-state-directories rule:

    ~/.scitex/openalex-local/
    ├── config.yaml                          # Tracked — user config
    └── runtime/                             # Untracked — regenerable data
        ├── .gitkeep
        ├── README.md
        ├── cache/                           # Cache files (*.json)
        ├── jobs/                            # Job state files (*.json)
        └── openalex.db                      # DB (when at user scope)

Relocation via ``$SCITEX_DIR``:

    export SCITEX_DIR=/mnt/fast-ssd/scitex
    → runtime root = /mnt/fast-ssd/scitex/openalex-local/runtime/

Backward-compatibility (§8 of local-state-directories skill):

    Old location ``~/.openalex_local/{caches,jobs}/`` is migrated on first
    access: contents are moved to the new tree and a one-time deprecation
    warning is emitted via ``warnings.warn``.  The fallback read path is
    kept for one minor version.
"""

import os as _os
import shutil as _shutil
import warnings as _warnings
from pathlib import Path as _Path
from typing import Iterator as _Iterator

# ---------------------------------------------------------------------------
# Package identity
# ---------------------------------------------------------------------------

_PKG_SHORT = "openalex-local"  # same as pip name (no scitex- prefix to strip)

# ---------------------------------------------------------------------------
# Legacy paths (back-compat, §8)
# ---------------------------------------------------------------------------

_OLD_HOME_DIR = _Path.home() / ".openalex_local"

# ---------------------------------------------------------------------------
# Public resolvers
# ---------------------------------------------------------------------------


def _scitex_root() -> _Path:
    """Return the user-scope root ``<SCITEX_DIR>/openalex-local/``.

    Respects ``$SCITEX_DIR``; falls back to ``~/.scitex/``.
    """
    base = _Path(_os.environ.get("SCITEX_DIR", _Path.home() / ".scitex"))
    return base / _PKG_SHORT


def get_runtime_dir() -> _Path:
    """Return the runtime directory, creating it lazily if needed.

    Resolves to::

        $SCITEX_DIR/openalex-local/runtime/
        ~/.scitex/openalex-local/runtime/   (default)

    On first call, migrates legacy ``~/.openalex_local/`` state and emits
    a deprecation warning if old data was found.
    """
    d = _scitex_root() / "runtime"
    d.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_once(d)
    return d


def get_cache_dir() -> _Path:
    """Return the cache directory under runtime.

    ``<runtime>/cache/`` — created lazily.
    """
    d = get_runtime_dir() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_jobs_dir() -> _Path:
    """Return the jobs directory under runtime.

    ``<runtime>/jobs/`` — created lazily.
    """
    d = get_runtime_dir() / "jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Backward-compatibility migration (§8)
# ---------------------------------------------------------------------------

_MIGRATED: bool = False


def _migrate_legacy_once(new_runtime: _Path) -> None:
    """Migrate old ``~/.openalex_local/{caches,jobs}`` → new runtime dirs.

    Runs at most once per process (idempotent after first call).
    """
    global _MIGRATED
    if _MIGRATED:
        return

    old = _OLD_HOME_DIR
    if not old.is_dir():
        _MIGRATED = True
        return

    # ── caches → runtime/cache/ ──────────────────────────────────────
    old_caches = old / "caches"
    new_cache = new_runtime / "cache"
    if old_caches.is_dir() and not _dir_is_nonempty(new_cache):
        _move_contents(old_caches, new_cache)
        _warnings.warn(
            f"Moved caches from {old_caches} to {new_cache}. "
            f"The old location is deprecated and will be removed in a future version.",
            DeprecationWarning,
            stacklevel=3,
        )

    # ── jobs → runtime/jobs/ ─────────────────────────────────────────
    old_jobs = old / "jobs"
    new_jobs = new_runtime / "jobs"
    if old_jobs.is_dir() and not _dir_is_nonempty(new_jobs):
        _move_contents(old_jobs, new_jobs)
        _warnings.warn(
            f"Moved job state from {old_jobs} to {new_jobs}. "
            f"The old location is deprecated and will be removed in a future version.",
            DeprecationWarning,
            stacklevel=3,
        )

    _MIGRATED = True


def _dir_is_nonempty(p: _Path) -> bool:
    """Return True if *p* exists and contains at least one entry."""
    if not p.is_dir():
        return False
    try:
        next(p.iterdir())
        return True
    except StopIteration:
        return False


def _move_contents(src: _Path, dst: _Path) -> None:
    """Move every entry from *src* into *dst*.

    *dst* is created if it does not exist.  Conflicts are resolved by
    overwriting files (``shutil.move`` semantics).
    """
    dst.mkdir(parents=True, exist_ok=True)
    for entry in src.iterdir():
        dest = dst / entry.name
        if dest.exists():
            if entry.is_file():
                dest.unlink()
            else:
                _shutil.rmtree(dest)
        _shutil.move(str(entry), str(dest))


# ---------------------------------------------------------------------------
# Convenience: iterate known runtime subdirs
# ---------------------------------------------------------------------------


def iter_runtime_dirs() -> _Iterator[_Path]:
    """Yield all standard runtime subdirectories."""
    rt = get_runtime_dir()
    yield rt / "cache"
    yield rt / "jobs"


# EOF
