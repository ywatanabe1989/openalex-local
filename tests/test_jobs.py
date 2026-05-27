"""Tests for openalex_local.jobs module."""

import tempfile
from pathlib import Path

import pytest

from openalex_local import jobs


# ---------------------------------------------------------------------------
# Public API surface
# ---------------------------------------------------------------------------

def test_jobs_module_exports_create_attribute():
    # Arrange
    target = jobs
    # Act
    present = hasattr(target, "create")
    # Assert
    assert present


def test_jobs_module_exports_get_attribute():
    # Arrange
    target = jobs
    # Act
    present = hasattr(target, "get")
    # Assert
    assert present


def test_jobs_module_exports_list_jobs_attribute():
    # Arrange
    target = jobs
    # Act
    present = hasattr(target, "list_jobs")
    # Assert
    assert present


def test_jobs_module_exports_run_attribute():
    # Arrange
    target = jobs
    # Act
    present = hasattr(target, "run")
    # Assert
    assert present


def test_jobs_create_is_callable():
    # Arrange
    target = jobs.create
    # Act
    callable_now = callable(target)
    # Assert
    assert callable_now


def test_jobs_get_is_callable():
    # Arrange
    target = jobs.get
    # Act
    callable_now = callable(target)
    # Assert
    assert callable_now


def test_jobs_list_jobs_is_callable():
    # Arrange
    target = jobs.list_jobs
    # Act
    callable_now = callable(target)
    # Assert
    assert callable_now


def test_jobs_run_is_callable():
    # Arrange
    target = jobs.run
    # Act
    callable_now = callable(target)
    # Assert
    assert callable_now


# ---------------------------------------------------------------------------
# _JobQueue.create — internal API
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_queue():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield jobs._JobQueue(jobs_dir=Path(tmpdir))


def test_queue_create_returns_object_with_id_attribute(temp_queue):
    # Arrange
    items = ["item1", "item2"]
    # Act
    job = temp_queue.create(items=items, name="test_job")
    # Assert
    assert hasattr(job, "id")


def test_queue_create_assigns_items_to_returned_job(temp_queue):
    # Arrange
    items = ["item1", "item2"]
    # Act
    job = temp_queue.create(items=items, name="test_job")
    # Assert
    assert job.items == items


def test_queue_create_stores_name_in_metadata(temp_queue):
    # Arrange
    items = ["item1", "item2"]
    # Act
    job = temp_queue.create(items=items, name="test_job")
    # Assert
    assert job.metadata.get("name") == "test_job"


def test_queue_create_persists_job_for_load_by_id(temp_queue):
    # Arrange
    items = ["item1", "item2", "item3"]
    job = temp_queue.create(items=items, name="test_job")
    # Act
    loaded = temp_queue.load(job.id)
    # Assert
    assert loaded is not None


def test_queue_load_preserves_metadata_name_round_trip(temp_queue):
    # Arrange
    items = ["item1", "item2", "item3"]
    job = temp_queue.create(items=items, name="test_job")
    # Act
    loaded = temp_queue.load(job.id)
    # Assert
    assert loaded.metadata.get("name") == "test_job"


def test_queue_load_preserves_items_round_trip(temp_queue):
    # Arrange
    items = ["item1", "item2", "item3"]
    job = temp_queue.create(items=items, name="test_job")
    # Act
    loaded = temp_queue.load(job.id)
    # Assert
    assert loaded.items == items


def test_queue_load_returns_none_for_unknown_job_id(temp_queue):
    # Arrange
    unknown_id = "nonexistent_job_id"
    # Act
    result = temp_queue.load(unknown_id)
    # Assert
    assert result is None


def test_queue_list_returns_list_instance(temp_queue):
    # Arrange
    queue = temp_queue
    # Act
    result = queue.list()
    # Assert
    assert isinstance(result, list)


def test_queue_list_includes_created_job_ids(temp_queue):
    # Arrange
    job1 = temp_queue.create(items=["a"], name="job1")
    job2 = temp_queue.create(items=["b"], name="job2")
    # Act
    listed_ids = {j.id for j in temp_queue.list()}
    # Assert
    assert {job1.id, job2.id}.issubset(listed_ids)


def test_queue_delete_returns_true_for_existing_job(temp_queue):
    # Arrange
    job = temp_queue.create(items=["a"])
    # Act
    result = temp_queue.delete(job.id)
    # Assert
    assert result is True


def test_queue_delete_removes_job_from_subsequent_load(temp_queue):
    # Arrange
    job = temp_queue.create(items=["a"])
    temp_queue.delete(job.id)
    # Act
    loaded = temp_queue.load(job.id)
    # Assert
    assert loaded is None


# ---------------------------------------------------------------------------
# _Job dataclass — internal API
# ---------------------------------------------------------------------------

def test_job_pending_returns_only_unprocessed_items():
    # Arrange
    job = jobs._Job(id="test", items=["a", "b", "c"])
    job.completed = ["a"]
    job.failed = {"b": "error"}
    # Act
    pending = job.pending
    # Assert
    assert pending == ["c"]


def test_job_progress_property_returns_percent_completed():
    # Arrange
    job = jobs._Job(id="test", items=["a", "b", "c", "d"])
    job.completed = ["a", "b"]
    # Act
    progress = job.progress
    # Assert
    assert progress == 50.0


@pytest.fixture
def serialized_simple_job():
    job = jobs._Job(id="test123", items=["x", "y"])
    return job.to_dict()


def test_job_to_dict_serializes_id(serialized_simple_job):
    # Arrange
    payload = serialized_simple_job
    # Act
    value = payload["id"]
    # Assert
    assert value == "test123"


def test_job_to_dict_serializes_items(serialized_simple_job):
    # Arrange
    payload = serialized_simple_job
    # Act
    value = payload["items"]
    # Assert
    assert value == ["x", "y"]


def test_job_to_dict_includes_status_key(serialized_simple_job):
    # Arrange
    payload = serialized_simple_job
    # Act
    present = "status" in payload
    # Assert
    assert present


def test_job_to_dict_includes_created_at_key(serialized_simple_job):
    # Arrange
    payload = serialized_simple_job
    # Act
    present = "created_at" in payload
    # Assert
    assert present


@pytest.fixture
def deserialized_running_job():
    data = {
        "id": "test456",
        "items": ["p", "q"],
        "completed": ["p"],
        "failed": {},
        "status": "running",
        "created_at": 1_234_567_890.0,
        "updated_at": 1_234_567_890.0,
        "metadata": {"name": "test"},
    }
    return jobs._Job.from_dict(data)


def test_job_from_dict_restores_id(deserialized_running_job):
    # Arrange
    job = deserialized_running_job
    # Act
    value = job.id
    # Assert
    assert value == "test456"


def test_job_from_dict_restores_items(deserialized_running_job):
    # Arrange
    job = deserialized_running_job
    # Act
    value = job.items
    # Assert
    assert value == ["p", "q"]


def test_job_from_dict_restores_completed(deserialized_running_job):
    # Arrange
    job = deserialized_running_job
    # Act
    value = job.completed
    # Assert
    assert value == ["p"]


def test_job_from_dict_restores_status_string(deserialized_running_job):
    # Arrange
    job = deserialized_running_job
    # Act
    value = job.status
    # Assert
    assert value == "running"
