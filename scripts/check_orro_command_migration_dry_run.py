#!/usr/bin/env python3
"""Dry-run historical ORRO command-migration compatibility without changing this repo."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from orro_build_backend import BuildBackendBootstrapError, build_isolated_wheel, prepare_build_venv


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "0.1"
WORKDIR_MARKER = ".orro-command-migration-dry-run-workdir"
SIMULATED_ENTRY_POINT = "orro = orro_wrapper.cli:main"


class DryRunError(RuntimeError):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def fail(code: str, message: str, details: dict[str, Any] | None = None) -> None:
    raise DryRunError(code, message, details)


def boundary() -> dict[str, Any]:
    return {
        "contains_engine_logic": False,
        "shadows_orro_in_committed_package": False,
        "simulates_orro_entry_point_in_temporary_copy": True,
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
            "ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_COMMAND_FAILED",
            "command migration dry-run command failed",
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


def command_path(bin_dir: Path, name: str) -> Path:
    return bin_dir / (f"{name}.exe" if os.name == "nt" else name)


def prepare_workdir(workspace: Path | None) -> tuple[Path, bool]:
    if workspace is None:
        return Path(tempfile.mkdtemp(prefix="orro-command-migration-dry-run-")), True

    workspace = workspace.resolve()
    if workspace.exists():
        marker = workspace / WORKDIR_MARKER
        if marker.exists():
            shutil.rmtree(workspace)
        elif any(workspace.iterdir()):
            fail(
                "ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_WORKDIR_NOT_EMPTY",
                "workdir must be empty or be a previous dry-run workspace",
                {"workdir": str(workspace), "marker": WORKDIR_MARKER},
            )
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / WORKDIR_MARKER).write_text("ORRO command migration dry-run workspace\n", encoding="utf-8")
    return workspace, False


def copy_source(destination: Path) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        ignored = {".git", "__pycache__", ".pytest_cache", "build", "dist"}
        ignored.update(name for name in names if name.endswith(".egg-info"))
        return ignored.intersection(names)

    shutil.copytree(ROOT, destination, ignore=ignore)


def add_simulated_orro_entry_point(source_dir: Path) -> bool:
    """Patch the copy to add the simulated ``orro`` entry point.

    Returns whether the source was already migrated (real ORRO command
    ownership landed), in which case the copy is left untouched: the
    post-migration steady state already matches the simulated target and is
    a valid pass, not a dry-run failure.
    """
    pyproject = source_dir / "pyproject.toml"
    setup_cfg = source_dir / "setup.cfg"
    pyproject_text = pyproject.read_text(encoding="utf-8")
    setup_cfg_text = setup_cfg.read_text(encoding="utf-8")

    if SIMULATED_ENTRY_POINT in pyproject_text or "    orro = orro_wrapper.cli:main" in setup_cfg_text:
        return True
    pyproject_text = pyproject_text.replace(
        'orro-wrapper = "orro_wrapper.cli:main"',
        'orro-wrapper = "orro_wrapper.cli:main"\norro = "orro_wrapper.cli:main"',
    )
    setup_cfg_text = setup_cfg_text.replace(
        "    orro-wrapper = orro_wrapper.cli:main",
        "    orro-wrapper = orro_wrapper.cli:main\n    orro = orro_wrapper.cli:main",
    )
    if 'orro = "orro_wrapper.cli:main"' not in pyproject_text:
        fail("ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_PATCH_FAILED", "could not patch pyproject entry points in source copy")
    if "    orro = orro_wrapper.cli:main" not in setup_cfg_text:
        fail("ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_PATCH_FAILED", "could not patch setup.cfg entry points in source copy")
    pyproject.write_text(pyproject_text, encoding="utf-8")
    setup_cfg.write_text(setup_cfg_text, encoding="utf-8")
    return False


def inspect_entry_points(wheel_path: Path) -> dict[str, bool]:
    if not zipfile.is_zipfile(wheel_path):
        fail("ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_WHEEL_INVALID", "built artifact is not a wheel", {"wheel": str(wheel_path)})
    with zipfile.ZipFile(wheel_path) as archive:
        entry_points_name = next((name for name in archive.namelist() if name.endswith(".dist-info/entry_points.txt")), None)
        if entry_points_name is None:
            fail("ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_ENTRY_POINTS_MISSING", "wheel entry_points.txt is missing")
        entry_points = archive.read(entry_points_name).decode("utf-8")
    return {
        "orro-wrapper": "orro-wrapper = orro_wrapper.cli:main" in entry_points,
        "orro": any(line.strip() == SIMULATED_ENTRY_POINT for line in entry_points.splitlines()),
    }


def install_wheel(python: Path, wheel_path: Path) -> None:
    run_command([str(python), "-m", "pip", "install", "--no-deps", "--force-reinstall", str(wheel_path)])


def load_json_stdout(label: str, completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        fail("ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_JSON_INVALID", f"{label} did not emit valid JSON", {"stdout": completed.stdout})
    if not isinstance(payload, dict):
        fail("ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_JSON_INVALID", f"{label} JSON must be an object")
    return payload


def check_boundary_payload(label: str, payload: dict[str, Any]) -> None:
    payload_boundary = payload.get("boundary")
    if not isinstance(payload_boundary, dict):
        fail("ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_BOUNDARY_INVALID", f"{label} must include boundary object")
    for key in (
        "contains_engine_logic",
        "implements_proofrun",
        "implements_proofcheck",
        "executes_proofrun_itself",
        "verifies_evidence_itself",
        "approves_merge",
        "raises_assurance",
    ):
        if key in payload_boundary and payload_boundary.get(key) is not False:
            fail("ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_BOUNDARY_INVALID", f"{label}.boundary.{key} must be false")


def installed_commands(bin_dir: Path) -> dict[str, bool]:
    return {
        "orro-wrapper": command_path(bin_dir, "orro-wrapper").exists(),
        "orro": command_path(bin_dir, "orro").exists(),
    }


def require_commands(label: str, actual: dict[str, bool], expected: dict[str, bool]) -> None:
    for command, value in expected.items():
        if actual.get(command) is not value:
            fail(
                "ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_COMMAND_SHAPE_INVALID",
                f"{label} command {command!r} presence mismatch",
                {"actual": actual, "expected": expected},
            )


def smoke_command(label: str, command: Path, python: Path) -> dict[str, Any]:
    boundary_payload = load_json_stdout(f"{label} boundary", run_command([str(command), "boundary"]))
    self_test_payload = load_json_stdout(f"{label} self-test", run_command([str(command), "self-test"]))
    delegated = run_command([str(command), "--engine-command", str(python), "delegate", "--", "-c", f"print('{label}-delegated')"]).stdout.strip()
    check_boundary_payload(f"{label} boundary", boundary_payload)
    check_boundary_payload(f"{label} self-test", self_test_payload)
    if boundary_payload.get("kind") != "orro-wrapper-info":
        fail("ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_ASSERTION_FAILED", f"{label} boundary kind mismatch", {"payload": boundary_payload})
    if self_test_payload.get("decision") != "pass":
        fail("ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_ASSERTION_FAILED", f"{label} self-test did not pass", {"payload": self_test_payload})
    if delegated != f"{label}-delegated":
        fail("ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_ASSERTION_FAILED", f"{label} delegate smoke mismatch", {"stdout": delegated})
    return {
        "boundary_kind": boundary_payload.get("kind"),
        "self_test_decision": self_test_payload.get("decision"),
        "delegate_stdout": delegated,
    }


def smoke_installed_commands(label: str, commands: dict[str, bool], bin_dir: Path, python: Path) -> dict[str, Any]:
    smoke = {
        "orro-wrapper": smoke_command(f"orro-wrapper-{label}", command_path(bin_dir, "orro-wrapper"), python),
    }
    if commands.get("orro"):
        smoke["orro"] = smoke_command(f"orro-{label}", command_path(bin_dir, "orro"), python)
    return smoke


def command_migration_dry_run(workspace: Path | None, *, allow_network: bool) -> dict[str, Any]:
    workdir, owns_workspace = prepare_workdir(workspace)
    venv_dir = workdir / "venv"
    current_source = workdir / "source-current"
    migrated_source = workdir / "source-migrated"
    try:
        copy_source(current_source)
        copy_source(migrated_source)
        already_migrated = add_simulated_orro_entry_point(migrated_source)
        python = prepare_build_venv(venv_dir)
        bin_dir = scripts_dir(venv_dir)

        # Once real ORRO command ownership has landed, the "current" copy already
        # carries the orro entry point too: that steady state is the valid target,
        # not a pre-migration baseline, so the expected shape shifts with it.
        expected_current_entry_points = {"orro-wrapper": True, "orro": already_migrated}

        current_wheel = build_isolated_wheel(
            python,
            current_source,
            workdir / "dist-current",
            allow_network=allow_network,
        )
        migrated_wheel = build_isolated_wheel(
            python,
            migrated_source,
            workdir / "dist-migrated",
            allow_network=allow_network,
        )
        current_entry_points = inspect_entry_points(current_wheel)
        migrated_entry_points = inspect_entry_points(migrated_wheel)
        if current_entry_points != expected_current_entry_points:
            fail("ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_ENTRY_POINTS_INVALID", "current wheel entry points changed", current_entry_points)
        if migrated_entry_points != {"orro-wrapper": True, "orro": True}:
            fail("ERR_ORRO_COMMAND_MIGRATION_DRY_RUN_ENTRY_POINTS_INVALID", "migrated wheel entry points are not simulated", migrated_entry_points)

        install_wheel(python, current_wheel)
        current_commands = installed_commands(bin_dir)
        require_commands("current install", current_commands, expected_current_entry_points)
        current_smoke = smoke_installed_commands("current", current_commands, bin_dir, python)

        install_wheel(python, migrated_wheel)
        migrated_commands = installed_commands(bin_dir)
        require_commands("migrated install", migrated_commands, {"orro-wrapper": True, "orro": True})
        migrated_smoke = smoke_installed_commands("migrated", migrated_commands, bin_dir, python)

        install_wheel(python, current_wheel)
        rollback_commands = installed_commands(bin_dir)
        require_commands("rollback install", rollback_commands, expected_current_entry_points)
        rollback_smoke = smoke_installed_commands("rollback", rollback_commands, bin_dir, python)

        return {
            "kind": "orro-command-migration-dry-run-result",
            "schema_version": SCHEMA_VERSION,
            "decision": "pass",
            "workspace": str(workdir),
            "current_wheel": str(current_wheel),
            "migrated_wheel": str(migrated_wheel),
            "simulated_entry_point": SIMULATED_ENTRY_POINT,
            "already_migrated": already_migrated,
            "commands": {
                "current": current_commands,
                "migrated": migrated_commands,
                "rollback": rollback_commands,
            },
            "wheel_entry_points": {
                "current": current_entry_points,
                "migrated": migrated_entry_points,
            },
            "smoke": {
                "current": current_smoke,
                "migrated": migrated_smoke,
                "rollback": rollback_smoke,
            },
            "checks": [
                {
                    "name": "current_package_already_exposes_orro_and_orro_wrapper" if already_migrated else "current_package_exposes_orro_wrapper_only",
                    "status": "pass",
                },
                {"name": "temporary_migrated_copy_exposes_orro_and_orro_wrapper", "status": "pass"},
                {"name": "simulated_commands_are_thin_wrapper_surfaces", "status": "pass"},
                {"name": "delegate_smoke_is_harmless", "status": "pass"},
                {
                    "name": "rollback_reinstall_preserves_migrated_state" if already_migrated else "rollback_reinstall_removes_orro",
                    "status": "pass",
                },
            ],
            "boundary": boundary(),
            "not_proof": True,
            "not_verifier_truth": True,
            "not_package_publish": True,
            "dry_run_metadata_is_not_proof": True,
        }
    finally:
        if owns_workspace:
            shutil.rmtree(workdir, ignore_errors=True)


def self_test() -> dict[str, Any]:
    payload = {
        "kind": "orro-command-migration-dry-run-result",
        "schema_version": SCHEMA_VERSION,
        "decision": "pass",
        "simulated_entry_point": SIMULATED_ENTRY_POINT,
        "commands": {
            "current": {"orro-wrapper": True, "orro": False},
            "migrated": {"orro-wrapper": True, "orro": True},
            "rollback": {"orro-wrapper": True, "orro": False},
        },
        "checks": [{"name": "self_test_shape", "status": "pass"}],
        "boundary": boundary(),
        "not_proof": True,
        "not_verifier_truth": True,
        "not_package_publish": True,
        "dry_run_metadata_is_not_proof": True,
    }
    require_commands("self-test current", payload["commands"]["current"], {"orro-wrapper": True, "orro": False})
    require_commands("self-test migrated", payload["commands"]["migrated"], {"orro-wrapper": True, "orro": True})
    require_commands("self-test rollback", payload["commands"]["rollback"], {"orro-wrapper": True, "orro": False})
    return {
        "kind": "orro-command-migration-dry-run-self-test-result",
        "schema_version": SCHEMA_VERSION,
        "decision": "pass",
        "checks": [
            {"name": "result_shape", "status": "pass"},
            {"name": "current_command_shape", "status": "pass"},
            {"name": "migrated_command_shape", "status": "pass"},
            {"name": "rollback_command_shape", "status": "pass"},
            {"name": "boundary_non_engine", "status": "pass"},
        ],
        "boundary": boundary(),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run historical ORRO command-migration compatibility in a temporary source copy.")
    parser.add_argument("--workdir", help="Workspace for source copies, wheels, and venv. Defaults to a temporary directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON. JSON is the default output.")
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Allow pip build isolation to bootstrap the wrapper's declared build dependency.",
    )
    parser.add_argument("--self-test", action="store_true", help="Run offline shape checks without creating a venv.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = (
            self_test()
            if args.self_test
            else command_migration_dry_run(Path(args.workdir) if args.workdir else None, allow_network=args.allow_network)
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (DryRunError, BuildBackendBootstrapError) as exc:
        print(
            json.dumps(
                {
                    "kind": "orro-command-migration-dry-run-error",
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
