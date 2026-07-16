#!/usr/bin/env python3
"""Check the ORRO thin wrapper skeleton stays a delegating wrapper."""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch


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
    require_contains("pyproject.toml", text, 'name = "orro"')
    require_contains("pyproject.toml", text, 'version = "0.1.0"')
    require_contains("pyproject.toml", text, 'dependencies = ["witnessd>=2.3.2"]')
    require_contains("pyproject.toml", text, 'orro = "orro_wrapper.cli:main"')
    require_contains("pyproject.toml", text, 'orro-wrapper = "orro_wrapper.cli:main"')


def check_setup_cfg() -> None:
    text = SETUP_CFG.read_text(encoding="utf-8")
    require_contains("setup.cfg", text, "name = orro")
    require_contains("setup.cfg", text, "version = 0.1.0")
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
    require_contains("wrapper package", text, "from witnessd.__main__ import ORRO_COMMANDS, main as witnessd_main")

    forbidden = (
        "from depone",
        "import depone",
        "subprocess.run",
        "ORRO_ENGINE_COMMAND",
        "DEFAULT_ENGINE_COMMAND",
        "team-ledger verifier",
        "scheduler implementation",
    )
    lowered = text.lower()
    for needle in forbidden:
        if needle in lowered:
            fail(f"wrapper package must not contain {needle!r}")


def check_in_process_delegation() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from orro_wrapper.cli import main

    witnessd_main = Mock(return_value=0)
    with (
        patch("orro_wrapper.cli.ORRO_COMMANDS", frozenset({"flowplan"})),
        patch("orro_wrapper.cli.witnessd_main", witnessd_main),
    ):
        result = main(["flowplan", "--help"])
    if result != 0:
        fail("in-process delegation returned a non-zero status")
    witnessd_main.assert_called_once_with(["orro", "flowplan", "--help"])


def check_unknown_command_error() -> None:
    from orro_wrapper.cli import main

    stderr = io.StringIO()
    with (
        patch("orro_wrapper.cli.ORRO_COMMANDS", frozenset({"flowplan"})),
        patch("orro_wrapper.cli.witnessd_main", Mock()),
        redirect_stderr(stderr),
    ):
        result = main(["flowpln"])
    if result != 2:
        fail("unknown command must exit 2")
    message = stderr.getvalue()
    require_contains("unknown command error", message, "orro: unknown command 'flowpln'")
    require_contains("unknown command suggestion", message, "Did you mean 'flowplan'?")
    require_contains("unknown command list", message, "Valid commands:")


def check_local_commands() -> None:
    from orro_wrapper.cli import main

    for command, expected_kind in (
        ("boundary", "orro-wrapper-info"),
        ("self-test", "orro-wrapper-self-test-result"),
    ):
        stdout = io.StringIO()
        with patch("orro_wrapper.cli.get_version", return_value="0.1.0"), redirect_stdout(stdout):
            result = main([command])
        if result != 0:
            fail(f"local {command} command returned a non-zero status")
        require_contains(f"local {command} output", stdout.getvalue(), expected_kind)


def check_explicit_delegate() -> None:
    from orro_wrapper.cli import main

    witnessd_main = Mock(return_value=0)
    with patch("orro_wrapper.cli.witnessd_main", witnessd_main):
        result = main(["delegate", "--", "flowplan", "--help"])
    if result != 0:
        fail("explicit delegate returned a non-zero status")
    witnessd_main.assert_called_once_with(["orro", "flowplan", "--help"])


def check_missing_witnessd_error() -> None:
    from orro_wrapper.cli import main

    stderr = io.StringIO()
    with patch("orro_wrapper.cli.witnessd_main", None), redirect_stderr(stderr):
        result = main(["flowplan"])
    if result == 0:
        fail("missing witnessd must return a non-zero status")
    require_contains("missing witnessd error", stderr.getvalue(), "install witnessd>=2.3.2")


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
    check_in_process_delegation()
    check_unknown_command_error()
    check_local_commands()
    check_explicit_delegate()
    check_missing_witnessd_error()
    check_docs()
    print("ORRO wrapper: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
