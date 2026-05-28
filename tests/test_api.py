"""Tests for openalex_local API functions."""

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


@pytest.mark.unit
class TestAPIImports:
    """Test that API functions are properly exported."""

    def test_search_function_is_callable(self):
        """Test search function is callable."""
        # Arrange — (nothing; import at module level)
        # Act — (nothing; testing callable attribute)
        # Assert
        assert callable(search)

    def test_count_function_is_callable(self):
        """Test count function is callable."""
        # Arrange — (nothing)
        # Act — (nothing)
        # Assert
        assert callable(count)

    def test_get_function_is_callable(self):
        """Test get function is callable."""
        # Arrange — (nothing)
        # Act — (nothing)
        # Assert
        assert callable(get)

    def test_get_many_function_is_callable(self):
        """Test get_many function is callable."""
        # Arrange — (nothing)
        # Act — (nothing)
        # Assert
        assert callable(get_many)

    def test_exists_function_is_callable(self):
        """Test exists function is callable."""
        # Arrange — (nothing)
        # Act — (nothing)
        # Assert
        assert callable(exists)

    def test_info_function_is_callable(self):
        """Test info function is callable."""
        # Arrange — (nothing)
        # Act — (nothing)
        # Assert
        assert callable(info)

    def test_get_mode_function_is_callable(self):
        """Test get_mode function is callable."""
        # Arrange — (nothing)
        # Act — (nothing)
        # Assert
        assert callable(get_mode)

    def test_configure_function_is_callable(self):
        """Test configure function is callable."""
        # Arrange — (nothing)
        # Act — (nothing)
        # Assert
        assert callable(configure)


@pytest.mark.unit
class TestAPIModels:
    """Test API model classes."""

    def test_work_class_is_exported(self):
        """Test Work class is exported."""
        # Arrange — (nothing)
        # Act — (nothing)
        # Assert
        assert Work is not None

    def test_search_result_class_is_exported(self):
        """Test SearchResult class is exported."""
        # Arrange — (nothing)
        # Act — (nothing)
        # Assert
        assert SearchResult is not None


@pytest.mark.unit
class TestGetMode:
    """Test get_mode function."""

    def test_get_mode_returns_valid_mode_string(self, reset_config):
        """Test get_mode returns a valid mode string."""
        # Arrange — (reset_config fixture)
        # Act
        mode = get_mode()
        # Assert
        assert mode in ("db", "http")

    def test_default_mode_is_db_when_db_exists(self, reset_config):
        """Test default mode is db when database file exists."""
        import os
        import tempfile

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
                os.environ["OPENALEX_LOCAL_API_URL"] == old_url
            if old_mode:
                os.environ["OPENALEX_LOCAL_MODE"] == old_mode


@pytest.mark.unit
class TestSearchResult:
    """Test SearchResult container."""

    @pytest.fixture()
    def five_works(self):
        """Create five Work objects for testing."""
        return [Work(openalex_id=f"W{i}") for i in range(5)]

    @pytest.fixture()
    def three_works(self):
        """Create three Work objects for testing."""
        return [Work(openalex_id=f"W{i}") for i in range(3)]

    def test_search_result_len_returns_work_count(self, five_works):
        """Test SearchResult length matches works count."""
        # Arrange
        result = SearchResult(
            works=five_works, total=100, query="test", elapsed_ms=10.0
        )
        # Act
        length = len(result)
        # Assert
        assert length == 5

    def test_search_result_iter_yields_all_works(self, three_works):
        """Test SearchResult iteration yields all works."""
        # Arrange
        result = SearchResult(works=three_works, total=3, query="test", elapsed_ms=5.0)
        # Act
        items = list(result)
        # Assert
        assert items == three_works

    def test_search_result_index_zero_returns_first_work(self, three_works):
        """Test SearchResult indexing at 0 returns first work."""
        # Arrange
        result = SearchResult(works=three_works, total=3, query="test", elapsed_ms=5.0)
        # Act
        work = result[0]
        # Assert
        assert work.openalex_id == "W0"

    def test_search_result_index_last_returns_last_work(self, three_works):
        """Test SearchResult indexing at end returns last work."""
        # Arrange
        result = SearchResult(works=three_works, total=3, query="test", elapsed_ms=5.0)
        # Act
        work = result[2]
        # Assert
        assert work.openalex_id == "W2"

    def test_search_result_total_matches_provided_value(self):
        """Test SearchResult stores total correctly."""
        # Arrange
        works = [Work(openalex_id="W1")]
        result = SearchResult(
            works=works, total=50, query="machine learning", elapsed_ms=15.5
        )
        # Act
        total = result.total
        # Assert
        assert total == 50

    def test_search_result_query_matches_provided_value(self):
        """Test SearchResult stores query correctly."""
        # Arrange
        works = [Work(openalex_id="W1")]
        result = SearchResult(
            works=works, total=50, query="machine learning", elapsed_ms=15.5
        )
        # Act
        query = result.query
        # Assert
        assert query == "machine learning"

    def test_search_result_elapsed_ms_matches_provided_value(self):
        """Test SearchResult stores elapsed_ms correctly."""
        # Arrange
        works = [Work(openalex_id="W1")]
        result = SearchResult(
            works=works, total=50, query="machine learning", elapsed_ms=15.5
        )
        # Act
        elapsed = result.elapsed_ms
        # Assert
        assert elapsed == 15.5


