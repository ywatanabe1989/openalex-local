"""Tests for openalex_local._core.config module."""

import os
import tempfile
from pathlib import Path

import pytest

from openalex_local._core.config import Config, get_db_path


_CONFIG_ENV_KEYS = (
    "OPENALEX_LOCAL_DB",
    "OPENALEX_LOCAL_API_URL",
    "OPENALEX_LOCAL_MODE",
)


@pytest.fixture
def isolated_config_env():
    """Reset Config state and clear OpenAlex env vars for the test.

    Yields nothing; restores the original env on teardown.
    """
    Config.reset()
    saved = {key: os.environ.pop(key, None) for key in _CONFIG_ENV_KEYS}
    try:
        yield
    finally:
        Config.reset()
        for key, value in saved.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)


@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        yield path
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


# ---------------------------------------------------------------------------
# Config class state machine
# ---------------------------------------------------------------------------

def test_config_default_internal_mode_is_auto(isolated_config_env):
    # Arrange
    expected = "auto"
    # Act
    value = Config._mode
    # Assert
    assert value == expected


def test_config_mode_becomes_db_when_env_points_at_real_file(
    isolated_config_env, temp_db_path
):
    # Arrange
    os.environ["OPENALEX_LOCAL_DB"] = temp_db_path
    Config.reset()
    # Act
    mode = Config.get_mode()
    # Assert
    assert mode == "db"


def test_config_mode_becomes_http_when_api_url_env_set(isolated_config_env):
    # Arrange
    os.environ["OPENALEX_LOCAL_API_URL"] = "http://localhost:8080"
    # Act
    mode = Config.get_mode()
    # Assert
    assert mode == "http"


def test_config_set_api_url_switches_mode_to_http(isolated_config_env):
    # Arrange
    Config.set_api_url("http://example.com:1234")
    # Act
    mode = Config.get_mode()
    # Assert
    assert mode == "http"


def test_config_set_api_url_persists_url_for_get_api_url(isolated_config_env):
    # Arrange
    Config.set_api_url("http://example.com:1234")
    # Act
    url = Config.get_api_url()
    # Assert
    assert url == "http://example.com:1234"


def test_config_get_api_url_default_is_localhost_31292(isolated_config_env):
    # Arrange
    expected = "http://localhost:31292"
    # Act
    url = Config.get_api_url()
    # Assert
    assert url == expected


def test_config_get_api_url_reads_from_openalex_local_api_url_env(
    isolated_config_env,
):
    # Arrange
    os.environ["OPENALEX_LOCAL_API_URL"] = "http://custom:9999"
    Config.reset()
    # Act
    url = Config.get_api_url()
    # Assert
    assert url == "http://custom:9999"


def test_config_set_db_path_with_existing_file_records_path(
    isolated_config_env, temp_db_path
):
    # Arrange
    Config.set_db_path(temp_db_path)
    # Act
    stored = Config.get_db_path()
    # Assert
    assert stored == Path(temp_db_path)


def test_config_set_db_path_with_existing_file_sets_mode_to_db(
    isolated_config_env, temp_db_path
):
    # Arrange
    Config.set_db_path(temp_db_path)
    # Act
    mode = Config.get_mode()
    # Assert
    assert mode == "db"


def test_config_set_db_path_raises_for_nonexistent_file(isolated_config_env):
    # Arrange
    bogus = "/nonexistent/path/to/db.db"
    # Act
    ctx = pytest.raises(FileNotFoundError)
    # Assert
    with ctx:
        Config.set_db_path(bogus)


def test_config_reset_clears_db_path(isolated_config_env):
    # Arrange
    Config.set_api_url("http://test:1234")
    # Act
    Config.reset()
    # Assert
    assert Config._db_path is None


def test_config_reset_clears_api_url(isolated_config_env):
    # Arrange
    Config.set_api_url("http://test:1234")
    # Act
    Config.reset()
    # Assert
    assert Config._api_url is None


def test_config_reset_returns_internal_mode_to_auto(isolated_config_env):
    # Arrange
    Config.set_api_url("http://test:1234")
    # Act
    Config.reset()
    # Assert
    assert Config._mode == "auto"


# ---------------------------------------------------------------------------
# get_db_path() helper — env-driven path resolution
# ---------------------------------------------------------------------------

@pytest.fixture
def isolated_db_env():
    saved = os.environ.pop("OPENALEX_LOCAL_DB", None)
    try:
        yield
    finally:
        if saved is not None:
            os.environ["OPENALEX_LOCAL_DB"] = saved
        else:
            os.environ.pop("OPENALEX_LOCAL_DB", None)


def test_get_db_path_returns_env_path_when_file_exists(
    isolated_db_env, temp_db_path
):
    # Arrange
    os.environ["OPENALEX_LOCAL_DB"] = temp_db_path
    # Act
    path = get_db_path()
    # Assert
    assert path == Path(temp_db_path)


def test_get_db_path_raises_when_env_path_does_not_exist(isolated_db_env):
    # Arrange
    os.environ["OPENALEX_LOCAL_DB"] = "/nonexistent/path.db"
    # Act
    ctx = pytest.raises(FileNotFoundError, match="OPENALEX_LOCAL_DB")
    # Assert
    with ctx:
        get_db_path()
