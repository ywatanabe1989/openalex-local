"""Tests for openalex_local._core.config module."""

import os
import tempfile
from pathlib import Path

import pytest

from openalex_local._core.config import Config, get_db_path


class TestConfig:
    """Test Config class."""

    def setup_method(self):
        """Reset Config before each test."""
        Config.reset()
        # Clear environment variables
        self._original_env = {}
        for key in [
            "OPENALEX_LOCAL_DB",
            "OPENALEX_LOCAL_API_URL",
            "OPENALEX_LOCAL_MODE",
        ]:
            self._original_env[key] = os.environ.pop(key, None)

    def teardown_method(self):
        """Restore environment after each test."""
        Config.reset()
        for key, value in self._original_env.items():
            if value is not None:
                os.environ[key] = value

    def test_get_mode_default_is_auto(self):
        """Test that default internal mode is auto."""
        assert Config._mode == "auto"

    def test_get_mode_returns_db_when_db_exists(self):
        """Test that mode returns db when database file exists."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        try:
            os.environ["OPENALEX_LOCAL_DB"] = temp_path
            Config.reset()
            assert Config.get_mode() == "db"
        finally:
            os.unlink(temp_path)
            os.environ.pop("OPENALEX_LOCAL_DB", None)

    def test_get_mode_http_when_api_url_env_set(self):
        """Test that mode is http when OPENALEX_LOCAL_API_URL is set."""
        os.environ["OPENALEX_LOCAL_API_URL"] = "http://localhost:8080"
        assert Config.get_mode() == "http"

    def test_set_api_url_changes_mode_to_http(self):
        """Test that set_api_url changes mode to http."""
        Config.set_api_url("http://example.com:1234")
        assert Config.get_mode() == "http"
        assert Config.get_api_url() == "http://example.com:1234"

    def test_get_api_url_default(self):
        """Test default API URL."""
        assert Config.get_api_url() == "http://localhost:31292"

    def test_get_api_url_from_env(self):
        """Test API URL from environment."""
        os.environ["OPENALEX_LOCAL_API_URL"] = "http://custom:9999"
        Config.reset()
        assert Config.get_api_url() == "http://custom:9999"

    def test_set_db_path_with_existing_file(self):
        """Test set_db_path with existing file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        try:
            Config.set_db_path(temp_path)
            assert Config.get_db_path() == Path(temp_path)
            assert Config.get_mode() == "db"
        finally:
            os.unlink(temp_path)

    def test_set_db_path_with_nonexistent_file_raises(self):
        """Test set_db_path with nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Config.set_db_path("/nonexistent/path/to/db.db")

    def test_reset_clears_all_settings(self):
        """Test that reset clears all settings."""
        Config.set_api_url("http://test:1234")
        Config.reset()
        assert Config._db_path is None
        assert Config._api_url is None
        assert Config._mode == "auto"


class TestGetDbPath:
    """Test get_db_path function."""

    def setup_method(self):
        """Clear environment before each test."""
        self._original_db = os.environ.pop("OPENALEX_LOCAL_DB", None)

    def teardown_method(self):
        """Restore environment after each test."""
        if self._original_db is not None:
            os.environ["OPENALEX_LOCAL_DB"] = self._original_db

    def test_get_db_path_from_env_existing(self):
        """Test get_db_path returns path from env if exists."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        try:
            os.environ["OPENALEX_LOCAL_DB"] = temp_path
            assert get_db_path() == Path(temp_path)
        finally:
            os.unlink(temp_path)

    def test_get_db_path_from_env_nonexistent_raises(self):
        """Test get_db_path raises if env path doesn't exist."""
        os.environ["OPENALEX_LOCAL_DB"] = "/nonexistent/path.db"
        with pytest.raises(FileNotFoundError) as exc_info:
            get_db_path()
        assert "OPENALEX_LOCAL_DB" in str(exc_info.value)
