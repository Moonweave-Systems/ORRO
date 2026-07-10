#!/usr/bin/env python3
"""Check the ORRO thin wrapper skeleton stays a delegating wrapper."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
SETUP_CFG = ROOT / "setup.cfg"
PACKAGE_DIR = ROOT / "src/orro_wrapper"
DOC_PATH = ROOT / "docs/thin-wrapper.md"
INVARIANT = "Depone verifies; witnessd executes; ORRO exposes the workflow"


def fail(message: str) -> None:
    print(f"ORRO wrapper violation: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_contains(label: str, haystack: str, needle: str) -> None:
    if needle not in haystack:
        fail(f"{label} must contain {needle!r}")


def check_pyproject() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    require_contains("pyproject.toml", text, 'name = "orro-product-wrapper"')
    require_contains("pyproject.toml", text, "dependencies = []")
    require_contains("pyproject.toml", text, 'orro = "orro_wrapper.cli:main"')
    require_contains("pyproject.toml", text, 'orro-wrapper = "orro_wrapper.cli:main"')


def check_setup_cfg() -> None:
    text = SETUP_CFG.read_text(encoding="utf-8")
    require_contains("setup.cfg", text, "name = orro-product-wrapper")
    require_contains("setup.cfg", text, "orro = orro_wrapper.cli:main")
    require_contains("setup.cfg", text, "orro-wrapper = orro_wrapper.cli:main")


def check_package_files() -> None:
    required = ["__init__.py", "__main__.py", "cli.py"]
    for name in required:
        path = PACKAGE_DIR / name
        if not path.is_file():
            fail(f"missing wrapper package file: src/orro_wrapper/{name}")
    text = "\n".join((PACKAGE_DIR / name).read_text(encoding="utf-8") for name in required)
    require_contains("wrapper package", text, "contains_engine_logic")
    require_contains("wrapper package", text, "implements_proofrun")
    require_contains("wrapper package", text, "implements_proofcheck")
    require_contains("wrapper package", text, "delegates_to_witnessd_hosted_orro")
    require_contains("wrapper package", text, "subprocess.run")

    forbidden = (
        "from depone",
        "import depone",
        "from witnessd",
        "import witnessd",
        "team-ledger verifier",
        "scheduler implementation",
    )
    lowered = text.lower()
    for needle in forbidden:
        if needle in lowered:
            fail(f"wrapper package must not contain {needle!r}")


def check_docs() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    require_contains("thin wrapper doc", text, INVARIANT)
    require_contains("thin wrapper doc", text, "delegates")
    require_contains("thin wrapper doc", text, "not proof")
    require_contains("thin wrapper doc", text, "not verifier truth")
    require_contains("thin wrapper doc", text, "does not implement proofrun")
    require_contains("thin wrapper doc", text, "does not implement proofcheck")
    require_contains("thin wrapper doc", text, "ORRO-owned `orro` command")


def main() -> int:
    if not PYPROJECT.is_file():
        fail("missing pyproject.toml")
    if not SETUP_CFG.is_file():
        fail("missing setup.cfg")
    if not PACKAGE_DIR.is_dir():
        fail("missing src/orro_wrapper package")
    if not DOC_PATH.is_file():
        fail("missing docs/thin-wrapper.md")
    check_pyproject()
    check_setup_cfg()
    check_package_files()
    check_docs()
    print("ORRO wrapper: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