@pytest.mark.integration
class TestAPIWithDatabase:
    """Integration tests that require database access."""

    @pytest.fixture(autouse=True)
    def check_db(self, db_available):
        """Skip tests if database is not available."""
        if not db_available:
            pytest.skip("Database not available")

    def test_search_returns_search_result_type(self, reset_config):
        """Test search returns SearchResult instance."""
        # Arrange — (reset_config fixture + db_available)
        # Act
        result = search("machine learning", limit=5)
        # Assert
        assert isinstance(result, SearchResult)

    def test_search_result_has_works_attribute(self, reset_config):
        """Test search result contains works attribute."""
        # Arrange
        result = search("machine learning", limit=5)
        # Act
        has_works = hasattr(result, "works")
        # Assert
        assert has_works is True

    def test_search_result_has_total_attribute(self, reset_config):
        """Test search result contains total attribute."""
        # Arrange
        result = search("machine learning", limit=5)
        # Act
        has_total = hasattr(result, "total")
        # Assert
        assert has_total is True

    def test_search_result_has_elapsed_ms_attribute(self, reset_config):
        """Test search result contains elapsed_ms attribute."""
        # Arrange
        result = search("machine learning", limit=5)
        # Act
        has_elapsed = hasattr(result, "elapsed_ms")
        # Assert
        assert has_elapsed is True

    def test_search_with_limit_respects_max_count(self, reset_config):
        """Test search respects limit parameter."""
        # Arrange — (reset_config)
        # Act
        result = search("science", limit=3)
        # Assert
        assert len(result.works) <= 3

    def test_search_with_offset_returns_different_first_result(self, reset_config):
        """Test search with offset returns different results."""
        # Arrange
        result1 = search("research", limit=5, offset=0)
        # Act
        result2 = search("research", limit=5, offset=5)
        # Assert
        if result1.total > 5 and len(result1) > 0 and len(result2) > 0:
            assert result1[0].openalex_id != result2[0].openalex_id

    def test_count_returns_integer_type(self, reset_config):
        """Test count returns integer type."""
        # Arrange
        # Act
        result = count("machine learning")
        # Assert
        assert isinstance(result, int)

    def test_count_returns_non_negative_value(self, reset_config):
        """Test count returns non-negative value."""
        # Arrange
        # Act
        result = count("machine learning")
        # Assert
        assert result >= 0

    def test_get_by_openalex_id_returns_work_or_none(
        self, reset_config, sample_openalex_id
    ):
        """Test get by OpenAlex ID returns Work or None."""
        # Arrange — (fixtures)
        # Act
        work = get(sample_openalex_id)
        # Assert
        if work is not None:
            assert isinstance(work, Work)

    def test_get_by_openalex_id_matches_requested_id(
        self, reset_config, sample_openalex_id
    ):
        """Test get by OpenAlex ID returns matching ID."""
        # Arrange
        work = get(sample_openalex_id)
        # Act
        actual_id = work.openalex_id if work else None
        # Assert
        if actual_id is not None:
            assert actual_id == sample_openalex_id

    def test_get_by_doi_returns_work_or_none(self, reset_config, sample_doi):
        """Test get by DOI returns Work or None."""
        # Arrange — (fixtures)
        # Act
        work = get(sample_doi)
        # Assert
        if work is not None:
            assert isinstance(work, Work)

    def test_get_by_doi_matches_requested_doi(self, reset_config, sample_doi):
        """Test get by DOI returns matching DOI."""
        # Arrange
        work = get(sample_doi)
        # Act
        actual_doi = work.doi if work else None
        # Assert
        if actual_doi is not None:
            assert actual_doi == sample_doi

    def test_get_nonexistent_id_returns_none(self, reset_config):
        """Test get returns None for nonexistent ID."""
        # Arrange — (reset_config)
        # Act
        work = get("W99999999999999")
        # Assert
        assert work is None

    def test_get_many_returns_list_of_works(self, reset_config, sample_openalex_id):
        """Test get_many returns list of Work objects."""
        # Arrange — (fixtures)
        # Act
        works = get_many([sample_openalex_id, "W99999999999999"])
        # Assert
        assert isinstance(works, list)

    def test_get_many_items_are_work_instances(self, reset_config, sample_openalex_id):
        """Test get_many items are all Work instances."""
        # Arrange
        works = get_many([sample_openalex_id, "W99999999999999"])
        # Act
        types = [isinstance(w, Work) for w in works]
        # Assert
        assert all(types)

    def test_exists_returns_boolean_type(self, reset_config, sample_openalex_id):
        """Test exists returns boolean."""
        # Arrange — (fixtures)
        # Act
        result = exists(sample_openalex_id)
        # Assert
        assert isinstance(result, bool)

    def test_exists_false_for_nonexistent_id(self, reset_config):
        """Test exists returns False for nonexistent ID."""
        # Arrange — (reset_config)
        # Act
        result = exists("W99999999999999")
        # Assert
        assert result is False

    def test_info_returns_dictionary(self, reset_config):
        """Test info returns dictionary."""
        # Arrange — (reset_config)
        # Act
        result = info()
        # Assert
        assert isinstance(result, dict)

    def test_info_contains_status_key(self, reset_config):
        """Test info response contains status key."""
        # Arrange
        result = info()
        # Act
        keys = result.keys()
        # Assert
        assert "status" in keys

    def test_info_contains_mode_key(self, reset_config):
        """Test info response contains mode key."""
        # Arrange
        result = info()
        # Act
        keys = result.keys()
        # Assert
        assert "mode" in keys

    def test_info_mode_is_db_when_database_available(self, reset_config):
        """Test info reports db mode when database is available."""
        # Arrange
        result = info()
        # Act
        mode = result["mode"]
        # Assert
        assert mode == "db"
