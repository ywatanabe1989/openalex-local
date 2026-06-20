"""Compile-only smoke for examples/11_abstract_coverage.py (PS303)."""

import subprocess
import sys
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "11_abstract_coverage.py"


def test_example_script_file_exists():
    """Test the example script is present on disk."""
    # Arrange
    path = EXAMPLE
    # Act
    present = path.exists()
    # Assert
    assert present, f"missing example: {path}"


def test_example_script_compiles_cleanly():
    """Test the example script compiles without a syntax error."""
    # Arrange
    cmd = [sys.executable, "-m", "py_compile", str(EXAMPLE)]
    # Act
    result = subprocess.run(cmd, capture_output=True, text=True)
    # Assert
    assert result.returncode == 0, result.stderr
