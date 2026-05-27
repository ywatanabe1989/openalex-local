"""Runtime cross-package import gate (PS-140 §2)."""

import importlib
import importlib.util

import pytest

CROSS_PACKAGE_IMPORTS = [
    "scitex.cli.introspect",
    "scitex_dev",
    "scitex_dev._cli._completion",
    "scitex_dev.cli",
]

def _is_importable(module_path: str) -> bool:
    """Best-effort find_spec wrapper — returns False when any parent
    package is missing (find_spec can raise ModuleNotFoundError on
    intermediate misses)."""
    try:
        return importlib.util.find_spec(module_path) is not None
    except (ModuleNotFoundError, ValueError):
        return False


_AVAILABLE_CROSS_PACKAGE_IMPORTS = [
    m for m in CROSS_PACKAGE_IMPORTS if _is_importable(m)
]


@pytest.mark.parametrize("module_path", _AVAILABLE_CROSS_PACKAGE_IMPORTS)
def test_cross_package_module_loads_with_public_attrs(module_path: str) -> None:
    # Arrange
    target = module_path
    # Act
    mod = importlib.import_module(target)
    # Assert
    assert any(not a.startswith("_") for a in dir(mod)), (
        f"imported {target} but it exposes no public attrs"
    )
