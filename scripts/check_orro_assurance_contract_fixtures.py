#!/usr/bin/env python3
"""Exercise negative fixtures for ORRO assurance contract checks."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def ignored_copy_names(_directory: str, names: list[str]) -> set[str]:
    ignored = {".git", ".omx", "__pycache__"}
    return {name for name in names if name in ignored or name.endswith(".pyc")}


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def fixture_repo() -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory(prefix="orro-assurance-contract-")
    workspace = Path(temp.name) / "repo"
    shutil.copytree(ROOT, workspace, ignore=ignored_copy_names)
    init = run(["git", "init"], workspace)
    if init.returncode != 0:
        raise RuntimeError(init.stderr)
    add = run(["git", "add", "."], workspace)
    if add.returncode != 0:
        raise RuntimeError(add.stderr)
    return temp


def run_contract(workspace: Path) -> subprocess.CompletedProcess[str]:
    return run([sys.executable, "scripts/check_orro_repo_contract.py"], workspace)


def replace_line(path: Path, predicate: Callable[[str], bool], rewrite: Callable[[str], list[str]]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    rewritten: list[str] = []
    replaced = False
    for line in lines:
        if not replaced and predicate(line):
            rewritten.extend(rewrite(line))
            replaced = True
        else:
            rewritten.append(line)
    if not replaced:
        raise RuntimeError(f"target line not found in {path}")
    path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")


def duplicate_workflow_plan_artifact_row(workspace: Path) -> None:
    path = workspace / "docs/orro-strategic-review-spec.md"
    replace_line(
        path,
        lambda line: line.strip().startswith("| workflow-plan |"),
        lambda line: [line, line],
    )


def remove_workflow_plan_verifier_truth_token(workspace: Path) -> None:
    path = workspace / "docs/orro-strategic-review-spec.md"

    def rewrite(line: str) -> list[str]:
        if "verifier truth" not in line:
            raise RuntimeError("workflow-plan row does not contain verifier truth")
        return [line.replace("verifier truth", "verifier boundary claim", 1)]

    replace_line(path, lambda line: line.strip().startswith("| workflow-plan |"), rewrite)


def remove_corpus_required_risk(workspace: Path) -> None:
    path = workspace / "docs/assurance/strategic-review-corpus.v0.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for case in data["cases"]:
        if case["risk"] == "long_automation_trust_confusion":
            case["risk"] = "report_proof_confusion"
            break
    else:
        raise RuntimeError("long automation corpus case not found")
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def track_local_omx_state(workspace: Path) -> None:
    path = workspace / ".omx/runtime-state.txt"
    path.parent.mkdir()
    path.write_text("local runtime state must stay untracked\n", encoding="utf-8")
    add = run(["git", "add", ".omx/runtime-state.txt"], workspace)
    if add.returncode != 0:
        raise RuntimeError(add.stderr)


def expect_contract_pass() -> None:
    with fixture_repo() as temp:
        workspace = Path(temp) / "repo"
        result = run_contract(workspace)
        if result.returncode != 0:
            raise AssertionError(
                "baseline contract unexpectedly failed\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )


def expect_contract_failure(
    name: str,
    mutate: Callable[[Path], None],
    expected_stderr: str,
) -> None:
    with fixture_repo() as temp:
        workspace = Path(temp) / "repo"
        mutate(workspace)
        result = run_contract(workspace)
        if result.returncode == 0:
            raise AssertionError(f"{name}: contract unexpectedly passed")
        if expected_stderr not in result.stderr:
            raise AssertionError(
                f"{name}: expected stderr to contain {expected_stderr!r}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )


def main() -> int:
    expect_contract_pass()
    expect_contract_failure(
        "duplicate workflow-plan artifact row",
        duplicate_workflow_plan_artifact_row,
        "artifact table must define 'workflow-plan' exactly once",
    )
    expect_contract_failure(
        "workflow-plan semantic token removal",
        remove_workflow_plan_verifier_truth_token,
        "artifact 'workflow-plan' missing semantic tokens",
    )
    expect_contract_failure(
        "missing strategic corpus risk",
        remove_corpus_required_risk,
        "strategic review corpus missing required risks",
    )
    expect_contract_failure(
        "tracked local .omx state",
        track_local_omx_state,
        ".omx is local workflow runtime state and must not be tracked",
    )
    print("ORRO assurance contract fixtures: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
