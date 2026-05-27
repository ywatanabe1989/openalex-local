#!/usr/bin/env python3
"""Existence smoke test for examples/08_cli_demo.sh (shell script)."""

from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "08_cli_demo.sh"


def test_cli_demo_script_file_exists():
    # Arrange
    path = EXAMPLE
    # Act
    found = path.is_file()
    # Assert
    assert found, f"missing example: {path}"


def test_cli_demo_script_starts_with_comment_or_shebang():
    # Arrange
    contents = EXAMPLE.read_text()
    # Act
    first_char = contents.lstrip()[:1]
    # Assert
    assert first_char == "#", "expected shell shebang/comment"
