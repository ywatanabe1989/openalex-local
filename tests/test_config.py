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
        """Test that the default internal mode is auto."""
        # Arrange
        Config.reset()
        # Act
        mode = Config._mode
        # Assert
        assert mode == "auto"

    def test_get_mode_returns_db_when_db_file_exists(self):
        """Test that mode returns db when the database file exists."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        os.environ["OPENALEX_LOCAL_DB"] = temp_path
        Config.reset()
        # Act
        try:
            mode = Config.get_mode()
        finally:
            os.unlink(temp_path)
            os.environ.pop("OPENALEX_LOCAL_DB", None)
        # Assert
        assert mode == "db"

    def test_get_mode_returns_http_when_api_url_env_set(self):
        """Test that mode is http when OPENALEX_LOCAL_API_URL is set."""
        # Arrange
        os.environ["OPENALEX_LOCAL_API_URL"] = "http://localhost:8080"
        # Act
        mode = Config.get_mode()
        # Assert
        assert mode == "http"

    def test_set_api_url_changes_mode_to_http(self):
        """Test that set_api_url switches the mode to http."""
        # Arrange
        Config.set_api_url("http://example.com:1234")
        # Act
        mode = Config.get_mode()
        # Assert
        assert mode == "http"

    def test_set_api_url_stores_the_url(self):
        """Test that set_api_url records the supplied URL."""
        # Arrange
        Config.set_api_url("http://example.com:1234")
        # Act
        url = Config.get_api_url()
        # Assert
        assert url == "http://example.com:1234"

    def test_get_api_url_default_is_localhost(self):
        """Test the default API URL points at localhost."""
        # Arrange
        Config.reset()
        # Act
        url = Config.get_api_url()
        # Assert
        assert url == "http://localhost:31292"

    def test_get_api_url_reads_from_env(self):
        """Test the API URL is read from the environment."""
        # Arrange
        os.environ["OPENALEX_LOCAL_API_URL"] = "http://custom:9999"
        Config.reset()
        # Act
        url = Config.get_api_url()
        # Assert
        assert url == "http://custom:9999"

    def test_set_db_path_returns_existing_path(self):
        """Test set_db_path stores a path to an existing file."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        # Act
        try:
            Config.set_db_path(temp_path)
            stored = Config.get_db_path()
        finally:
            os.unlink(temp_path)
        # Assert
        assert stored == Path(temp_path)

    def test_set_db_path_with_existing_file_sets_mode_db(self):
        """Test set_db_path with an existing file switches mode to db."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        # Act
        try:
            Config.set_db_path(temp_path)
            mode = Config.get_mode()
        finally:
            os.unlink(temp_path)
        # Assert
        assert mode == "db"

    def test_set_db_path_with_nonexistent_file_raises(self):
        """Test set_db_path raises FileNotFoundError for a missing file."""
        # Arrange
        missing = "/nonexistent/path/to/db.db"
        # Act
        ctx = pytest.raises(FileNotFoundError)
        # Assert
        with ctx:
            Config.set_db_path(missing)

    def test_reset_clears_db_path(self):
        """Test that reset clears the stored db path."""
        # Arrange
        Config.set_api_url("http://test:1234")
        # Act
        Config.reset()
        # Assert
        assert Config._db_path is None

    def test_reset_clears_api_url(self):
        """Test that reset clears the stored API URL."""
        # Arrange
        Config.set_api_url("http://test:1234")
        # Act
        Config.reset()
        # Assert
        assert Config._api_url is None

    def test_reset_restores_auto_mode(self):
        """Test that reset restores the auto mode."""
        # Arrange
        Config.set_api_url("http://test:1234")
        # Act
        Config.reset()
        # Assert
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

    def test_get_db_path_returns_existing_env_path(self):
        """Test get_db_path returns the env path when it exists."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        os.environ["OPENALEX_LOCAL_DB"] = temp_path
        # Act
        try:
            resolved = get_db_path()
        finally:
            os.unlink(temp_path)
        # Assert
        assert resolved == Path(temp_path)

    def test_get_db_path_raises_when_env_path_missing(self):
        """Test get_db_path raises FileNotFoundError for a missing env path."""
        # Arrange
        os.environ["OPENALEX_LOCAL_DB"] = "/nonexistent/path.db"
        # Act
        ctx = pytest.raises(FileNotFoundError)
        # Assert
        with ctx:
            get_db_path()
