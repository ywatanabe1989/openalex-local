#!/usr/bin/env python3
"""Existence smoke test for examples/08_cli_demo.sh (shell script)."""

from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "08_cli_demo.sh"


def test_example_exists():
    assert EXAMPLE.is_file(), f"missing example: {EXAMPLE}"
    assert EXAMPLE.read_text().lstrip().startswith("#"), (
        "expected shell shebang/comment"
    )


if __name__ == "__main__":
    test_example_exists()
