"""Compile-only smoke for examples/11_abstract_coverage.py (PS-303)."""

import subprocess
import sys
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "11_abstract_coverage.py"


def test_example_file_exists_on_disk():
    # Arrange
    path = EXAMPLE
    # Act
    found = path.exists()
    # Assert
    assert found, f"missing example: {path}"


def test_example_byte_compiles_under_py_compile():
    # Arrange
    cmd = [sys.executable, "-m", "py_compile", str(EXAMPLE)]
    # Act
    result = subprocess.run(cmd, capture_output=True, text=True)
    # Assert
    assert result.returncode == 0, f"py_compile failed: {result.stderr}"
