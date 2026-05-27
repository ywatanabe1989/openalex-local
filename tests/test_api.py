"""Tests for openalex_local API functions."""

import os
import tempfile

import pytest

from openalex_local import (
    Work,
    SearchResult,
    search,
    count,
    get,
    get_many,
    exists,
    info,
    get_mode,
    configure,
)
from openalex_local._core.config import Config


# ---------------------------------------------------------------------------
# Public API surface — callable / exported
# ---------------------------------------------------------------------------

def test_search_function_is_callable_via_top_level_import():
    # Arrange
    target = search
    # Act
    callable_now = callable(target)
    # Assert
    assert callable_now


def test_count_function_is_callable_via_top_level_import():
    # Arrange
    target = count
    # Act
    callable_now = callable(target)
    # Assert
    assert callable_now


def test_get_function_is_callable_via_top_level_import():
    # Arrange
    target = get
    # Act
    callable_now = callable(target)
    # Assert
    assert callable_now


def test_get_many_function_is_callable_via_top_level_import():
    # Arrange
    target = get_many
    # Act
    callable_now = callable(target)
    # Assert
    assert callable_now


def test_exists_function_is_callable_via_top_level_import():
    # Arrange
    target = exists
    # Act
    callable_now = callable(target)
    # Assert
    assert callable_now


def test_info_function_is_callable_via_top_level_import():
    # Arrange
    target = info
    # Act
    callable_now = callable(target)
    # Assert
    assert callable_now


def test_get_mode_function_is_callable_via_top_level_import():
    # Arrange
    target = get_mode
    # Act
    callable_now = callable(target)
    # Assert
    assert callable_now


def test_configure_function_is_callable_via_top_level_import():
    # Arrange
    target = configure
    # Act
    callable_now = callable(target)
    # Assert
    assert callable_now


def test_work_class_is_exported_from_top_level():
    # Arrange
    target = Work
    # Act
    not_none = target is not None
    # Assert
    assert not_none


def test_search_result_class_is_exported_from_top_level():
    # Arrange
    target = SearchResult
    # Act
    not_none = target is not None
    # Assert
    assert not_none


# ---------------------------------------------------------------------------
# get_mode() — depends on env / config
# ---------------------------------------------------------------------------

def test_get_mode_returns_one_of_db_or_http(reset_config):
    # Arrange
    valid_modes = {"db", "http"}
    # Act
    mode = get_mode()
    # Assert
    assert mode in valid_modes


def test_get_mode_returns_db_when_openalex_local_db_env_points_at_real_file(
    reset_config,
):
    # Arrange
    old_url = os.environ.pop("OPENALEX_LOCAL_API_URL", None)
    old_mode = os.environ.pop("OPENALEX_LOCAL_MODE", None)
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    try:
        os.environ["OPENALEX_LOCAL_DB"] = temp_path
        Config.reset()
        # Act
        mode = get_mode()
        # Assert
        assert mode == "db"
    finally:
        os.unlink(temp_path)
        os.environ.pop("OPENALEX_LOCAL_DB", None)
        if old_url:
            os.environ["OPENALEX_LOCAL_API_URL"] = old_url
        if old_mode:
            os.environ["OPENALEX_LOCAL_MODE"] = old_mode


# ---------------------------------------------------------------------------
# SearchResult — container API
# ---------------------------------------------------------------------------

@pytest.fixture
def five_work_search_result():
    works = [Work(openalex_id=f"W{i}") for i in range(5)]
    return SearchResult(works=works, total=100, query="test", elapsed_ms=10.0)


def test_search_result_len_reports_number_of_works(five_work_search_result):
    # Arrange
    result = five_work_search_result
    # Act
    length = len(result)
    # Assert
    assert length == 5


def test_search_result_iter_yields_underlying_works():
    # Arrange
    works = [Work(openalex_id=f"W{i}") for i in range(3)]
    result = SearchResult(works=works, total=3, query="test", elapsed_ms=5.0)
    # Act
    items = list(result)
    # Assert
    assert items == works


