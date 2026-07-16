#!/usr/bin/env python3
"""Shared build-backend bootstrap policy for ORRO repository checks."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "0.1"
BUILD_BACKEND = "setuptools.build_meta"
BUILD_REQUIREMENT = "setuptools>=61"


class BuildBackendBootstrapError(RuntimeError):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def scripts_dir(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts" if os.name == "nt" else "bin")


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise BuildBackendBootstrapError(
            "ERR_ORRO_BUILD_BACKEND_COMMAND_FAILED",
            "ORRO build-backend bootstrap command failed",
            {
                "command": command,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            },
        )
    return completed


def setuptools_available(python: Path) -> bool:
    completed = run_command(
        [
            str(python),
            "-c",
            "import importlib.util; print(importlib.util.find_spec('setuptools') is not None)",
        ]
    )
    return completed.stdout.strip() == "True"


def prepare_build_venv(venv_dir: Path) -> Path:
    venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
    python = scripts_dir(venv_dir) / ("python.exe" if os.name == "nt" else "python")
    run_command([str(python), "-m", "pip", "uninstall", "--yes", "setuptools"])
    if setuptools_available(python):
        raise BuildBackendBootstrapError(
            "ERR_ORRO_BUILD_BACKEND_ENV_INVALID",
            "ORRO build venv must not contain setuptools before isolated bootstrap",
            {"build_backend": BUILD_BACKEND, "build_requirement": BUILD_REQUIREMENT},
        )
    return python


def require_build_backend_bootstrap(*, allow_network: bool) -> None:
    if not allow_network:
        raise BuildBackendBootstrapError(
            "ERR_ORRO_BUILD_BACKEND_NETWORK_NOT_ALLOWED",
            "isolated ORRO build dependency bootstrap requires --allow-network",
            {"build_backend": BUILD_BACKEND, "build_requirement": BUILD_REQUIREMENT},
        )


def isolated_wheel_command(python: Path, source_dir: Path, dist_dir: Path) -> list[str]:
    return [str(python), "-m", "pip", "wheel", "--no-deps", "-w", str(dist_dir), str(source_dir)]


def isolated_editable_command(python: Path, source_dir: Path) -> list[str]:
    return [str(python), "-m", "pip", "install", "--no-deps", "-e", str(source_dir)]


def build_isolated_wheel(
    python: Path,
    source_dir: Path,
    dist_dir: Path,
    *,
    allow_network: bool,
) -> Path:
    require_build_backend_bootstrap(allow_network=allow_network)
    dist_dir.mkdir(parents=True, exist_ok=True)
    run_command(isolated_wheel_command(python, source_dir, dist_dir))
    wheels = sorted(dist_dir.glob("orro-*.whl"))
    if len(wheels) != 1:
        raise BuildBackendBootstrapError(
            "ERR_ORRO_BUILD_BACKEND_WHEEL_NOT_FOUND",
            "expected exactly one ORRO wrapper wheel",
            {"wheels": [str(path) for path in wheels]},
        )
    return wheels[0]


def install_isolated_editable(
    python: Path,
    source_dir: Path,
    *,
    allow_network: bool,
) -> None:
    require_build_backend_bootstrap(allow_network=allow_network)
    run_command(isolated_editable_command(python, source_dir))


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="orro-build-backend-self-test-") as raw_tmp:
        python = prepare_build_venv(Path(raw_tmp) / "venv")
        if setuptools_available(python):
            raise RuntimeError("self-test build venv unexpectedly contains setuptools")

    offline_operations = {
        "wheel": lambda: build_isolated_wheel(
            Path("python"),
            Path("source"),
            Path("dist"),
            allow_network=False,
        ),
        "editable": lambda: install_isolated_editable(
            Path("python"),
            Path("source"),
            allow_network=False,
        ),
    }
    for label, operation in offline_operations.items():
        try:
            operation()
        except BuildBackendBootstrapError as exc:
            if exc.code != "ERR_ORRO_BUILD_BACKEND_NETWORK_NOT_ALLOWED":
                raise RuntimeError(f"self-test {label} received unexpected error code: {exc.code}") from exc
            if "--allow-network" not in exc.message:
                raise RuntimeError(f"self-test {label} network error did not explain the required flag") from exc
        else:
            raise RuntimeError(f"self-test accepted {label} bootstrap without network permission")

    isolated_commands = {
        "wheel": isolated_wheel_command(Path("python"), Path("source"), Path("dist")),
        "editable": isolated_editable_command(Path("python"), Path("source")),
    }
    for label, command in isolated_commands.items():
        if "--no-build-isolation" in command:
            raise RuntimeError(f"self-test isolated {label} command disabled build isolation")

    return {
        "kind": "orro-build-backend-self-test-result",
        "schema_version": SCHEMA_VERSION,
        "decision": "pass",
        "checks": [
            {"name": "build_venv_has_no_setuptools", "status": "pass"},
            {"name": "offline_wheel_bootstrap_fails_closed", "status": "pass"},
            {"name": "offline_editable_bootstrap_fails_closed", "status": "pass"},
            {"name": "isolated_wheel_build", "status": "pass"},
            {"name": "isolated_editable_install", "status": "pass"},
        ],
        "build_backend": BUILD_BACKEND,
        "build_requirement": BUILD_REQUIREMENT,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exercise the shared ORRO build-backend bootstrap policy.")
    parser.add_argument("--self-test", action="store_true", help="Run the offline missing-setuptools regression checks.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.self_test:
        print("error: --self-test is required", file=sys.stderr)
        return 2
    print(json.dumps(self_test(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
