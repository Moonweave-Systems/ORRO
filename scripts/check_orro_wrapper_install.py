#!/usr/bin/env python3
"""Smoke-test the ORRO wrapper package install without engine logic."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, NoReturn, cast

from orro_build_backend import BuildBackendBootstrapError, install_isolated_editable, prepare_build_venv


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "0.1"
DIST_NAME = "orro"


class InstallSmokeError(RuntimeError):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def fail(code: str, message: str, details: dict[str, Any] | None = None) -> NoReturn:
    raise InstallSmokeError(code, message, details)


def boundary() -> dict[str, Any]:
    return {
        "contains_engine_logic": False,
        "executes_proofrun": False,
        "implements_proofcheck": False,
        "implements_proofrun": False,
        "verifies_evidence": False,
        "approves_merge": False,
        "raises_assurance": False,
        "depone_verifies": True,
        "witnessd_executes": True,
        "orro_exposes_workflow": True,
    }


def run_command(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        fail(
            "ERR_ORRO_WRAPPER_INSTALL_COMMAND_FAILED",
            "wrapper install smoke command failed",
            {
                "command": command,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            },
        )
    return completed


def scripts_dir(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts" if os.name == "nt" else "bin")


def copy_source(destination: Path) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        ignored = {".git", "__pycache__", ".pytest_cache"}
        ignored.update(name for name in names if name.endswith(".egg-info"))
        return ignored.intersection(names)

    shutil.copytree(ROOT, destination, ignore=ignore)


def load_json_stdout(label: str, completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        fail("ERR_ORRO_WRAPPER_INSTALL_JSON_INVALID", f"{label} did not emit valid JSON", {"stdout": completed.stdout})
    if not isinstance(data, dict):
        fail("ERR_ORRO_WRAPPER_INSTALL_JSON_INVALID", f"{label} JSON must be an object")
    return cast(dict[str, Any], data)


def require_false(label: str, data: dict[str, Any], key: str) -> None:
    if data.get(key) is not False:
        fail("ERR_ORRO_WRAPPER_INSTALL_BOUNDARY_INVALID", f"{label}.{key} must be false", {"value": data.get(key)})


def check_boundary_payload(label: str, payload: dict[str, Any]) -> None:
    payload_boundary = payload.get("boundary")
    if not isinstance(payload_boundary, dict):
        fail("ERR_ORRO_WRAPPER_INSTALL_BOUNDARY_INVALID", f"{label} must include boundary object")
    boundary_payload = cast(dict[str, Any], payload_boundary)
    for key in (
        "contains_engine_logic",
        "implements_proofrun",
        "implements_proofcheck",
        "executes_proofrun_itself",
        "verifies_evidence_itself",
        "approves_merge",
        "raises_assurance",
    ):
        if key in boundary_payload:
            require_false(f"{label}.boundary", boundary_payload, key)


def check_orro_command_installed(bin_dir: Path) -> Path:
    orro = bin_dir / ("orro.exe" if os.name == "nt" else "orro")
    if not orro.exists():
        fail("ERR_ORRO_WRAPPER_INSTALL_ORRO_SCRIPT_MISSING", "ORRO package must install an orro console script", {"path": str(orro)})
    return orro


def install_smoke(workspace: Path | None, *, allow_network: bool) -> dict[str, Any]:
    owns_workspace = workspace is None
    workdir = Path(tempfile.mkdtemp(prefix="orro-wrapper-install-")) if workspace is None else workspace
    if workdir.exists() and any(workdir.iterdir()):
        fail("ERR_ORRO_WRAPPER_INSTALL_WORKSPACE_NOT_EMPTY", "workspace must be empty for install smoke", {"workspace": str(workdir)})
    workdir.mkdir(parents=True, exist_ok=True)
    venv_dir = workdir / "venv"
    source_dir = workdir / "source"
    try:
        copy_source(source_dir)
        python = prepare_build_venv(venv_dir)
        bin_dir = scripts_dir(venv_dir)
        wrapper = bin_dir / ("orro-wrapper.exe" if os.name == "nt" else "orro-wrapper")
        install_isolated_editable(python, source_dir, allow_network=allow_network)
        if not wrapper.exists():
            fail("ERR_ORRO_WRAPPER_INSTALL_SCRIPT_MISSING", "orro-wrapper console script was not installed", {"path": str(wrapper)})
        orro = check_orro_command_installed(bin_dir)

        boundary_payload = load_json_stdout("orro-wrapper boundary", run_command([str(wrapper), "boundary"]))
        orro_boundary_payload = load_json_stdout("orro boundary", run_command([str(orro), "boundary"]))
        self_test_payload = load_json_stdout("orro-wrapper self-test", run_command([str(wrapper), "self-test"]))
        version = run_command([str(wrapper), "--version"]).stdout.strip()
        expected_version = run_command(
            [
                str(python),
                "-c",
                (
                    "import importlib.metadata; "
                    f"print(importlib.metadata.version({DIST_NAME!r}))"
                ),
            ]
        ).stdout.strip()
        delegated = run_command([str(wrapper), "--engine-command", str(python), "delegate", "--", "-c", "print('delegated')"]).stdout.strip()

        check_boundary_payload("boundary", boundary_payload)
        check_boundary_payload("orro boundary", orro_boundary_payload)
        check_boundary_payload("self-test", self_test_payload)
        if boundary_payload.get("kind") != "orro-wrapper-info":
            fail("ERR_ORRO_WRAPPER_INSTALL_ASSERTION_FAILED", "boundary payload kind mismatch", {"kind": boundary_payload.get("kind")})
        if self_test_payload.get("decision") != "pass":
            fail("ERR_ORRO_WRAPPER_INSTALL_ASSERTION_FAILED", "self-test did not pass", {"payload": self_test_payload})
        if version != expected_version:
            fail(
                "ERR_ORRO_WRAPPER_INSTALL_ASSERTION_FAILED",
                "wrapper version must match package metadata",
                {"version": version, "metadata_version": expected_version},
            )
        if delegated != "delegated":
            fail("ERR_ORRO_WRAPPER_INSTALL_ASSERTION_FAILED", "delegate smoke did not return expected output", {"stdout": delegated})

        return {
            "kind": "orro-wrapper-install-smoke-result",
            "schema_version": SCHEMA_VERSION,
            "decision": "pass",
            "workspace": str(workdir),
            "installed_console_script": str(wrapper),
            "checks": [
                {"name": "editable_install", "status": "pass"},
                {"name": "console_script_installed", "status": "pass"},
                {"name": "orro_console_script_installed", "status": "pass"},
                {"name": "boundary_non_engine", "status": "pass"},
                {"name": "self_test_passes", "status": "pass"},
                {"name": "delegate_smoke", "status": "pass"},
            ],
            "boundary": boundary(),
            "not_proof": True,
            "not_verifier_truth": True,
            "not_package_publish": True,
        }
    finally:
        if owns_workspace:
            shutil.rmtree(workdir, ignore_errors=True)


def self_test() -> dict[str, Any]:
    payload = {
        "kind": "orro-wrapper-install-smoke-result",
        "schema_version": SCHEMA_VERSION,
        "decision": "pass",
        "workspace": None,
        "checks": [{"name": "self_test_shape", "status": "pass"}],
        "boundary": boundary(),
        "not_proof": True,
        "not_verifier_truth": True,
        "not_package_publish": True,
    }
    check_boundary_payload("self-test-shape", payload)
    return {
        "kind": "orro-wrapper-install-self-test-result",
        "schema_version": SCHEMA_VERSION,
        "decision": "pass",
        "checks": [
            {"name": "result_shape", "status": "pass"},
            {"name": "boundary_non_engine", "status": "pass"},
        ],
        "boundary": boundary(),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test the ORRO wrapper install.")
    parser.add_argument("--workspace", help="Empty workspace to use for the install smoke. Defaults to a temporary directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON. JSON is the default output.")
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Allow pip build isolation to bootstrap the wrapper's declared build dependency.",
    )
    parser.add_argument("--self-test", action="store_true", help="Run offline self-test without creating a venv.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = (
            self_test()
            if args.self_test
            else install_smoke(Path(args.workspace) if args.workspace else None, allow_network=args.allow_network)
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (InstallSmokeError, BuildBackendBootstrapError) as exc:
        print(
            json.dumps(
                {
                    "kind": "orro-wrapper-install-smoke-error",
                    "schema_version": SCHEMA_VERSION,
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "details": exc.details,
                    },
                    "boundary": boundary(),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
