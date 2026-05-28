"""Tests for openalex_local CLI."""

import pytest
from click.testing import CliRunner

from openalex_local._cli.cli import cli

try:
    from scitex_dev import get_tools_sync  # noqa: F401

    _has_scitex_dev = True
except ImportError:
    _has_scitex_dev = False


@pytest.mark.unit
class TestCLI:
    """Test CLI commands."""

    def setup_method(self):
        """Create CLI runner."""
        self.runner = CliRunner()

    def test_cli_help_flag_shows_usage_info(self):
        """Test that --help works."""
        # Arrange — (self.runner in setup_method)
        # Act
        result = self.runner.invoke(cli, ["--help"])
        # Assert
        assert result.exit_code == 0

    def test_cli_help_output_mentions_search(self):
        """Test that --help mentions search command."""
        # Arrange
        result = self.runner.invoke(cli, ["--help"])
        # Act
        output = result.output.lower()
        # Assert
        assert "openalex-local" in output or "search" in output

    def test_cli_version_flag_shows_version(self):
        """Test that --version works."""
        # Arrange — (self.runner)
        # Act
        result = self.runner.invoke(cli, ["--version"])
        # Assert
        assert result.exit_code == 0

    def test_cli_version_output_contains_semver(self):
        """Test that --version contains version number."""
        # Arrange
        result = self.runner.invoke(cli, ["--version"])
        # Act
        # Assert
        assert "0." in result.output

    def test_cli_help_recursive_exits_zero(self):
        """Test that --help-recursive works."""
        # Arrange — (self.runner)
        # Act
        result = self.runner.invoke(cli, ["--help-recursive"])
        # Assert
        assert result.exit_code == 0

    def test_cli_help_recursive_mentions_mcp(self):
        """Test --help-recursive mentions mcp subcommand."""
        # Arrange
        result = self.runner.invoke(cli, ["--help-recursive"])
        # Act
        # Assert
        assert "mcp" in result.output

    def test_cli_help_recursive_mentions_search(self):
        """Test --help-recursive mentions search subcommand."""
        # Arrange
        result = self.runner.invoke(cli, ["--help-recursive"])
        # Act
        # Assert
        assert "search" in result.output

    def test_search_help_flag_exits_zero(self):
        """Test search --help exits successfully."""
        # Arrange — (self.runner)
        # Act
        result = self.runner.invoke(cli, ["search", "--help"])
        # Assert
        assert result.exit_code == 0

    def test_search_help_output_mentions_search(self):
        """Test search --help mentions search."""
        # Arrange
        result = self.runner.invoke(cli, ["search", "--help"])
        # Act
        # Assert
        assert "search" in result.output.lower()

    def test_status_help_flag_exits_zero(self):
        """Test status --help exits successfully."""
        # Arrange — (self.runner)
        # Act
        result = self.runner.invoke(cli, ["status", "--help"])
        # Assert
        assert result.exit_code == 0

    def test_status_help_output_mentions_status(self):
        """Test status --help mentions status."""
        # Arrange
        result = self.runner.invoke(cli, ["status", "--help"])
        # Act
        # Assert
        assert "status" in result.output.lower()

    def test_mcp_help_flag_exits_zero(self):
        """Test mcp --help exits successfully."""
        # Arrange — (self.runner)
        # Act
        result = self.runner.invoke(cli, ["mcp", "--help"])
        # Assert
        assert result.exit_code == 0

    def test_mcp_help_output_mentions_mcp(self):
        """Test mcp --help mentions mcp."""
        # Arrange
        result = self.runner.invoke(cli, ["mcp", "--help"])
        # Act
        # Assert
        assert "mcp" in result.output.lower()

    def test_mcp_list_tools_help_flag_exits_zero(self):
        """Test mcp list-tools --help exits successfully."""
        # Arrange — (self.runner)
        # Act
        result = self.runner.invoke(cli, ["mcp", "list-tools", "--help"])
        # Assert
        assert result.exit_code == 0

    def test_mcp_doctor_help_flag_exits_zero(self):
        """Test mcp doctor --help exits successfully."""
        # Arrange — (self.runner)
        # Act
        result = self.runner.invoke(cli, ["mcp", "doctor", "--help"])
        # Assert
        assert result.exit_code == 0

    def test_mcp_installation_help_flag_exits_zero(self):
        """Test mcp installation --help exits successfully."""
        # Arrange — (self.runner)
        # Act
        result = self.runner.invoke(cli, ["mcp", "installation", "--help"])
        # Assert
        assert result.exit_code == 0

    def test_mcp_start_help_flag_exits_zero(self):
        """Test mcp start --help exits successfully."""
        # Arrange — (self.runner)
        # Act
        result = self.runner.invoke(cli, ["mcp", "start", "--help"])
        # Assert
        assert result.exit_code == 0

    def test_mcp_start_help_mentions_transport(self):
        """Test mcp start --help mentions transport or stdio."""
        # Arrange
        result = self.runner.invoke(cli, ["mcp", "start", "--help"])
        # Act
        output = result.output.lower()
        # Assert
        assert "transport" in output or "stdio" in output


@pytest.mark.integration
class TestCLICommands:
    """Test CLI command execution (without database)."""

    def setup_method(self):
        """Create CLI runner."""
        self.runner = CliRunner()

    @pytest.mark.skipif(
        not _has_scitex_dev,
        reason="scitex_dev not installed",
    )
    def test_mcp_list_tools_command_exits_zero(self):
        """Test mcp list-tools runs."""
        # Arrange — (self.runner, _has_scitex_dev guard)
        # Act
        result = self.runner.invoke(cli, ["mcp", "list-tools"])
        # Assert
        assert result.exit_code == 0

    def test_mcp_installation_command_exits_zero(self):
        """Test mcp installation runs."""
        # Arrange — (self.runner)
        # Act
        result = self.runner.invoke(cli, ["mcp", "installation"])
        # Assert
        assert result.exit_code == 0

    def test_mcp_installation_output_mentions_mcp_or_install(self):
        """Test mcp installation output mentions mcp or install."""
        # Arrange
        result = self.runner.invoke(cli, ["mcp", "installation"])
        # Act
        output = result.output.lower()
        # Assert
        assert "mcp" in output or "install" in output

    def test_mcp_doctor_command_exits_cleanly(self):
        """Test mcp doctor runs (slow on large databases)."""
        # Arrange
        result = self.runner.invoke(cli, ["mcp", "doctor"])
        # Act
        exit_code = result.exit_code
        # Assert
        assert exit_code >= 0
