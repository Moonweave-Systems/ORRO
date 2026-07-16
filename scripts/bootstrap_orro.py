#!/usr/bin/env python3
"""Prepare or check local ORRO engine checkouts from the pinned engine lock.

This is setup/distribution orchestration only. It contains no proofrun,
proofcheck, scheduler, observer, fan-in, team-ledger, or verifier
implementation.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENGINE_LOCK = ROOT / "engine-lock/orro-e2e-engine-lock.json"
SCHEMA_VERSION = "0.1"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
ZERO_COMMIT = "0" * 40
FALSE_BOUNDARY_KEYS = ("approves_merge", "raises_assurance", "executes_commands", "verifies_evidence")


class BootstrapError(RuntimeError):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


@dataclass
class CommandOwnershipClaim:
    receipt: dict[str, Any]
    backups: list[tuple[Path, Path | None]]

    def commit(self) -> None:
        for _link, backup in self.backups:
            if backup is not None:
                backup.unlink(missing_ok=True)

    def rollback(self) -> None:
        for link, backup in reversed(self.backups):
            link.unlink(missing_ok=True)
            if backup is not None:
                backup.replace(link)


def boundary() -> dict[str, Any]:
    return {
        "contains_engine_logic": False,
        "executes_proofrun": False,
        "verifies_evidence": False,
        "approves_merge": False,
        "raises_assurance": False,
        "depone_verifies": True,
        "witnessd_executes": True,
        "orro_exposes_workflow": True,
    }


def fail_json(exc: BootstrapError) -> int:
    payload = {
        "kind": "orro-bootstrap-error",
        "schema_version": SCHEMA_VERSION,
        "decision": "fail",
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
        "boundary": boundary(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1


def load_json(path: Path, code: str) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as exc:
        raise BootstrapError(code, f"could not read engine lock: {path}", {"path": str(path), "error": str(exc)}) from exc
    except json.JSONDecodeError as exc:
        raise BootstrapError(code, f"engine lock is malformed JSON: {path}", {"path": str(path), "error": str(exc)}) from exc
    if not isinstance(payload, dict):
        raise BootstrapError("ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_INVALID", "engine lock must be a JSON object", {"path": str(path)})
    return payload


def validate_engine_lock(path: Path) -> dict[str, Any]:
    payload = load_json(path, "ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_LOAD_FAILED")
    if payload.get("kind") != "orro-engine-lock":
        raise BootstrapError("ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_INVALID", "engine lock kind must be orro-engine-lock", {"path": str(path)})
    if payload.get("schema_version") != "1.0":
        raise BootstrapError("ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_INVALID", "engine lock schema_version must be 1.0", {"path": str(path)})

    for key, repository in (("witnessd", "Moonweave-Systems/witnessd"), ("depone", "Moonweave-Systems/Depone")):
        engine = payload.get(key)
        if not isinstance(engine, dict):
            raise BootstrapError("ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_INVALID", f"engine lock {key} entry must be an object", {"path": str(path)})
        if engine.get("repository") != repository:
            raise BootstrapError(
                "ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_INVALID",
                f"engine lock {key}.repository must be {repository}",
                {"path": str(path), "actual": engine.get("repository")},
            )
        commit = engine.get("commit")
        if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit) or commit == ZERO_COMMIT:
            raise BootstrapError(
                "ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_INVALID",
                f"engine lock {key}.commit must be a nonzero 40-hex commit",
                {"path": str(path), "actual": commit},
            )

    lock_boundary = payload.get("boundary")
    if not isinstance(lock_boundary, dict):
        raise BootstrapError("ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_INVALID", "engine lock boundary must be an object", {"path": str(path)})
    for key in FALSE_BOUNDARY_KEYS:
        if lock_boundary.get(key) is not False:
            raise BootstrapError(
                "ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_INVALID",
                f"engine lock boundary.{key} must be false",
                {"path": str(path), "actual": lock_boundary.get(key)},
            )
    return payload


def lock_summary(lock_path: Path, lock: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(lock_path),
        "witnessd": {
            "repository": lock["witnessd"]["repository"],
            "commit": lock["witnessd"]["commit"],
        },
        "depone": {
            "repository": lock["depone"]["repository"],
            "commit": lock["depone"]["commit"],
        },
    }


def bootstrap_plan(mode: str, workspace: Path, lock_path: Path, lock: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "orro-bootstrap-plan",
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "workspace": str(workspace),
        "engine_lock": lock_summary(lock_path, lock),
        "planned_steps": [
            {
                "name": "prepare witnessd checkout",
                "action": "git clone or verify pinned checkout",
                "repository": lock["witnessd"]["repository"],
                "commit": lock["witnessd"]["commit"],
                "executes_engine": False,
                "verifies_evidence": False,
            },
            {
                "name": "prepare Depone checkout",
                "action": "git clone or verify pinned checkout",
                "repository": lock["depone"]["repository"],
                "commit": lock["depone"]["commit"],
                "executes_engine": False,
                "verifies_evidence": False,
            },
            {
                "name": "install witnessd editable",
                "action": "python3 -m pip install -e <witnessd-root>",
                "requires_explicit_flag": "--install-witnessd",
                "executes_engine": False,
                "verifies_evidence": False,
            },
            {
                "name": "install ORRO wrapper last",
                "action": "python3 -m pip install --no-deps -e <ORRO-root>",
                "requires_explicit_flag": "--install-witnessd",
                "executes_engine": False,
                "verifies_evidence": False,
            },
            {
                "name": "claim ORRO command ownership",
                "action": "link venv/bin/orro and ~/.local/bin/orro to venv/bin/orro-wrapper",
                "requires_explicit_flag": "--install-witnessd",
                "executes_engine": False,
                "verifies_evidence": False,
            },
            {
                "name": "verify shared-environment ORRO commands",
                "action": "check wrapper metadata, boundary, delegation, and compatibility paths",
                "requires_explicit_flag": "--install-witnessd",
                "executes_engine": False,
                "verifies_evidence": False,
            },
        ],
        "not_proof": True,
        "not_verifier_truth": True,
        "not_package_publish": True,
        "boundary": boundary(),
    }


def git_head(root: Path, label: str) -> str:
    completed = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise BootstrapError(
            "ERR_ORRO_BOOTSTRAP_COMMAND_FAILED",
            f"could not read {label} git HEAD",
            {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr},
        )
    commit = completed.stdout.strip()
    if not COMMIT_RE.fullmatch(commit):
        raise BootstrapError("ERR_ORRO_BOOTSTRAP_COMMAND_FAILED", f"{label} git HEAD was not a 40-hex commit", {"stdout": completed.stdout})
    return commit


def check_existing(witnessd_root: Path, depone_root: Path, lock_path: Path, lock: dict[str, Any]) -> dict[str, Any]:
    if not witnessd_root.is_dir():
        raise BootstrapError("ERR_ORRO_BOOTSTRAP_ENGINE_ROOT_MISSING", "witnessd root is missing", {"path": str(witnessd_root)})
    if not depone_root.is_dir():
        raise BootstrapError("ERR_ORRO_BOOTSTRAP_ENGINE_ROOT_MISSING", "Depone root is missing", {"path": str(depone_root)})
    witnessd_actual = git_head(witnessd_root, "witnessd")
    depone_actual = git_head(depone_root, "Depone")
    witnessd_expected = lock["witnessd"]["commit"]
    depone_expected = lock["depone"]["commit"]
    steps = [
        {
            "name": "check witnessd commit",
            "status": "pass" if witnessd_actual == witnessd_expected else "fail",
            "expected": witnessd_expected,
            "actual": witnessd_actual,
        },
        {
            "name": "check Depone commit",
            "status": "pass" if depone_actual == depone_expected else "fail",
            "expected": depone_expected,
            "actual": depone_actual,
        },
    ]
    matched = all(step["status"] == "pass" for step in steps)
    receipt = {
        "kind": "orro-bootstrap-receipt",
        "schema_version": SCHEMA_VERSION,
        "mode": "check-existing",
        "engine_lock": lock_summary(lock_path, lock),
        "engine_lock_matched": matched,
        "witnessd_root": str(witnessd_root),
        "depone_root": str(depone_root),
        "steps": steps,
        "not_proof": True,
        "not_verifier_truth": True,
        "boundary": boundary(),
    }
    if not matched:
        raise BootstrapError("ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_MISMATCH", "local engine roots do not match engine lock", {"receipt": receipt})
    return receipt


def run_command(args: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    step = {
        "command": args,
        "cwd": str(cwd) if cwd else None,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        raise BootstrapError("ERR_ORRO_BOOTSTRAP_COMMAND_FAILED", f"command failed: {' '.join(args)}", step)
    return step


def require_virtual_environment(prefix: Path, base_prefix: Path) -> None:
    if prefix == base_prefix:
        raise BootstrapError(
            "ERR_ORRO_BOOTSTRAP_VENV_REQUIRED",
            "--install-witnessd requires running bootstrap with the shared virtual environment's Python",
            {"prefix": str(prefix), "base_prefix": str(base_prefix)},
        )


def replace_symlink(link: Path, target: Path | str) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    temporary = link.with_name(f".{link.name}.orro-owner-tmp")
    try:
        temporary.unlink(missing_ok=True)
        temporary.symlink_to(target)
        temporary.replace(link)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise BootstrapError(
            "ERR_ORRO_BOOTSTRAP_COMMAND_OWNER_FAILED",
            f"could not set ORRO command owner: {link}",
            {"path": str(link), "target": str(target), "error": str(exc)},
        ) from exc


def claim_orro_command_owner(scripts: Path, path_bin: Path) -> CommandOwnershipClaim:
    wrapper = scripts / "orro-wrapper"
    if not wrapper.is_file():
        raise BootstrapError(
            "ERR_ORRO_BOOTSTRAP_WRAPPER_MISSING",
            "ORRO wrapper install did not create orro-wrapper",
            {"path": str(wrapper)},
        )
    orro = scripts / "orro"
    path_orro = path_bin / "orro"
    backups: list[tuple[Path, Path | None]] = []
    try:
        for link, target in ((orro, wrapper.name), (path_orro, wrapper)):
            backup = link.with_name(f".{link.name}.orro-owner-backup")
            backup.unlink(missing_ok=True)
            if os.path.lexists(link):
                link.replace(backup)
                backups.append((link, backup))
            else:
                backups.append((link, None))
            replace_symlink(link, target)
    except (OSError, BootstrapError) as exc:
        claim = CommandOwnershipClaim(receipt={}, backups=backups)
        claim.rollback()
        if isinstance(exc, BootstrapError):
            raise
        raise BootstrapError(
            "ERR_ORRO_BOOTSTRAP_COMMAND_OWNER_FAILED",
            "could not preserve the previous ORRO command owner",
            {"error": str(exc)},
        ) from exc
    receipt = {
        "name": "claim ORRO command ownership",
        "status": "pass",
        "entry_point": "orro_wrapper.cli:main",
        "orro": str(orro),
        "orro_resolves_to": str(orro.resolve()),
        "path_orro": str(path_orro),
        "path_orro_resolves_to": str(path_orro.resolve()),
        "executes_engine": False,
        "verifies_evidence": False,
    }
    return CommandOwnershipClaim(receipt=receipt, backups=backups)


def load_command_json(label: str, step: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(step["stdout"])
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise BootstrapError(
            "ERR_ORRO_BOOTSTRAP_INSTALL_SMOKE_FAILED",
            f"{label} did not emit JSON",
            {"stdout": step.get("stdout"), "stderr": step.get("stderr")},
        ) from exc
    if not isinstance(payload, dict):
        raise BootstrapError("ERR_ORRO_BOOTSTRAP_INSTALL_SMOKE_FAILED", f"{label} JSON must be an object")
    return payload


def verify_orro_install(python: Path, scripts: Path, path_bin: Path, witnessd_root: Path) -> dict[str, Any]:
    wrapper = scripts / "orro-wrapper"
    orro = scripts / "orro"
    path_orro = path_bin / "orro"
    for label, command in (("environment", orro), ("PATH-facing", path_orro)):
        if not command.is_symlink() or command.resolve() != wrapper.resolve():
            raise BootstrapError(
                "ERR_ORRO_BOOTSTRAP_INSTALL_SMOKE_FAILED",
                f"{label} orro does not resolve to the ORRO wrapper",
                {"orro": str(command), "actual": str(command.resolve()), "expected": str(wrapper.resolve())},
            )

    metadata = run_command(
        [
            str(python),
            "-c",
            (
                "import importlib.metadata as m; "
                "eps=[e for e in m.distribution('orro').entry_points if e.group == 'console_scripts' and e.name == 'orro']; "
                "print(eps[0].value)"
            ),
        ]
    )["stdout"].strip()
    if metadata != "orro_wrapper.cli:main":
        raise BootstrapError(
            "ERR_ORRO_BOOTSTRAP_INSTALL_SMOKE_FAILED",
            "installed ORRO metadata has the wrong orro entry point",
            {"expected": "orro_wrapper.cli:main", "actual": metadata},
        )

    path_env = os.environ.copy()
    path_env["PATH"] = os.pathsep.join([str(path_bin), str(scripts), path_env.get("PATH", "")])
    selected = shutil.which("orro", path=path_env["PATH"])
    if selected is None or Path(selected) != path_orro:
        raise BootstrapError(
            "ERR_ORRO_BOOTSTRAP_INSTALL_SMOKE_FAILED",
            "PATH lookup did not select the managed ORRO command",
            {"expected": str(path_orro), "actual": selected, "path": path_env["PATH"]},
        )
    boundary_step = run_command(["orro", "boundary"], env=path_env)
    boundary_payload = load_command_json("orro boundary", boundary_step)
    if boundary_payload.get("kind") != "orro-wrapper-info" or boundary_payload.get("boundary", {}).get("contains_engine_logic") is not False:
        raise BootstrapError(
            "ERR_ORRO_BOOTSTRAP_INSTALL_SMOKE_FAILED",
            "PATH-facing orro did not report the ORRO wrapper boundary",
            {"payload": boundary_payload},
        )

    delegate_step = run_command(["orro", "flowplan", "--help"], cwd=witnessd_root, env=path_env)
    if "usage: witnessd flowplan" not in delegate_step["stdout"]:
        raise BootstrapError(
            "ERR_ORRO_BOOTSTRAP_INSTALL_SMOKE_FAILED",
            "PATH-facing orro flowplan --help did not reach witnessd",
            {"stdout": delegate_step["stdout"], "stderr": delegate_step["stderr"]},
        )
    environment_step = run_command([str(orro), "boundary"])
    wrapper_step = run_command([str(wrapper), "boundary"])
    module_step = run_command([str(python), "-m", "orro", "--help"], cwd=witnessd_root)
    return {
        "name": "verify shared-environment ORRO commands",
        "status": "pass",
        "entry_point": metadata,
        "path_command": str(path_orro),
        "path_command_resolves_to": str(path_orro.resolve()),
        "boundary_kind": boundary_payload["kind"],
        "contains_engine_logic": False,
        "delegated_command": delegate_step["command"],
        "compatibility_commands": [environment_step["command"], wrapper_step["command"], module_step["command"]],
        "executes_engine": False,
        "verifies_evidence": False,
    }


def clone_or_verify(repo: str, commit: str, root: Path, *, allow_network: bool) -> dict[str, Any]:
    if root.exists():
        actual = git_head(root, repo)
        if actual != commit:
            raise BootstrapError(
                "ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_MISMATCH",
                f"existing {repo} checkout does not match engine lock",
                {"path": str(root), "expected": commit, "actual": actual},
            )
        return {"name": f"verify existing {repo} checkout", "status": "pass", "path": str(root), "expected": commit, "actual": actual}

    if not allow_network:
        raise BootstrapError(
            "ERR_ORRO_BOOTSTRAP_NETWORK_REQUIRED",
            "cloning engine repos requires --allow-network",
            {"repository": repo, "destination": str(root)},
        )
    root.parent.mkdir(parents=True, exist_ok=True)
    clone_step = run_command(["git", "clone", f"https://github.com/{repo}.git", str(root)])
    checkout_step = run_command(["git", "-C", str(root), "checkout", commit])
    return {
        "name": f"clone {repo} checkout",
        "status": "pass",
        "path": str(root),
        "expected": commit,
        "actual": git_head(root, repo),
        "commands": [clone_step, checkout_step],
    }


def execute_bootstrap(workspace: Path, lock_path: Path, lock: dict[str, Any], *, allow_network: bool, install_witnessd: bool) -> dict[str, Any]:
    if not allow_network and not workspace.exists():
        raise BootstrapError("ERR_ORRO_BOOTSTRAP_NETWORK_REQUIRED", "--execute needs --allow-network when creating engine checkouts", {"workspace": str(workspace)})
    workspace.mkdir(parents=True, exist_ok=True)
    witnessd_root = workspace / "witnessd"
    depone_root = workspace / "Depone"
    steps = [
        clone_or_verify(lock["witnessd"]["repository"], lock["witnessd"]["commit"], witnessd_root, allow_network=allow_network),
        clone_or_verify(lock["depone"]["repository"], lock["depone"]["commit"], depone_root, allow_network=allow_network),
    ]
    if install_witnessd:
        require_virtual_environment(Path(sys.prefix), Path(sys.base_prefix))
        install_step = run_command([sys.executable, "-m", "pip", "install", "-e", str(witnessd_root)])
        steps.append({"name": "install witnessd editable", "status": "pass", "command": install_step, "executes_engine": False, "verifies_evidence": False})
        wrapper_install = run_command([sys.executable, "-m", "pip", "install", "--no-deps", "-e", str(ROOT)])
        steps.append({"name": "install ORRO wrapper last", "status": "pass", "command": wrapper_install, "executes_engine": False, "verifies_evidence": False})
        scripts = Path(sys.executable).parent
        path_bin = Path.home() / ".local/bin"
        claim = claim_orro_command_owner(scripts, path_bin)
        try:
            verification = verify_orro_install(Path(sys.executable), scripts, path_bin, witnessd_root)
        except BootstrapError:
            claim.rollback()
            raise
        claim.commit()
        steps.append(claim.receipt)
        steps.append(verification)
    return {
        "kind": "orro-bootstrap-receipt",
        "schema_version": SCHEMA_VERSION,
        "mode": "execute",
        "workspace": str(workspace),
        "engine_lock": lock_summary(lock_path, lock),
        "engine_lock_matched": True,
        "witnessd_root": str(witnessd_root),
        "depone_root": str(depone_root),
        "steps": steps,
        "not_proof": True,
        "not_verifier_truth": True,
        "boundary": boundary(),
    }


def write_output(path: str | None, payload: dict[str, Any]) -> None:
    if not path:
        return
    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        raise BootstrapError("ERR_ORRO_BOOTSTRAP_WRITE_FAILED", f"could not write output: {target}", {"path": str(target), "error": str(exc)}) from exc


def resolve_mode(args: argparse.Namespace) -> str:
    selected = [name for name in ("dry_run", "execute", "check_existing") if getattr(args, name)]
    if len(selected) > 1:
        raise BootstrapError("ERR_ORRO_BOOTSTRAP_MODE_CONFLICT", "select only one bootstrap mode", {"selected": selected})
    if not selected:
        return "dry-run"
    return selected[0].replace("_", "-")


def self_test() -> int:
    checks: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="orro-bootstrap-self-test-") as raw_tmp:
        tmp = Path(raw_tmp)
        valid = write_lock(tmp / "valid.json")
        lock = validate_engine_lock(valid)
        assert lock["witnessd"]["repository"] == "Moonweave-Systems/witnessd"
        checks.append({"name": "valid_engine_lock_parses", "status": "pass"})

        expect_error("malformed_lock_fails", "ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_LOAD_FAILED", lambda: validate_engine_lock(write_text(tmp / "bad.json", "{bad")), checks)
        expect_error("invalid_repository_fails", "ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_INVALID", lambda: validate_engine_lock(write_lock(tmp / "bad-repo.json", witnessd_repo="Moonweave-Systems/not-witnessd")), checks)
        expect_error("boundary_overclaim_fails", "ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_INVALID", lambda: validate_engine_lock(write_lock(tmp / "overclaim.json", boundary_overrides={"approves_merge": True})), checks)

        args = parse_args(["--dry-run", "--execute", "--workspace", str(tmp / "workspace")])
        expect_error("mode_conflict_fails", "ERR_ORRO_BOOTSTRAP_MODE_CONFLICT", lambda: resolve_mode(args), checks)
        expect_error(
            "shared_venv_required_for_install",
            "ERR_ORRO_BOOTSTRAP_VENV_REQUIRED",
            lambda: require_virtual_environment(Path("/usr"), Path("/usr")),
            checks,
        )
        require_virtual_environment(Path("/tmp/orro-venv"), Path("/usr"))

        plan = bootstrap_plan("dry-run", tmp / "workspace", valid, lock)
        assert plan["kind"] == "orro-bootstrap-plan"
        assert plan["boundary"]["contains_engine_logic"] is False
        planned_text = json.dumps(plan["planned_steps"], sort_keys=True)
        for forbidden in ("proofrun", "proofcheck", "handoff"):
            assert forbidden not in planned_text
        assert "install ORRO wrapper last" in planned_text
        assert "claim ORRO command ownership" in planned_text
        assert "verify shared-environment ORRO commands" in planned_text
        checks.append({"name": "dry_run_output_shape", "status": "pass"})
        checks.append({"name": "dry_run_has_no_proof_commands", "status": "pass"})

        scripts = tmp / "venv/bin"
        path_bin = tmp / "home/.local/bin"
        scripts.mkdir(parents=True)
        write_text(scripts / "orro", "from orro.__main__ import main\n")
        wrapper = write_text(scripts / "orro-wrapper", "from orro_wrapper.cli import main\n")
        claim = claim_orro_command_owner(scripts, path_bin)
        assert (scripts / "orro").resolve() == wrapper.resolve()
        assert (path_bin / "orro").resolve() == wrapper.resolve()
        assert claim.receipt["entry_point"] == "orro_wrapper.cli:main"
        claim.rollback()
        assert (scripts / "orro").read_text(encoding="utf-8") == "from orro.__main__ import main\n"
        assert not (path_bin / "orro").exists()
        claim = claim_orro_command_owner(scripts, path_bin)
        claim.commit()
        assert (scripts / "orro").resolve() == wrapper.resolve()
        assert (path_bin / "orro").resolve() == wrapper.resolve()
        checks.append({"name": "orro_command_owner_is_deterministic", "status": "pass"})

        witnessd_repo = tmp / "witnessd"
        depone_repo = tmp / "Depone"
        seed_repo(witnessd_repo)
        seed_repo(depone_repo)
        mismatch = write_lock(tmp / "mismatch.json", witnessd_commit="1" * 40, depone_commit="2" * 40)
        mismatch_lock = validate_engine_lock(mismatch)
        expect_error(
            "check_existing_mismatch_fails",
            "ERR_ORRO_BOOTSTRAP_ENGINE_LOCK_MISMATCH",
            lambda: check_existing(witnessd_repo, depone_repo, mismatch, mismatch_lock),
            checks,
        )
    result = {
        "kind": "orro-bootstrap-self-test-result",
        "schema_version": SCHEMA_VERSION,
        "decision": "pass",
        "checks": checks,
        "boundary": boundary(),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def expect_error(name: str, code: str, fn: Any, checks: list[dict[str, Any]]) -> None:
    try:
        fn()
    except BootstrapError as exc:
        if exc.code != code:
            raise AssertionError(f"{name} raised {exc.code}, expected {code}") from exc
        checks.append({"name": name, "status": "pass", "code": code})
        return
    raise AssertionError(f"{name} did not raise {code}")


def write_text(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def write_lock(
    path: Path,
    *,
    witnessd_repo: str = "Moonweave-Systems/witnessd",
    depone_repo: str = "Moonweave-Systems/Depone",
    witnessd_commit: str = "0" * 39 + "1",
    depone_commit: str = "0" * 39 + "2",
    boundary_overrides: dict[str, Any] | None = None,
) -> Path:
    lock_boundary: dict[str, Any] = {
        "approves_merge": False,
        "raises_assurance": False,
        "executes_commands": False,
        "verifies_evidence": False,
    }
    if boundary_overrides:
        lock_boundary.update(boundary_overrides)
    payload = {
        "kind": "orro-engine-lock",
        "schema_version": "1.0",
        "witnessd": {"repository": witnessd_repo, "commit": witnessd_commit, "ref_name": "main"},
        "depone": {"repository": depone_repo, "commit": depone_commit, "ref_name": "main"},
        "boundary": lock_boundary,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def seed_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    run_command(["git", "init", "-q"], cwd=repo)
    run_command(["git", "config", "user.email", "orro@example.invalid"], cwd=repo)
    run_command(["git", "config", "user.name", "ORRO"], cwd=repo)
    (repo / "README.md").write_text("# bootstrap fixture\n", encoding="utf-8")
    run_command(["git", "add", "-A"], cwd=repo)
    run_command(["git", "commit", "-qm", "seed"], cwd=repo)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan, check, or prepare local ORRO engine checkouts.")
    parser.add_argument("--dry-run", action="store_true", help="Emit a setup plan without mutating anything. This is the default mode.")
    parser.add_argument("--execute", action="store_true", help="Create or verify pinned local engine checkouts. Requires --allow-network for cloning.")
    parser.add_argument("--check-existing", action="store_true", help="Inspect existing engine roots and compare them to the engine lock.")
    parser.add_argument("--workspace", help="Workspace where engine checkouts would be prepared.")
    parser.add_argument("--engine-lock", default=str(DEFAULT_ENGINE_LOCK), help="Path to ORRO engine lock JSON.")
    parser.add_argument("--witnessd-root", help="Existing witnessd checkout for --check-existing.")
    parser.add_argument("--depone-root", help="Existing Depone checkout for --check-existing.")
    parser.add_argument("--allow-network", action="store_true", help="Allow --execute to clone engine repositories.")
    parser.add_argument("--install-witnessd", action="store_true", help="Allow --execute to run python3 -m pip install -e <witnessd-root>.")
    parser.add_argument("--out", help="Write the plan or receipt JSON to this path.")
    parser.add_argument("--json", action="store_true", help="Emit JSON. JSON is the default output format.")
    parser.add_argument("--self-test", action="store_true", help="Run offline bootstrap self-tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.self_test:
        return self_test()
    try:
        mode = resolve_mode(args)
        lock_path = Path(args.engine_lock).expanduser().resolve()
        lock = validate_engine_lock(lock_path)

        if mode == "check-existing":
            if not args.witnessd_root or not args.depone_root:
                raise BootstrapError(
                    "ERR_ORRO_BOOTSTRAP_ENGINE_ROOT_MISSING",
                    "--check-existing requires --witnessd-root and --depone-root",
                )
            payload = check_existing(Path(args.witnessd_root).expanduser().resolve(), Path(args.depone_root).expanduser().resolve(), lock_path, lock)
        else:
            if not args.workspace:
                raise BootstrapError("ERR_ORRO_BOOTSTRAP_WORKSPACE_REQUIRED", f"{mode} requires --workspace")
            workspace = Path(args.workspace).expanduser().resolve()
            if mode == "execute":
                payload = execute_bootstrap(workspace, lock_path, lock, allow_network=args.allow_network, install_witnessd=args.install_witnessd)
            else:
                payload = bootstrap_plan(mode, workspace, lock_path, lock)

        write_output(args.out, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except BootstrapError as exc:
        return fail_json(exc)


if __name__ == "__main__":
    raise SystemExit(main())
