"""Notebook smoke for examples/10_quickstart.ipynb (PS-303 / PS-505).

Uses `jupyter nbconvert --execute` so cells actually run; runpy /
subprocess `python …` does NOT execute .ipynb cells.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "10_quickstart.ipynb"


@pytest.fixture
def executable_notebook():
    """Yield the notebook path once nbconvert and the DB are available.

    Skips the requesting test when nbconvert/nbclient are missing or the
    local OpenAlex DB is absent — the notebook demonstrates DB-backed
    search and would error out otherwise.
    """
    pytest.importorskip("nbconvert")
    pytest.importorskip("nbclient")
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            "import os; from openalex_local._core.config import Config; "
            "print(int(os.path.exists(Config().db_path)))",
        ],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0 or probe.stdout.strip() != "1":
        pytest.skip("OpenAlex local DB not present; nbconvert run would fail")
    yield EXAMPLE


def test_notebook_file_exists():
    """Test the quickstart notebook is present on disk."""
    # Arrange
    path = EXAMPLE
    # Act
    present = path.exists()
    # Assert
    assert present, f"missing example: {path}"


def test_notebook_uses_supported_nbformat():
    """Test the notebook declares a supported nbformat version."""
    # Arrange
    raw = EXAMPLE.read_text(encoding="utf-8")
    # Act
    nb = json.loads(raw)
    # Assert
    assert nb.get("nbformat", 0) >= 4, f"unexpected nbformat: {nb.get('nbformat')!r}"


def test_notebook_executes_end_to_end(executable_notebook):
    """Test the notebook runs to completion under nbconvert."""
    # Arrange
    cmd = [
        sys.executable,
        "-m",
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        "--output",
        "/tmp/_nbconvert_out.ipynb",
        str(executable_notebook),
    ]
    # Act
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    # Assert
    assert res.returncode == 0, f"nbconvert failed:\n{res.stderr}"
