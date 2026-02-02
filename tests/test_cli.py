"""Tests for openalex_local CLI."""

import pytest
from click.testing import CliRunner

from openalex_local._cli.cli import cli


class TestCLI:
    """Test CLI commands."""

    def setup_method(self):
        """Create CLI runner."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test that --help works."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "openalex-local" in result.output.lower() or "search" in result.output

    def test_cli_version(self):
        """Test that --version works."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0." in result.output  # Version starts with 0.x.x

    def test_cli_help_recursive(self):
        """Test that --help-recursive works."""
        result = self.runner.invoke(cli, ["--help-recursive"])
        assert result.exit_code == 0
        assert "mcp" in result.output
        assert "search" in result.output

    def test_search_help(self):
        """Test search --help."""
        result = self.runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "search" in result.output.lower()

    def test_status_help(self):
        """Test status --help."""
        result = self.runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0
        assert "status" in result.output.lower()

    def test_mcp_help(self):
        """Test mcp --help."""
        result = self.runner.invoke(cli, ["mcp", "--help"])
        assert result.exit_code == 0
        assert "mcp" in result.output.lower()

    def test_mcp_list_tools_help(self):
        """Test mcp list-tools --help."""
        result = self.runner.invoke(cli, ["mcp", "list-tools", "--help"])
        assert result.exit_code == 0

    def test_mcp_doctor_help(self):
        """Test mcp doctor --help."""
        result = self.runner.invoke(cli, ["mcp", "doctor", "--help"])
        assert result.exit_code == 0

    def test_mcp_installation_help(self):
        """Test mcp installation --help."""
        result = self.runner.invoke(cli, ["mcp", "installation", "--help"])
        assert result.exit_code == 0

    def test_mcp_start_help(self):
        """Test mcp start --help."""
        result = self.runner.invoke(cli, ["mcp", "start", "--help"])
        assert result.exit_code == 0
        assert "transport" in result.output.lower() or "stdio" in result.output


class TestCLICommands:
    """Test CLI command execution (without database)."""

    def setup_method(self):
        """Create CLI runner."""
        self.runner = CliRunner()

    def test_mcp_list_tools(self):
        """Test mcp list-tools runs."""
        result = self.runner.invoke(cli, ["mcp", "list-tools"])
        # Should run without error (may have no tools or list tools)
        assert result.exit_code == 0

    def test_mcp_installation(self):
        """Test mcp installation runs."""
        result = self.runner.invoke(cli, ["mcp", "installation"])
        assert result.exit_code == 0
        assert "mcp" in result.output.lower() or "install" in result.output.lower()

    @pytest.mark.skip(reason="Slow on large databases (459M+ rows) - COUNT(*) times out")
    def test_mcp_doctor(self):
        """Test mcp doctor runs."""
        result = self.runner.invoke(cli, ["mcp", "doctor"])
        # May pass or fail depending on setup, but should not crash
        assert result.exit_code in [0, 1]
