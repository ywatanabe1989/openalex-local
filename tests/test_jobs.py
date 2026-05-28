"""Tests for openalex_local.jobs module."""

import tempfile
from pathlib import Path

import pytest

from openalex_local import jobs


@pytest.mark.unit
class TestJobsModule:
    """Test the jobs module public API."""

    def test_jobs_module_has_create_function(self):
        """Test that jobs module exports create function."""
        # Arrange — (nothing; import at module level)
        # Act — (nothing; testing attributes)
        # Assert
        assert hasattr(jobs, "create") and callable(jobs.create)

    def test_jobs_module_has_get_function(self):
        """Test that jobs module exports get function."""
        # Arrange — (nothing)
        # Act — (nothing)
        # Assert
        assert hasattr(jobs, "get") and callable(jobs.get)

    def test_jobs_module_has_list_jobs_function(self):
        """Test that jobs module exports list_jobs function."""
        # Arrange — (nothing)
        # Act — (nothing)
        # Assert
        assert hasattr(jobs, "list_jobs") and callable(jobs.list_jobs)

    def test_jobs_module_has_run_function(self):
        """Test that jobs module exports run function."""
        # Arrange — (nothing)
        # Act — (nothing)
        # Assert
        assert hasattr(jobs, "run") and callable(jobs.run)


@pytest.mark.unit
class TestJobQueueInternal:
    """Test _JobQueue class directly with temp directory (internal API)."""

    def test_create_returns_job_with_id(self):
        """Test that create returns a _Job object with id."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs._JobQueue(jobs_dir=Path(tmpdir))
            # Act
            job = queue.create(items=["item1", "item2"], name="test_job")
            # Assert
            assert hasattr(job, "id")

    def test_create_stores_provided_items(self):
        """Test that create stores provided items."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs._JobQueue(jobs_dir=Path(tmpdir))
            # Act
            job = queue.create(items=["item1", "item2"], name="test_job")
            # Assert
            assert job.items == ["item1", "item2"]

    def test_create_stores_name_in_metadata(self):
        """Test that create stores name in metadata."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs._JobQueue(jobs_dir=Path(tmpdir))
            # Act
            job = queue.create(items=["item1", "item2"], name="test_job")
            # Assert
            assert job.metadata.get("name") == "test_job"

    def test_load_returns_created_job_after_create(self):
        """Test that load returns the created job."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs._JobQueue(jobs_dir=Path(tmpdir))
            job = queue.create(items=["item1", "item2", "item3"], name="test_job")
            # Act
            loaded = queue.load(job.id)
            # Assert
            assert loaded is not None

    def test_load_restores_metadata_name(self):
        """Test that loaded job preserves metadata name."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs._JobQueue(jobs_dir=Path(tmpdir))
            job = queue.create(items=["item1", "item2", "item3"], name="test_job")
            # Act
            loaded = queue.load(job.id)
            # Assert
            assert loaded.metadata.get("name") == "test_job"

    def test_load_restores_item_count(self):
        """Test that loaded job preserves item count."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs._JobQueue(jobs_dir=Path(tmpdir))
            job = queue.create(items=["item1", "item2", "item3"], name="test_job")
            # Act
            loaded = queue.load(job.id)
            # Assert
            assert len(loaded.items) == 3

    def test_load_nonexistent_returns_none(self):
        """Test that loading non-existent job returns None."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs._JobQueue(jobs_dir=Path(tmpdir))
            # Act
            result = queue.load("nonexistent_job_id")
            # Assert
            assert result is None

    def test_list_returns_empty_list_initially(self):
        """Test that list returns empty list for new queue."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs._JobQueue(jobs_dir=Path(tmpdir))
            # Act
            result = queue.list()
            # Assert
            assert isinstance(result, list)

    def test_list_contains_first_created_job(self):
        """Test that list includes first created job."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs._JobQueue(jobs_dir=Path(tmpdir))
            job1 = queue.create(items=["a"], name="job1")
            queue.create(items=["b"], name="job2")
            # Act
            job_list = queue.list()
            job_ids = [j.id for j in job_list]
            # Assert
            assert job1.id in job_ids

    def test_list_contains_second_created_job(self):
        """Test that list includes second created job."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs._JobQueue(jobs_dir=Path(tmpdir))
            queue.create(items=["a"], name="job1")
            job2 = queue.create(items=["b"], name="job2")
            # Act
            job_list = queue.list()
            job_ids = [j.id for j in job_list]
            # Assert
            assert job2.id in job_ids

    def test_delete_returns_true_for_existing_job(self):
        """Test that delete returns True for existing job."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs._JobQueue(jobs_dir=Path(tmpdir))
            job = queue.create(items=["a"])
            # Act
            result = queue.delete(job.id)
            # Assert
            assert result is True

    def test_delete_removes_job_from_queue(self):
        """Test that delete removes job from queue."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs._JobQueue(jobs_dir=Path(tmpdir))
            job = queue.create(items=["a"])
            # Act
            queue.delete(job.id)
            # Assert
            assert queue.load(job.id) is None


