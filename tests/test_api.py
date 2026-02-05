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


class TestAPIImports:
    """Test that API functions are properly exported."""

    def test_search_importable(self):
        """Test search function is importable."""
        assert callable(search)

    def test_count_importable(self):
        """Test count function is importable."""
        assert callable(count)

    def test_get_importable(self):
        """Test get function is importable."""
        assert callable(get)

    def test_get_many_importable(self):
        """Test get_many function is importable."""
        assert callable(get_many)

    def test_exists_importable(self):
        """Test exists function is importable."""
        assert callable(exists)

    def test_info_importable(self):
        """Test info function is importable."""
        assert callable(info)

    def test_get_mode_importable(self):
        """Test get_mode function is importable."""
        assert callable(get_mode)

    def test_configure_importable(self):
        """Test configure function is importable."""
        assert callable(configure)


class TestAPIModels:
    """Test API model classes."""

    def test_work_class_exists(self):
        """Test Work class is exported."""
        assert Work is not None

    def test_search_result_class_exists(self):
        """Test SearchResult class is exported."""
        assert SearchResult is not None


class TestGetMode:
    """Test get_mode function."""

    def test_get_mode_returns_string(self, reset_config):
        """Test get_mode returns a valid mode string."""
        mode = get_mode()
        assert mode in ("db", "http")

    def test_default_mode_is_db_when_db_exists(self, reset_config):
        """Test default mode is db when database file exists."""
        import os
        import tempfile

        # Clear env vars
        old_url = os.environ.pop("OPENALEX_LOCAL_API_URL", None)
        old_mode = os.environ.pop("OPENALEX_LOCAL_MODE", None)
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        try:
            os.environ["OPENALEX_LOCAL_DB"] = temp_path
            Config.reset()
            mode = get_mode()
            assert mode == "db"
        finally:
            os.unlink(temp_path)
            os.environ.pop("OPENALEX_LOCAL_DB", None)
            if old_url:
                os.environ["OPENALEX_LOCAL_API_URL"] = old_url
            if old_mode:
                os.environ["OPENALEX_LOCAL_MODE"] = old_mode


class TestSearchResult:
    """Test SearchResult container."""

    def test_search_result_len(self):
        """Test SearchResult length."""
        works = [Work(openalex_id=f"W{i}") for i in range(5)]
        result = SearchResult(works=works, total=100, query="test", elapsed_ms=10.0)
        assert len(result) == 5

    def test_search_result_iter(self):
        """Test SearchResult iteration."""
        works = [Work(openalex_id=f"W{i}") for i in range(3)]
        result = SearchResult(works=works, total=3, query="test", elapsed_ms=5.0)
        assert list(result) == works

    def test_search_result_getitem(self):
        """Test SearchResult indexing."""
        works = [Work(openalex_id=f"W{i}") for i in range(3)]
        result = SearchResult(works=works, total=3, query="test", elapsed_ms=5.0)
        assert result[0].openalex_id == "W0"
        assert result[2].openalex_id == "W2"

    def test_search_result_attributes(self):
        """Test SearchResult attributes."""
        works = [Work(openalex_id="W1")]
        result = SearchResult(
            works=works, total=50, query="machine learning", elapsed_ms=15.5
        )
        assert result.total == 50
        assert result.query == "machine learning"
        assert result.elapsed_ms == 15.5


class TestAPIWithDatabase:
    """Integration tests that require database access."""

    @pytest.fixture(autouse=True)
    def check_db(self, db_available):
        """Skip tests if database is not available."""
        if not db_available:
            pytest.skip("Database not available")

    def test_search_returns_search_result(self, reset_config):
        """Test search returns SearchResult."""
        result = search("machine learning", limit=5)
        assert isinstance(result, SearchResult)
        assert hasattr(result, "works")
        assert hasattr(result, "total")
        assert hasattr(result, "elapsed_ms")

    def test_search_with_limit(self, reset_config):
        """Test search respects limit."""
        result = search("science", limit=3)
        assert len(result.works) <= 3

    def test_search_with_offset(self, reset_config):
        """Test search with offset returns different results."""
        result1 = search("research", limit=5, offset=0)
        result2 = search("research", limit=5, offset=5)
        if result1.total > 5 and len(result1) > 0 and len(result2) > 0:
            # Results should be different if enough matches exist
            assert result1[0].openalex_id != result2[0].openalex_id

    def test_count_returns_int(self, reset_config):
        """Test count returns integer."""
        result = count("machine learning")
        assert isinstance(result, int)
        assert result >= 0

    def test_get_by_openalex_id(self, reset_config, sample_openalex_id):
        """Test get by OpenAlex ID."""
        work = get(sample_openalex_id)
        if work:  # May not exist in all databases
            assert isinstance(work, Work)
            assert work.openalex_id == sample_openalex_id

    def test_get_by_doi(self, reset_config, sample_doi):
        """Test get by DOI."""
        work = get(sample_doi)
        if work:  # May not exist in all databases
            assert isinstance(work, Work)
            assert work.doi == sample_doi

    def test_get_nonexistent_returns_none(self, reset_config):
        """Test get returns None for nonexistent ID."""
        work = get("W99999999999999")
        assert work is None

    def test_get_many_returns_list(self, reset_config, sample_openalex_id):
        """Test get_many returns list."""
        works = get_many([sample_openalex_id, "W99999999999999"])
        assert isinstance(works, list)
        # At least the existing one should be found if in database
        for work in works:
            assert isinstance(work, Work)

    def test_exists_returns_bool(self, reset_config, sample_openalex_id):
        """Test exists returns boolean."""
        result = exists(sample_openalex_id)
        assert isinstance(result, bool)

    def test_exists_false_for_nonexistent(self, reset_config):
        """Test exists returns False for nonexistent ID."""
        result = exists("W99999999999999")
        assert result is False

    def test_info_returns_dict(self, reset_config):
        """Test info returns dictionary."""
        result = info()
        assert isinstance(result, dict)
        assert "status" in result
        assert "mode" in result
        assert result["mode"] == "db"
