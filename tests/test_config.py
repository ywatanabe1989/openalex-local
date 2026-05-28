"""Tests for openalex_local._core.config module."""

import os
import tempfile
from pathlib import Path

import pytest

from openalex_local._core.config import Config, get_db_path


@pytest.mark.unit
class TestConfig:
    """Test Config class."""

    def setup_method(self):
        """Reset Config before each test."""
        Config.reset()
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

    def test_default_internal_mode_is_auto(self):
        """Test that default internal mode is auto."""
        # Arrange — (setup_method clears env + resets Config)
        # Act — (nothing; reading default)
        # Assert
        assert Config._mode == "auto"

    def test_mode_returns_db_when_db_file_exists(self):
        """Test that mode returns db when database file exists."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        try:
            os.environ["OPENALEX_LOCAL_DB"] = temp_path
            Config.reset()
            # Act
            mode = Config.get_mode()
            # Assert
            assert mode == "db"
        finally:
            os.unlink(temp_path)
            os.environ.pop("OPENALEX_LOCAL_DB", None)

    def test_mode_is_http_when_api_url_env_set(self):
        """Test that mode is http when OPENALEX_LOCAL_API_URL is set."""
        # Arrange
        os.environ["OPENALEX_LOCAL_API_URL"] = "http://localhost:8080"
        # Act
        mode = Config.get_mode()
        # Assert
        assert mode == "http"

    def test_set_api_url_changes_mode_to_http(self):
        """Test that set_api_url changes mode to http."""
        # Arrange — (setup_method)
        # Act
        Config.set_api_url("http://example.com:1234")
        # Assert
        assert Config.get_mode() == "http"

    def test_set_api_url_stores_provided_url(self):
        """Test that set_api_url stores the provided URL."""
        # Arrange — (setup_method)
        # Act
        Config.set_api_url("http://example.com:1234")
        # Assert
        assert Config.get_api_url() == "http://example.com:1234"

    def test_default_api_url_is_localhost(self):
        """Test default API URL."""
        # Arrange — (setup_method)
        # Act
        url = Config.get_api_url()
        # Assert
        assert url == "http://localhost:31292"

    def test_api_url_reads_from_environment(self):
        """Test API URL from environment."""
        # Arrange
        os.environ["OPENALEX_LOCAL_API_URL"] = "http://custom:9999"
        Config.reset()
        # Act
        url = Config.get_api_url()
        # Assert
        assert url == "http://custom:9999"

    def test_set_db_path_with_existing_file_sets_path(self):
        """Test set_db_path with existing file."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        try:
            # Act
            Config.set_db_path(temp_path)
            # Assert
            assert Config.get_db_path() == Path(temp_path)
        finally:
            os.unlink(temp_path)

    def test_set_db_path_with_existing_file_switches_to_db_mode(self):
        """Test set_db_path with existing file switches mode to db."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        try:
            # Act
            Config.set_db_path(temp_path)
            # Assert
            assert Config.get_mode() == "db"
        finally:
            os.unlink(temp_path)

    def test_set_db_path_with_nonexistent_file_raises(self):
        """Test set_db_path with nonexistent file raises FileNotFoundError."""
        # Arrange
        bad_path = "/nonexistent/path/to/db.db"
        # Act
        # Assert
        with pytest.raises(FileNotFoundError):
            Config.set_db_path(bad_path)

    def test_reset_clears_db_path(self):
        """Test that reset clears db_path."""
        # Arrange
        Config.set_api_url("http://test:1234")
        # Act
        Config.reset()
        # Assert
        assert Config._db_path is None

    def test_reset_clears_api_url(self):
        """Test that reset clears api_url."""
        # Arrange
        Config.set_api_url("http://test:1234")
        # Act
        Config.reset()
        # Assert
        assert Config._api_url is None

    def test_reset_restores_auto_mode(self):
        """Test that reset restores auto mode."""
        # Arrange
        Config.set_api_url("http://test:1234")
        # Act
        Config.reset()
        # Assert
        assert Config._mode == "auto"


@pytest.mark.unit
class TestGetDbPath:
    """Test get_db_path function."""

    def setup_method(self):
        """Clear environment before each test."""
        self._original_db = os.environ.pop("OPENALEX_LOCAL_DB", None)

    def teardown_method(self):
        """Restore environment after each test."""
        if self._original_db is not None:
            os.environ["OPENALEX_LOCAL_DB"] = self._original_db

    def test_get_db_path_returns_path_from_env_if_exists(self):
        """Test get_db_path returns path from env if exists."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        try:
            os.environ["OPENALEX_LOCAL_DB"] = temp_path
            # Act
            result = get_db_path()
            # Assert
            assert result == Path(temp_path)
        finally:
            os.unlink(temp_path)

    def test_get_db_path_raises_when_env_path_missing(self):
        """Test get_db_path raises if env path doesn't exist."""
        # Arrange
        os.environ["OPENALEX_LOCAL_DB"] = "/nonexistent/path.db"
        # Act
        # Assert
        with pytest.raises(FileNotFoundError):
            get_db_path()

    def test_get_db_path_error_mentions_env_var_name(self):
        """Test get_db_path error message mentions OPENALEX_LOCAL_DB."""
        # Arrange
        os.environ["OPENALEX_LOCAL_DB"] = "/nonexistent/path.db"
        # Act
        try:
            get_db_path()
            msg = "no error raised"
        except FileNotFoundError as exc:
            msg = str(exc)
        # Assert
        assert "OPENALEX_LOCAL_DB" in msg
