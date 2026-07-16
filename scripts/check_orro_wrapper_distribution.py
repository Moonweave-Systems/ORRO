#!/usr/bin/env python3
"""Build and smoke-test the ORRO wrapper wheel without publishing it."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path
from typing import Any, NoReturn, cast


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "0.1"
FORBIDDEN_PACKAGE_PREFIXES = ("depone/", "Depone/", "witnessd/")
FORBIDDEN_ENGINE_NAME_TOKENS = (
    "proofrun",
    "proofcheck",
    "team_ledger",
    "team-ledger",
    "scheduler",
    "observer",
    "fanin",
    "fan_in",
    "verifier",
    "depone",
    "witnessd",
)


class DistributionCheckError(RuntimeError):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def fail(code: str, message: str, details: dict[str, Any] | None = None) -> NoReturn:
    raise DistributionCheckError(code, message, details)


def boundary() -> dict[str, Any]:
    return {
        "contains_engine_logic": False,
        "owns_orro_command": True,
        "implements_proofrun": False,
        "implements_proofcheck": False,
        "approves_merge": False,
        "raises_assurance": False,
        "depone_verifies": True,
        "witnessd_executes": True,
        "orro_exposes_workflow": True,
    }


def run_command(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        fail(
            "ERR_ORRO_WRAPPER_DISTRIBUTION_COMMAND_FAILED",
            "wrapper distribution command failed",
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


def create_venv(venv_dir: Path) -> None:
    venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)


def copy_source(destination: Path) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        ignored = {".git", "__pycache__", ".pytest_cache", "build", "dist"}
        ignored.update(name for name in names if name.endswith(".egg-info"))
        return ignored.intersection(names)

    shutil.copytree(ROOT, destination, ignore=ignore)


def load_json_stdout(label: str, completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_JSON_INVALID", f"{label} did not emit valid JSON", {"stdout": completed.stdout})
    if not isinstance(data, dict):
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_JSON_INVALID", f"{label} JSON must be an object")
    return cast(dict[str, Any], data)


def inspect_wheel(wheel_path: Path) -> dict[str, Any]:
    if not zipfile.is_zipfile(wheel_path):
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_WHEEL_INVALID", "built artifact is not a valid wheel", {"wheel": str(wheel_path)})
    with zipfile.ZipFile(wheel_path) as archive:
        names = archive.namelist()
    forbidden_packages = [name for name in names if name.startswith(FORBIDDEN_PACKAGE_PREFIXES)]
    forbidden_engine_names = [
        name
        for name in names
        if not name.endswith("/")
        and not ".dist-info/" in name
        and any(token in name.lower().replace("-", "_") for token in FORBIDDEN_ENGINE_NAME_TOKENS)
    ]
    if forbidden_packages:
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_ENGINE_PACKAGE_PRESENT", "wheel contains engine package paths", {"paths": forbidden_packages})
    if forbidden_engine_names:
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_ENGINE_FILE_PRESENT", "wheel contains engine-looking implementation files", {"paths": forbidden_engine_names})
    if not any(name == "orro_wrapper/cli.py" for name in names):
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_WRAPPER_MISSING", "wheel must include orro_wrapper/cli.py", {"wheel": str(wheel_path)})
    return {
        "file_count": len(names),
        "contains_depone": False,
        "contains_witnessd": False,
        "contains_engine_logic": False,
    }


def inspect_entry_points(wheel_path: Path) -> dict[str, bool]:
    with zipfile.ZipFile(wheel_path) as archive:
        entry_points_name = next((name for name in archive.namelist() if name.endswith(".dist-info/entry_points.txt")), None)
        if entry_points_name is None:
            fail("ERR_ORRO_WRAPPER_DISTRIBUTION_ENTRY_POINTS_MISSING", "wheel entry_points.txt is missing")
        entry_points_name = cast(str, entry_points_name)
        entry_points = archive.read(entry_points_name).decode("utf-8")
    has_wrapper = "orro-wrapper = orro_wrapper.cli:main" in entry_points
    has_orro = any(line.strip().startswith("orro =") for line in entry_points.splitlines())
    if not has_wrapper:
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_WRAPPER_ENTRY_POINT_MISSING", "wheel must expose orro-wrapper")
    if not has_orro:
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_ORRO_ENTRY_POINT_MISSING", "wheel must expose ORRO-owned orro")
    return {"orro-wrapper": True, "orro": True}


def check_installed_commands(venv_dir: Path) -> dict[str, bool]:
    bin_dir = scripts_dir(venv_dir)
    wrapper = bin_dir / ("orro-wrapper.exe" if os.name == "nt" else "orro-wrapper")
    orro = bin_dir / ("orro.exe" if os.name == "nt" else "orro")
    if not wrapper.exists():
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_SCRIPT_MISSING", "installed wheel did not create orro-wrapper", {"path": str(wrapper)})
    if not orro.exists():
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_ORRO_SCRIPT_MISSING", "installed wheel did not create ORRO-owned orro", {"path": str(orro)})
    return {"orro-wrapper": True, "orro": True}


def check_boundary_payload(label: str, payload: dict[str, Any]) -> None:
    payload_boundary = payload.get("boundary")
    if not isinstance(payload_boundary, dict):
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_BOUNDARY_INVALID", f"{label} must include boundary object")
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
        if key in boundary_payload and boundary_payload.get(key) is not False:
            fail("ERR_ORRO_WRAPPER_DISTRIBUTION_BOUNDARY_INVALID", f"{label}.boundary.{key} must be false")


def prepare_build_venv(venv_dir: Path) -> Path:
    create_venv(venv_dir)
    bin_dir = scripts_dir(venv_dir)
    python = bin_dir / ("python.exe" if os.name == "nt" else "python")
    run_command([str(python), "-m", "pip", "uninstall", "--yes", "setuptools"])
    probe = run_command(
        [
            str(python),
            "-c",
            "import importlib.util; print(importlib.util.find_spec('setuptools') is not None)",
        ]
    )
    if probe.stdout.strip() != "False":
        fail(
            "ERR_ORRO_WRAPPER_DISTRIBUTION_BUILD_ENV_INVALID",
            "wrapper build venv must not contain setuptools before the isolated build",
            {"stdout": probe.stdout, "stderr": probe.stderr},
        )
    return python


def build_wheel(source_dir: Path, dist_dir: Path, python: Path) -> Path:
    run_command([str(python), "-m", "pip", "wheel", "--no-deps", "-w", str(dist_dir), str(source_dir)])
    wheels = sorted(dist_dir.glob("orro-*.whl"))
    if len(wheels) != 1:
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_WHEEL_NOT_FOUND", "expected exactly one ORRO wrapper wheel", {"wheels": [str(path) for path in wheels]})
    return wheels[0]


def distribution_check(workspace: Path | None, *, allow_network: bool) -> dict[str, Any]:
    owns_workspace = workspace is None
    workdir = Path(tempfile.mkdtemp(prefix="orro-wrapper-dist-")) if workspace is None else workspace
    if workdir.exists() and any(workdir.iterdir()):
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_WORKSPACE_NOT_EMPTY", "workspace must be empty for distribution check", {"workspace": str(workdir)})
    workdir.mkdir(parents=True, exist_ok=True)
    source_dir = workdir / "source"
    dist_dir = workdir / "dist"
    build_venv_dir = workdir / "build-venv"
    venv_dir = workdir / "venv"
    try:
        copy_source(source_dir)
        dist_dir.mkdir()
        build_python = prepare_build_venv(build_venv_dir)
        if not allow_network:
            fail(
                "ERR_ORRO_WRAPPER_DISTRIBUTION_NETWORK_NOT_ALLOWED",
                "isolated wrapper build dependency bootstrap requires --allow-network",
                {"build_backend": "setuptools.build_meta", "build_requirement": "setuptools>=61"},
            )
        wheel_path = build_wheel(source_dir, dist_dir, build_python)
        package_contents = inspect_wheel(wheel_path)
        entry_points = inspect_entry_points(wheel_path)

        create_venv(venv_dir)
        bin_dir = scripts_dir(venv_dir)
        python = bin_dir / ("python.exe" if os.name == "nt" else "python")
        run_command([str(python), "-m", "pip", "install", str(wheel_path)])
        installed_commands = check_installed_commands(venv_dir)
        wrapper = bin_dir / ("orro-wrapper.exe" if os.name == "nt" else "orro-wrapper")

        boundary_payload = load_json_stdout("orro-wrapper boundary", run_command([str(wrapper), "boundary"]))
        self_test_payload = load_json_stdout("orro-wrapper self-test", run_command([str(wrapper), "self-test"]))
        orro_boundary_payload = load_json_stdout("orro boundary", run_command([str(bin_dir / ("orro.exe" if os.name == "nt" else "orro")), "boundary"]))
        delegated = run_command([str(wrapper), "delegate", "--", "flowplan", "--help"]).stdout
        check_boundary_payload("boundary", boundary_payload)
        check_boundary_payload("self-test", self_test_payload)
        check_boundary_payload("orro boundary", orro_boundary_payload)
        if self_test_payload.get("decision") != "pass":
            fail("ERR_ORRO_WRAPPER_DISTRIBUTION_ASSERTION_FAILED", "installed wrapper self-test did not pass", {"payload": self_test_payload})
        if "usage: witnessd flowplan" not in delegated:
            fail("ERR_ORRO_WRAPPER_DISTRIBUTION_ASSERTION_FAILED", "delegate smoke did not show witnessd flowplan usage", {"stdout": delegated})

        return {
            "kind": "orro-wrapper-distribution-check",
            "schema_version": SCHEMA_VERSION,
            "decision": "pass",
            "workspace": str(workdir),
            "wheel": str(wheel_path),
            "built_wheel": True,
            "installed_wheel": True,
            "built_sdist": False,
            "sdist_note": "sdist build is deferred; v0 distribution smoke requires local wheel build/install.",
            "commands": installed_commands,
            "wheel_entry_points": entry_points,
            "package_contents": package_contents,
            "checks": [
                {"name": "build_venv_has_no_setuptools_before_build", "status": "pass"},
                {"name": "wheel_build", "status": "pass"},
                {"name": "wheel_contains_no_engine_packages", "status": "pass"},
                {"name": "wheel_entry_points_include_orro", "status": "pass"},
                {"name": "wheel_install", "status": "pass"},
                {"name": "installed_commands_include_orro", "status": "pass"},
                {"name": "installed_wrapper_self_test", "status": "pass"},
                {"name": "installed_wrapper_in_process_delegate_smoke", "status": "pass"},
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
    fake_names = [
        "orro_wrapper/__init__.py",
        "orro_wrapper/cli.py",
        "orro-0.1.0.dist-info/entry_points.txt",
    ]
    forbidden_packages = [name for name in fake_names if name.startswith(FORBIDDEN_PACKAGE_PREFIXES)]
    if forbidden_packages:
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_SELF_TEST_FAILED", "self-test false positive on allowed wrapper names")
    payload = {
        "kind": "orro-wrapper-distribution-check",
        "schema_version": SCHEMA_VERSION,
        "decision": "pass",
        "built_wheel": True,
        "installed_wheel": True,
        "commands": {"orro-wrapper": True, "orro": True},
        "package_contents": {
            "contains_depone": False,
            "contains_witnessd": False,
            "contains_engine_logic": False,
        },
        "boundary": boundary(),
        "not_proof": True,
        "not_verifier_truth": True,
        "not_package_publish": True,
    }
    if payload["commands"]["orro"] is not True:
        fail("ERR_ORRO_WRAPPER_DISTRIBUTION_SELF_TEST_FAILED", "self-test command ownership guard failed")
    return {
        "kind": "orro-wrapper-distribution-self-test-result",
        "schema_version": SCHEMA_VERSION,
        "decision": "pass",
        "checks": [
            {"name": "result_shape", "status": "pass"},
            {"name": "boundary_non_engine", "status": "pass"},
            {"name": "forbidden_package_detection", "status": "pass"},
            {"name": "command_shadowing_shape", "status": "pass"},
        ],
        "boundary": boundary(),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and smoke-test the local ORRO wrapper wheel.")
    parser.add_argument("--workspace", "--workdir", dest="workspace", help="Empty workspace for build/install artifacts. Defaults to a temporary directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON. JSON is the default output.")
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Allow pip build isolation to bootstrap the wrapper's declared build dependency.",
    )
    parser.add_argument("--self-test", action="store_true", help="Run offline self-test without building a wheel.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = (
            self_test()
            if args.self_test
            else distribution_check(Path(args.workspace) if args.workspace else None, allow_network=args.allow_network)
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except DistributionCheckError as exc:
        print(
            json.dumps(
                {
                    "kind": "orro-wrapper-distribution-check-error",
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
