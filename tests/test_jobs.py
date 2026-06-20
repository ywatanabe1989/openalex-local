"""Tests for openalex_local.jobs module."""

import tempfile
from pathlib import Path

import pytest

from openalex_local import jobs


JOBS_PUBLIC_API = ["create", "get", "list_jobs", "run"]


def _sample_job_dict():
    """Return a serialized job dict for from_dict round-trips."""
    return {
        "id": "test456",
        "items": ["p", "q"],
        "completed": ["p"],
        "failed": {},
        "status": "running",
        "created_at": 1234567890.0,
        "updated_at": 1234567890.0,
        "metadata": {"name": "test"},
    }


class TestJobsModule:
    """Test the jobs module public API."""

    @pytest.mark.parametrize("name", JOBS_PUBLIC_API)
    def test_jobs_module_exposes_callable(self, name):
        """Test the jobs module exposes each public function as callable."""
        # Arrange
        attr = getattr(jobs, name, None)
        # Act
        is_callable = callable(attr)
        # Assert
        assert is_callable is True


class TestJobQueueInternal:
    """Test _JobQueue class directly with temp directory (internal API)."""

    @pytest.fixture
    def queue(self):
        """Return a _JobQueue backed by a throwaway directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield jobs._JobQueue(jobs_dir=Path(tmpdir))

    def test_create_returns_job_with_items(self, queue):
        """Test create returns a job carrying the supplied items."""
        # Arrange
        items = ["item1", "item2"]
        # Act
        job = queue.create(items=items, name="test_job")
        # Assert
        assert job.items == ["item1", "item2"]

    def test_create_records_job_name_in_metadata(self, queue):
        """Test create stores the job name in its metadata."""
        # Arrange
        items = ["item1", "item2"]
        # Act
        job = queue.create(items=items, name="test_job")
        # Assert
        assert job.metadata.get("name") == "test_job"

    def test_create_persists_job_for_reload(self, queue):
        """Test a created job can be loaded back from disk."""
        # Arrange
        job = queue.create(items=["item1", "item2", "item3"], name="test_job")
        # Act
        loaded = queue.load(job.id)
        # Assert
        assert loaded is not None

    def test_create_persists_all_items(self, queue):
        """Test a reloaded job preserves every item."""
        # Arrange
        job = queue.create(items=["item1", "item2", "item3"], name="test_job")
        # Act
        loaded = queue.load(job.id)
        # Assert
        assert len(loaded.items) == 3

    def test_load_nonexistent_job_returns_none(self, queue):
        """Test loading an unknown job id returns None."""
        # Arrange
        unknown_id = "nonexistent_job_id"
        # Act
        result = queue.load(unknown_id)
        # Assert
        assert result is None

    def test_list_returns_list_type(self, queue):
        """Test list returns a list even when empty."""
        # Arrange
        empty_queue = queue
        # Act
        result = empty_queue.list()
        # Assert
        assert isinstance(result, list)

    def test_list_includes_created_jobs(self, queue):
        """Test list includes the ids of created jobs."""
        # Arrange
        job1 = queue.create(items=["a"], name="job1")
        job2 = queue.create(items=["b"], name="job2")
        # Act
        job_ids = [j.id for j in queue.list()]
        # Assert
        assert job1.id in job_ids and job2.id in job_ids

    def test_delete_reports_success(self, queue):
        """Test delete returns True when removing an existing job."""
        # Arrange
        job = queue.create(items=["a"])
        # Act
        result = queue.delete(job.id)
        # Assert
        assert result is True

    def test_delete_removes_job_from_store(self, queue):
        """Test a deleted job can no longer be loaded."""
        # Arrange
        job = queue.create(items=["a"])
        queue.delete(job.id)
        # Act
        loaded = queue.load(job.id)
        # Assert
        assert loaded is None


class TestJobInternal:
    """Test _Job dataclass (internal API)."""

    def test_job_pending_excludes_completed_and_failed(self):
        """Test pending returns items neither completed nor failed."""
        # Arrange
        job = jobs._Job(id="test", items=["a", "b", "c"])
        job.completed = ["a"]
        job.failed = {"b": "error"}
        # Act
        pending = job.pending
        # Assert
        assert pending == ["c"]

    def test_job_progress_reports_completion_percentage(self):
        """Test progress returns the completed fraction as a percentage."""
        # Arrange
        job = jobs._Job(id="test", items=["a", "b", "c", "d"])
        job.completed = ["a", "b"]
        # Act
        progress = job.progress
        # Assert
        assert progress == 50.0

    def test_job_to_dict_includes_id(self):
        """Test to_dict serializes the job id."""
        # Arrange
        job = jobs._Job(id="test123", items=["x", "y"])
        # Act
        d = job.to_dict()
        # Assert
        assert d["id"] == "test123"

    def test_job_to_dict_includes_items(self):
        """Test to_dict serializes the job items."""
        # Arrange
        job = jobs._Job(id="test123", items=["x", "y"])
        # Act
        d = job.to_dict()
        # Assert
        assert d["items"] == ["x", "y"]

    def test_job_to_dict_includes_status(self):
        """Test to_dict serializes the job status field."""
        # Arrange
        job = jobs._Job(id="test123", items=["x", "y"])
        # Act
        d = job.to_dict()
        # Assert
        assert "status" in d

    def test_job_from_dict_restores_id(self):
        """Test from_dict reconstructs the job id."""
        # Arrange
        data = _sample_job_dict()
        # Act
        job = jobs._Job.from_dict(data)
        # Assert
        assert job.id == "test456"

    def test_job_from_dict_restores_items(self):
        """Test from_dict reconstructs the job items."""
        # Arrange
        data = _sample_job_dict()
        # Act
        job = jobs._Job.from_dict(data)
        # Assert
        assert job.items == ["p", "q"]

    def test_job_from_dict_restores_completed(self):
        """Test from_dict reconstructs the completed list."""
        # Arrange
        data = _sample_job_dict()
        # Act
        job = jobs._Job.from_dict(data)
        # Assert
        assert job.completed == ["p"]

    def test_job_from_dict_restores_status(self):
        """Test from_dict reconstructs the running status."""
        # Arrange
        data = _sample_job_dict()
        # Act
        job = jobs._Job.from_dict(data)
        # Assert
        assert job.status == "running"