@pytest.mark.unit
class TestJobInternal:
    """Test _Job dataclass (internal API)."""

    def test_pending_returns_unprocessed_items(self):
        """Test pending property returns items not processed."""
        # Arrange
        job = jobs._Job(id="test", items=["a", "b", "c"])
        job.completed = ["a"]
        job.failed = {"b": "error"}
        # Act
        pending = job.pending
        # Assert
        assert pending == ["c"]

    def test_progress_returns_fifty_for_half_completed(self):
        """Test progress property returns correct percentage."""
        # Arrange
        job = jobs._Job(id="test", items=["a", "b", "c", "d"])
        job.completed = ["a", "b"]
        # Act
        progress = job.progress
        # Assert
        assert progress == 50.0

    def test_to_dict_contains_job_id(self):
        """Test to_dict serialization includes id."""
        # Arrange
        job = jobs._Job(id="test123", items=["x", "y"])
        # Act
        d = job.to_dict()
        # Assert
        assert d["id"] == "test123"

    def test_to_dict_contains_items(self):
        """Test to_dict serialization includes items."""
        # Arrange
        job = jobs._Job(id="test123", items=["x", "y"])
        # Act
        d = job.to_dict()
        # Assert
        assert d["items"] == ["x", "y"]

    def test_to_dict_contains_status_field(self):
        """Test to_dict serialization includes status."""
        # Arrange
        job = jobs._Job(id="test123", items=["x", "y"])
        # Act
        d = job.to_dict()
        # Assert
        assert "status" in d

    def test_to_dict_contains_created_at_field(self):
        """Test to_dict serialization includes created_at."""
        # Arrange
        job = jobs._Job(id="test123", items=["x", "y"])
        # Act
        d = job.to_dict()
        # Assert
        assert "created_at" in d

    def test_from_dict_restores_job_id(self):
        """Test from_dict deserialization restores id."""
        # Arrange
        data = {
            "id": "test456",
            "items": ["p", "q"],
            "completed": ["p"],
            "failed": {},
            "status": "running",
            "created_at": 1234567890.0,
            "updated_at": 1234567890.0,
            "metadata": {"name": "test"},
        }
        # Act
        job = jobs._Job.from_dict(data)
        # Assert
        assert job.id == "test456"

    def test_from_dict_restores_items(self):
        """Test from_dict deserialization restores items."""
        # Arrange
        data = {
            "id": "test456",
            "items": ["p", "q"],
            "completed": ["p"],
            "failed": {},
            "status": "running",
            "created_at": 1234567890.0,
            "updated_at": 1234567890.0,
            "metadata": {"name": "test"},
        }
        # Act
        job = jobs._Job.from_dict(data)
        # Assert
        assert job.items == ["p", "q"]

    def test_from_dict_restores_completed(self):
        """Test from_dict deserialization restores completed items."""
        # Arrange
        data = {
            "id": "test456",
            "items": ["p", "q"],
            "completed": ["p"],
            "failed": {},
            "status": "running",
            "created_at": 1234567890.0,
            "updated_at": 1234567890.0,
            "metadata": {"name": "test"},
        }
        # Act
        job = jobs._Job.from_dict(data)
        # Assert
        assert job.completed == ["p"]

    def test_from_dict_restores_status(self):
        """Test from_dict deserialization restores status."""
        # Arrange
        data = {
            "id": "test456",
            "items": ["p", "q"],
            "completed": ["p"],
            "failed": {},
            "status": "running",
            "created_at": 1234567890.0,
            "updated_at": 1234567890.0,
            "metadata": {"name": "test"},
        }
        # Act
        job = jobs._Job.from_dict(data)
        # Assert
        assert job.status == "running"
