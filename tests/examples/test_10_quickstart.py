"""Compile-only smoke for examples/10_quickstart.ipynb (PS303)."""

import subprocess
import sys
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "10_quickstart.ipynb"


def test_exists():
    assert EXAMPLE.exists(), f"missing example: {EXAMPLE}"


def test_compiles():
    import json
    nb = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    assert nb.get("nbformat", 0) >= 4, f"unexpected nbformat: {nb.get('nbformat')!r}"
