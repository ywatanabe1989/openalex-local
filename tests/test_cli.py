"""Tests for openalex_local CLI."""

import importlib.util

import pytest
from click.testing import CliRunner

from openalex_local._cli.cli import cli

_HAS_SCITEX_DEV = importlib.util.find_spec("scitex_dev") is not None


@pytest.fixture
def cli_runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# Top-level CLI shape
# ---------------------------------------------------------------------------

def test_cli_help_exits_zero_for_root_command(cli_runner):
    # Arrange
    args = ["--help"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_help_output_mentions_openalex_or_search(cli_runner):
    # Arrange
    args = ["--help"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert "openalex-local" in result.output.lower() or "search" in result.output


def test_cli_version_flag_exits_zero(cli_runner):
    # Arrange
    args = ["--version"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_version_flag_prints_zero_dot_prefix(cli_runner):
    # Arrange
    args = ["--version"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert "0." in result.output


def test_cli_help_recursive_flag_exits_zero(cli_runner):
    # Arrange
    args = ["--help-recursive"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_help_recursive_output_mentions_mcp(cli_runner):
    # Arrange
    args = ["--help-recursive"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert "mcp" in result.output


def test_cli_help_recursive_output_mentions_search(cli_runner):
    # Arrange
    args = ["--help-recursive"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert "search" in result.output


# ---------------------------------------------------------------------------
# Per-subcommand --help
# ---------------------------------------------------------------------------

def test_search_help_subcommand_exits_zero(cli_runner):
    # Arrange
    args = ["search", "--help"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_search_help_subcommand_mentions_search(cli_runner):
    # Arrange
    args = ["search", "--help"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert "search" in result.output.lower()


def test_status_help_subcommand_exits_zero(cli_runner):
    # Arrange
    args = ["status", "--help"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_status_help_subcommand_mentions_status(cli_runner):
    # Arrange
    args = ["status", "--help"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert "status" in result.output.lower()


def test_mcp_help_subcommand_exits_zero(cli_runner):
    # Arrange
    args = ["mcp", "--help"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_mcp_help_subcommand_mentions_mcp(cli_runner):
    # Arrange
    args = ["mcp", "--help"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert "mcp" in result.output.lower()


def test_mcp_list_tools_help_exits_zero(cli_runner):
    # Arrange
    args = ["mcp", "list-tools", "--help"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_mcp_doctor_help_exits_zero(cli_runner):
    # Arrange
    args = ["mcp", "doctor", "--help"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_mcp_installation_help_exits_zero(cli_runner):
    # Arrange
    args = ["mcp", "installation", "--help"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_mcp_start_help_exits_zero(cli_runner):
    # Arrange
    args = ["mcp", "start", "--help"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_mcp_start_help_mentions_transport_or_stdio(cli_runner):
    # Arrange
    args = ["mcp", "start", "--help"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert "transport" in result.output.lower() or "stdio" in result.output


# ---------------------------------------------------------------------------
# CLI command execution (no DB needed)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _HAS_SCITEX_DEV,
    reason="scitex_dev not installed",
)
def test_mcp_list_tools_command_exits_zero(cli_runner):
    # Arrange
    args = ["mcp", "list-tools"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_mcp_installation_command_exits_zero(cli_runner):
    # Arrange
    args = ["mcp", "installation"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_mcp_installation_command_mentions_mcp_or_install(cli_runner):
    # Arrange
    args = ["mcp", "installation"]
    # Act
    result = cli_runner.invoke(cli, args)
    # Assert
    assert "mcp" in result.output.lower() or "install" in result.output.lower()


# Note: a `mcp doctor` smoke test would naturally live here, but it is
# skipped permanently on large databases (459M+ rows) — COUNT(*) times
# out — so the test was removed during the TQ migration. Re-introduce
# as a real integration test once it has a non-trivial assertion.
