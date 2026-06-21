#!/usr/bin/env python3
"""Existence smoke test for examples/08_cli_demo.sh (shell script)."""

from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "08_cli_demo.sh"


def test_cli_demo_script_file_exists():
    """Test the shell demo script is present on disk."""
    # Arrange
    path = EXAMPLE
    # Act
    present = path.is_file()
    # Assert
    assert present, f"missing example: {path}"


def test_cli_demo_script_starts_with_comment():
    """Test the shell demo script opens with a shebang or comment line."""
    # Arrange
    path = EXAMPLE
    # Act
    first_char = path.read_text().lstrip()[:1]
    # Assert
    assert first_char == "#", "expected shell shebang/comment"
