#!/usr/bin/env python3
# Timestamp: 2026-01-29
"""Simple job/queue system for batch operations."""

import json as _json
import time as _time
import uuid as _uuid
from dataclasses import dataclass as _dataclass
from dataclasses import field as _field
from pathlib import Path as _Path
from typing import Any as _Any
from typing import Callable as _Callable
from typing import Optional as _Optional

__all__ = ["create", "get", "list_jobs", "run"]

# Default jobs directory
_JOBS_DIR = _Path.home() / ".openalex_local" / "jobs"


@_dataclass
class _Job:
    """A batch job with progress tracking (internal)."""

    id: str
    items: list[str]  # e.g., DOIs or OpenAlex IDs to process
    completed: list[str] = _field(default_factory=list)
    failed: dict[str, str] = _field(default_factory=dict)  # item -> error
    status: str = "pending"  # pending, running, completed, failed
    created_at: float = _field(default_factory=_time.time)
    updated_at: float = _field(default_factory=_time.time)
    metadata: dict[str, _Any] = _field(default_factory=dict)

    @property
    def pending(self) -> list[str]:
        """Items not yet processed."""
        done = set(self.completed) | set(self.failed.keys())
        return [i for i in self.items if i not in done]

    @property
    def progress(self) -> float:
        """Progress as percentage (0-100)."""
        if not self.items:
            return 100.0
        return len(self.completed) / len(self.items) * 100

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "items": self.items,
            "completed": self.completed,
            "failed": self.failed,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "_Job":
        return cls(**data)


class _JobQueue:
    """Manages job persistence and execution (internal)."""

    def __init__(self, jobs_dir: _Optional[_Path] = None):
        self.jobs_dir = _Path(jobs_dir) if jobs_dir else _JOBS_DIR
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def _job_path(self, job_id: str) -> _Path:
        return self.jobs_dir / f"{job_id}.json"

    def save(self, job: _Job) -> None:
        """Save job to disk."""
        job.updated_at = _time.time()
        self._job_path(job.id).write_text(_json.dumps(job.to_dict(), indent=2))

    def load(self, job_id: str) -> _Optional[_Job]:
        """Load job from disk."""
        path = self._job_path(job_id)
        if not path.exists():
            return None
        return _Job.from_dict(_json.loads(path.read_text()))

    def create(self, items: list[str], **metadata) -> _Job:
        """Create a new job."""
        job = _Job(id=str(_uuid.uuid4())[:8], items=items, metadata=metadata)
        self.save(job)
        return job

    def list(self) -> list[_Job]:
        """List all jobs."""
        jobs = []
        for path in self.jobs_dir.glob("*.json"):
            try:
                jobs.append(_Job.from_dict(_json.loads(path.read_text())))
            except Exception:
                continue
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def delete(self, job_id: str) -> bool:
        """Delete a job."""
        path = self._job_path(job_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def run(
        self,
        job: _Job,
        processor: _Callable[[str], _Any],
        on_progress: _Optional[_Callable[[_Job], None]] = None,
    ) -> _Job:
        """Run a job with a processor function."""
        job.status = "running"
        self.save(job)

        for item in job.pending:
            try:
                processor(item)
                job.completed.append(item)
            except Exception as e:
                job.failed[item] = str(e)
            self.save(job)
            if on_progress:
                on_progress(job)

        job.status = "completed" if not job.failed else "failed"
        self.save(job)
        return job


# Module-level convenience functions
_queue = None


def _get_queue() -> _JobQueue:
    global _queue
    if _queue is None:
        _queue = _JobQueue()
    return _queue


def create(items: list[str], **metadata) -> _Job:
    """Create a new job."""
    return _get_queue().create(items, **metadata)


def get(job_id: str) -> _Optional[_Job]:
    """Get a job by ID."""
    return _get_queue().load(job_id)


def list_jobs() -> list[_Job]:
    """List all jobs."""
    return _get_queue().list()


def run(job_id: str, processor: _Callable[[str], _Any]) -> _Job:
    """Run or resume a job."""
    job = get(job_id)
    if not job:
        raise ValueError(f"Job not found: {job_id}")
    return _get_queue().run(job, processor)


# EOF