def test_search_result_getitem_returns_first_work():
    # Arrange
    works = [Work(openalex_id=f"W{i}") for i in range(3)]
    result = SearchResult(works=works, total=3, query="test", elapsed_ms=5.0)
    # Act
    first = result[0]
    # Assert
    assert first.openalex_id == "W0"


def test_search_result_getitem_returns_third_work():
    # Arrange
    works = [Work(openalex_id=f"W{i}") for i in range(3)]
    result = SearchResult(works=works, total=3, query="test", elapsed_ms=5.0)
    # Act
    third = result[2]
    # Assert
    assert third.openalex_id == "W2"


@pytest.fixture
def search_result_with_metadata():
    works = [Work(openalex_id="W1")]
    return SearchResult(
        works=works,
        total=50,
        query="machine learning",
        elapsed_ms=15.5,
    )


def test_search_result_exposes_total_attribute(search_result_with_metadata):
    # Arrange
    result = search_result_with_metadata
    # Act
    value = result.total
    # Assert
    assert value == 50


def test_search_result_exposes_query_attribute(search_result_with_metadata):
    # Arrange
    result = search_result_with_metadata
    # Act
    value = result.query
    # Assert
    assert value == "machine learning"


def test_search_result_exposes_elapsed_ms_attribute(search_result_with_metadata):
    # Arrange
    result = search_result_with_metadata
    # Act
    value = result.elapsed_ms
    # Assert
    assert value == 15.5


# ---------------------------------------------------------------------------
# DB-backed integration — skipped when no local DB available
# ---------------------------------------------------------------------------

@pytest.fixture
def _require_db(db_available):
    if not db_available:
        pytest.skip("Database not available")


def test_search_returns_search_result_instance(_require_db, reset_config):
    # Arrange
    query = "machine learning"
    # Act
    result = search(query, limit=5)
    # Assert
    assert isinstance(result, SearchResult)


def test_search_result_carries_works_attribute(_require_db, reset_config):
    # Arrange
    query = "machine learning"
    # Act
    result = search(query, limit=5)
    # Assert
    assert hasattr(result, "works")


def test_search_result_carries_total_attribute(_require_db, reset_config):
    # Arrange
    query = "machine learning"
    # Act
    result = search(query, limit=5)
    # Assert
    assert hasattr(result, "total")


def test_search_result_carries_elapsed_ms_attribute(_require_db, reset_config):
    # Arrange
    query = "machine learning"
    # Act
    result = search(query, limit=5)
    # Assert
    assert hasattr(result, "elapsed_ms")


def test_search_respects_limit_parameter_upper_bound(_require_db, reset_config):
    # Arrange
    limit = 3
    # Act
    result = search("science", limit=limit)
    # Assert
    assert len(result.works) <= limit


def test_count_returns_non_negative_integer(_require_db, reset_config):
    # Arrange
    query = "machine learning"
    # Act
    result = count(query)
    # Assert
    assert isinstance(result, int) and result >= 0


def test_get_returns_none_for_unknown_openalex_id(_require_db, reset_config):
    # Arrange
    unknown_id = "W99999999999999"
    # Act
    work = get(unknown_id)
    # Assert
    assert work is None


def test_get_many_returns_list_of_work_instances(
    _require_db, reset_config, sample_openalex_id
):
    # Arrange
    ids = [sample_openalex_id, "W99999999999999"]
    # Act
    works = get_many(ids)
    # Assert
    assert isinstance(works, list)


def test_exists_returns_boolean_for_real_lookup(
    _require_db, reset_config, sample_openalex_id
):
    # Arrange
    target = sample_openalex_id
    # Act
    present = exists(target)
    # Assert
    assert isinstance(present, bool)


def test_exists_returns_false_for_unknown_openalex_id(_require_db, reset_config):
    # Arrange
    unknown_id = "W99999999999999"
    # Act
    present = exists(unknown_id)
    # Assert
    assert present is False


def test_info_returns_dict_with_mode_db_when_db_backed(_require_db, reset_config):
    # Arrange
    expected_mode = "db"
    # Act
    payload = info()
    # Assert
    assert payload.get("mode") == expected_mode
