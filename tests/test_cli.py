"""Tests for openalex_local CLI."""

import pytest
from click.testing import CliRunner

from openalex_local._cli.cli import cli

try:
    from scitex_dev import get_tools_sync  # noqa: F401

    _has_scitex_dev = True
except ImportError:
    _has_scitex_dev = False


@pytest.fixture
def runner():
    """Return a Click CLI runner."""
    return CliRunner()


class TestCLIHelp:
    """Test CLI --help output for each command."""

    def test_root_help_exits_zero(self, runner):
        """Test the root --help exits with status zero."""
        # Arrange
        args = ["--help"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert result.exit_code == 0

    def test_root_help_mentions_a_command(self, runner):
        """Test the root --help lists at least the search command."""
        # Arrange
        args = ["--help"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert "search" in result.output

    def test_version_exits_zero(self, runner):
        """Test --version exits with status zero."""
        # Arrange
        args = ["--version"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert result.exit_code == 0

    def test_version_prints_zero_dot_series(self, runner):
        """Test --version prints a 0.x version string."""
        # Arrange
        args = ["--version"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert "0." in result.output

    def test_help_recursive_exits_zero(self, runner):
        """Test --help-recursive exits with status zero."""
        # Arrange
        args = ["--help-recursive"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert result.exit_code == 0

    def test_help_recursive_lists_mcp_command(self, runner):
        """Test --help-recursive surfaces the nested mcp command."""
        # Arrange
        args = ["--help-recursive"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert "mcp" in result.output

    def test_search_help_exits_zero(self, runner):
        """Test search --help exits with status zero."""
        # Arrange
        args = ["search", "--help"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert result.exit_code == 0

    def test_status_help_exits_zero(self, runner):
        """Test status --help exits with status zero."""
        # Arrange
        args = ["status", "--help"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert result.exit_code == 0

    def test_mcp_help_exits_zero(self, runner):
        """Test mcp --help exits with status zero."""
        # Arrange
        args = ["mcp", "--help"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert result.exit_code == 0

    def test_mcp_list_tools_help_exits_zero(self, runner):
        """Test mcp list-tools --help exits with status zero."""
        # Arrange
        args = ["mcp", "list-tools", "--help"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert result.exit_code == 0

    def test_mcp_doctor_help_exits_zero(self, runner):
        """Test mcp doctor --help exits with status zero."""
        # Arrange
        args = ["mcp", "doctor", "--help"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert result.exit_code == 0

    def test_mcp_installation_help_exits_zero(self, runner):
        """Test mcp installation --help exits with status zero."""
        # Arrange
        args = ["mcp", "installation", "--help"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert result.exit_code == 0

    def test_mcp_start_help_exits_zero(self, runner):
        """Test mcp start --help exits with status zero."""
        # Arrange
        args = ["mcp", "start", "--help"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert result.exit_code == 0


class TestCLICommands:
    """Test CLI command execution (without database)."""

    @pytest.mark.skipif(
        not _has_scitex_dev,
        reason="scitex_dev not installed",
    )
    def test_mcp_list_tools_runs_clean(self, runner):
        """Test mcp list-tools runs and exits with status zero."""
        # Arrange
        args = ["mcp", "list-tools"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert result.exit_code == 0

    def test_mcp_installation_exits_zero(self, runner):
        """Test mcp installation runs and exits with status zero."""
        # Arrange
        args = ["mcp", "installation"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert result.exit_code == 0

    def test_mcp_installation_mentions_mcp(self, runner):
        """Test mcp installation output references mcp setup."""
        # Arrange
        args = ["mcp", "installation"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert "mcp" in result.output.lower() or "install" in result.output.lower()

    def test_mcp_doctor_does_not_crash(self, runner):
        """Test mcp doctor runs to a clean exit code without crashing."""
        # Arrange
        args = ["mcp", "doctor"]
        # Act
        result = runner.invoke(cli, args)
        # Assert
        assert result.exit_code in (0, 1)
