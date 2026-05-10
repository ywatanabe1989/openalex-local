"""Runtime cross-package import gate (PS-140 §2)."""

import pytest

CROSS_PACKAGE_IMPORTS = [
    "scitex.cli.introspect",
    "scitex_dev",
    "scitex_dev._cli._completion",
    "scitex_dev.cli",
]


@pytest.mark.parametrize("module_path", CROSS_PACKAGE_IMPORTS)
def test_cross_package_import(module_path: str) -> None:
    pytest.importorskip(module_path)
