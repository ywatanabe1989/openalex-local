# Runtime directory for openalex-local

This directory contains regenerable, per-host runtime data — caches,
job queues, logs, and the embedded SQLite database when stored at the
user scope.  Everything under `runtime/` is excluded from git; only
`.gitkeep` and this `README.md` are tracked.

See: `scitex-dev` skill `01_ecosystem/06_local-state-directories.md` for
the canonical layout.
