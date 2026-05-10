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


def test_exists():
    assert EXAMPLE.exists(), f"missing example: {EXAMPLE}"


def test_compiles():
    nb = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    assert nb.get("nbformat", 0) >= 4, f"unexpected nbformat: {nb.get('nbformat')!r}"


def test_executes():
    """Run the notebook end-to-end via nbconvert. Skip if jupyter or DB unavailable."""
    pytest.importorskip("nbconvert")
    pytest.importorskip("nbclient")
    # Skip when the local OpenAlex DB isn't present — the notebook
    # demonstrates DB-backed search and would error out otherwise.
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

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "--output",
            "/tmp/_nbconvert_out.ipynb",
            str(EXAMPLE),
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert res.returncode == 0, f"nbconvert failed:\n{res.stderr}"
