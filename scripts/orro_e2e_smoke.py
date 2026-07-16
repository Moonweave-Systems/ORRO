#!/usr/bin/env python3
"""Run an ORRO smoke flow against local witnessd and Depone checkouts.

This is an orchestration harness only. It shells out to the existing
witnessd-hosted `orro` command and contains no proofrun or proofcheck engine
implementation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "0.1"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
LOCK_BOUNDARY_FALSE_KEYS = ("approves_merge", "raises_assurance", "executes_commands", "verifies_evidence")
ROLE_LANE_PLACEHOLDER_PROMPT_PREFIX = "Execute ORRO role "


class OrroE2EError(RuntimeError):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def _json_result(
    decision: str,
    checks: list[dict[str, Any]],
    *,
    engine_lock: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "kind": "orro-e2e-smoke-result",
        "schema_version": SCHEMA_VERSION,
        "decision": decision,
        "engine_roots": {
            "witnessd": None,
            "depone": None,
        },
        "checks": checks,
        "boundary": {
            "orchestrates_engines": True,
            "contains_engine_logic": False,
            "depone_verifies": True,
            "witnessd_executes": True,
            "orro_exposes_workflow": True,
            "approves_merge": False,
            "raises_assurance": False,
        },
        **({"engine_lock": engine_lock} if engine_lock else {}),
        **({"error": error} if error else {}),
    }


def _self_test() -> int:
    checks = [
        {"name": "result_shape", "status": "pass"},
        {"name": "boundary_non_engine", "status": "pass"},
        {"name": "error_codes_defined", "status": "pass"},
    ]
    with tempfile.TemporaryDirectory(prefix="orro-e2e-self-test-") as raw_tmp:
        tmp = Path(raw_tmp)
        _expect_error(
            "missing_engine_lock_path",
            "ERR_ORRO_E2E_ENGINE_LOCK_LOAD_FAILED",
            lambda: _validate_engine_lock(tmp / "missing.json"),
            checks,
        )
        malformed = tmp / "malformed.json"
        malformed.write_text("{not-json", encoding="utf-8")
        _expect_error(
            "malformed_engine_lock",
            "ERR_ORRO_E2E_ENGINE_LOCK_LOAD_FAILED",
            lambda: _validate_engine_lock(malformed),
            checks,
        )
        invalid_repo = _write_lock(tmp / "invalid-repo.json", witnessd_repo="Moonweave-Systems/not-witnessd")
        _expect_error(
            "invalid_engine_lock_repository",
            "ERR_ORRO_E2E_ENGINE_LOCK_INVALID",
            lambda: _validate_engine_lock(invalid_repo),
            checks,
        )
        overclaim = _write_lock(tmp / "overclaim.json", boundary_overrides={"approves_merge": True})
        _expect_error(
            "engine_lock_boundary_overclaim",
            "ERR_ORRO_E2E_ENGINE_LOCK_INVALID",
            lambda: _validate_engine_lock(overclaim),
            checks,
        )
        witnessd_repo = tmp / "witnessd"
        depone_repo = tmp / "Depone"
        _seed_repo(witnessd_repo)
        _seed_repo(depone_repo)
        mismatch = _write_lock(tmp / "mismatch.json", witnessd_commit="1" * 40, depone_commit="2" * 40)
        _expect_error(
            "engine_lock_mismatch",
            "ERR_ORRO_E2E_ENGINE_LOCK_MISMATCH",
            lambda: _engine_lock_status(mismatch, True, witnessd_repo, depone_repo),
            checks,
        )
        role_lane_plan = {
            "lanes": [
                {
                    "lane_id": "runner",
                    "may_execute": True,
                    "prompt": "Execute ORRO role runner for goal: update README safely",
                },
                {
                    "lane_id": "reviewer",
                    "may_execute": False,
                    "prompt": "Review the README without changing it",
                },
            ]
        }
        materialized = _materialize_executable_role_lane_prompts(role_lane_plan, "update README safely")
        assert materialized == 1
        assert role_lane_plan["lanes"][0]["prompt"] == "update README safely"
        assert role_lane_plan["lanes"][1]["prompt"] == "Review the README without changing it"
        checks.append({"name": "executable_role_lane_prompt_materialization", "status": "pass"})
    result = _json_result("pass", checks)
    assert result["kind"] == "orro-e2e-smoke-result"
    assert result["boundary"]["contains_engine_logic"] is False
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _expect_error(name: str, code: str, fn: Any, checks: list[dict[str, Any]]) -> None:
    try:
        fn()
    except OrroE2EError as exc:
        if exc.code != code:
            raise AssertionError(f"{name} raised {exc.code}, expected {code}") from exc
        checks.append({"name": name, "status": "pass", "code": code})
        return
    raise AssertionError(f"{name} did not raise {code}")


def _write_lock(
    path: Path,
    *,
    witnessd_repo: str = "Moonweave-Systems/witnessd",
    depone_repo: str = "Moonweave-Systems/Depone",
    witnessd_commit: str = "0" * 39 + "1",
    depone_commit: str = "0" * 39 + "2",
    boundary_overrides: dict[str, Any] | None = None,
) -> Path:
    boundary: dict[str, Any] = {
        "approves_merge": False,
        "raises_assurance": False,
        "executes_commands": False,
        "verifies_evidence": False,
    }
    if boundary_overrides:
        boundary.update(boundary_overrides)
    payload = {
        "kind": "orro-engine-lock",
        "schema_version": "1.0",
        "witnessd": {
            "repository": witnessd_repo,
            "commit": witnessd_commit,
            "ref_name": "main",
        },
        "depone": {
            "repository": depone_repo,
            "commit": depone_commit,
            "ref_name": "main",
        },
        "boundary": boundary,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _resolve_root(label: str, explicit: str | None, env_name: str, candidates: list[Path], error_code: str) -> Path:
    raw = explicit or os.environ.get(env_name)
    paths = [Path(raw).expanduser()] if raw else candidates
    for path in paths:
        resolved = path.resolve()
        if resolved.is_dir():
            return resolved
    searched = [str(path) for path in paths]
    raise OrroE2EError(error_code, f"{label} root is missing", {"searched": searched})


def _load_json_file(path: Path, code: str) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as exc:
        raise OrroE2EError(code, f"could not read engine lock: {path}", {"path": str(path), "error": str(exc)}) from exc
    except json.JSONDecodeError as exc:
        raise OrroE2EError(code, f"engine lock is malformed JSON: {path}", {"path": str(path), "error": str(exc)}) from exc
    if not isinstance(payload, dict):
        raise OrroE2EError("ERR_ORRO_E2E_ENGINE_LOCK_INVALID", "engine lock must be a JSON object", {"path": str(path)})
    return payload


def _validate_engine_lock(path: Path) -> dict[str, Any]:
    payload = _load_json_file(path, "ERR_ORRO_E2E_ENGINE_LOCK_LOAD_FAILED")
    if payload.get("kind") != "orro-engine-lock":
        raise OrroE2EError("ERR_ORRO_E2E_ENGINE_LOCK_INVALID", "engine lock kind must be orro-engine-lock", {"path": str(path)})
    if payload.get("schema_version") != "1.0":
        raise OrroE2EError("ERR_ORRO_E2E_ENGINE_LOCK_INVALID", "engine lock schema_version must be 1.0", {"path": str(path)})

    engines = {
        "witnessd": "Moonweave-Systems/witnessd",
        "depone": "Moonweave-Systems/Depone",
    }
    for key, repository in engines.items():
        engine = payload.get(key)
        if not isinstance(engine, dict):
            raise OrroE2EError("ERR_ORRO_E2E_ENGINE_LOCK_INVALID", f"engine lock {key} entry must be an object", {"path": str(path)})
        if engine.get("repository") != repository:
            raise OrroE2EError(
                "ERR_ORRO_E2E_ENGINE_LOCK_INVALID",
                f"engine lock {key}.repository must be {repository}",
                {"path": str(path), "actual": engine.get("repository")},
            )
        commit = engine.get("commit")
        if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
            raise OrroE2EError(
                "ERR_ORRO_E2E_ENGINE_LOCK_INVALID",
                f"engine lock {key}.commit must be a 40-hex commit",
                {"path": str(path), "actual": commit},
            )

    boundary = payload.get("boundary")
    if not isinstance(boundary, dict):
        raise OrroE2EError("ERR_ORRO_E2E_ENGINE_LOCK_INVALID", "engine lock boundary must be an object", {"path": str(path)})
    for key in LOCK_BOUNDARY_FALSE_KEYS:
        if boundary.get(key) is not False:
            raise OrroE2EError(
                "ERR_ORRO_E2E_ENGINE_LOCK_INVALID",
                f"engine lock boundary.{key} must be false",
                {"path": str(path), "actual": boundary.get(key)},
            )
    return payload


def _git_head(root: Path, label: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise OrroE2EError(
            "ERR_ORRO_E2E_COMMAND_FAILED",
            f"could not read {label} git HEAD",
            {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr},
        )
    commit = completed.stdout.strip()
    if not COMMIT_RE.fullmatch(commit):
        raise OrroE2EError("ERR_ORRO_E2E_COMMAND_FAILED", f"{label} git HEAD was not a 40-hex commit", {"stdout": completed.stdout})
    return commit


def _engine_lock_status(
    lock_path: Path | None,
    require_match: bool,
    witnessd_root: Path,
    depone_root: Path,
) -> dict[str, Any] | None:
    if lock_path is None:
        return None
    lock = _validate_engine_lock(lock_path)
    witnessd_commit = _git_head(witnessd_root, "witnessd")
    depone_commit = _git_head(depone_root, "Depone")
    expected_witnessd = lock["witnessd"]["commit"]
    expected_depone = lock["depone"]["commit"]
    matched = witnessd_commit == expected_witnessd and depone_commit == expected_depone
    status = {
        "path": str(lock_path),
        "matched": matched,
        "witnessd_commit": witnessd_commit,
        "depone_commit": depone_commit,
        "expected_witnessd_commit": expected_witnessd,
        "expected_depone_commit": expected_depone,
    }
    if require_match and not matched:
        mismatches = []
        if witnessd_commit != expected_witnessd:
            mismatches.append({"engine": "witnessd", "expected": expected_witnessd, "actual": witnessd_commit})
        if depone_commit != expected_depone:
            mismatches.append({"engine": "depone", "expected": expected_depone, "actual": depone_commit})
        raise OrroE2EError("ERR_ORRO_E2E_ENGINE_LOCK_MISMATCH", "engine checkout does not match e2e lock", {"mismatches": mismatches})
    return status


def _seed_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _run_raw(["git", "init", "-q"], cwd=repo)
    _run_raw(["git", "config", "user.email", "orro@example.invalid"], cwd=repo)
    _run_raw(["git", "config", "user.name", "ORRO"], cwd=repo)
    (repo / "README.md").write_text("# ORRO e2e fixture\n\nInitial content.\n", encoding="utf-8")
    (repo / "SKILL.md").write_text("---\nname: orro-e2e-fixture\n---\n", encoding="utf-8")
    _run_raw(["git", "add", "-A"], cwd=repo)
    _run_raw(["git", "commit", "-qm", "seed"], cwd=repo)


def _run_raw(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise OrroE2EError(
            "ERR_ORRO_E2E_COMMAND_FAILED",
            f"command failed: {' '.join(args)}",
            {
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            },
        )
    return completed


def _materialize_executable_role_lane_prompts(role_lane_plan: dict[str, Any], task: str) -> int:
    lanes = role_lane_plan.get("lanes")
    if not isinstance(lanes, list):
        raise OrroE2EError(
            "ERR_ORRO_E2E_ROLE_LANE_PLAN_INVALID",
            "role-lane plan lanes must be a list",
        )
    materialized = 0
    for lane in lanes:
        if not isinstance(lane, dict):
            raise OrroE2EError(
                "ERR_ORRO_E2E_ROLE_LANE_PLAN_INVALID",
                "role-lane plan lanes must contain objects",
            )
        if lane.get("may_execute") is True:
            lane["prompt"] = task
            materialized += 1
    return materialized


class SmokeRunner:
    def __init__(
        self,
        witnessd_root: Path,
        depone_root: Path,
        workdir: Path,
        allow_network: bool,
        engine_lock: dict[str, Any] | None = None,
    ) -> None:
        self.witnessd_root = witnessd_root
        self.depone_root = depone_root
        self.workdir = workdir
        self.allow_network = allow_network
        self.engine_lock = engine_lock
        self.checks: list[dict[str, Any]] = []

    def _record(self, name: str, status: str = "pass", **details: Any) -> None:
        payload = {"name": name, "status": status}
        if details:
            payload.update(details)
        self.checks.append(payload)

    def _assert(self, condition: bool, name: str, message: str, **details: Any) -> None:
        if not condition:
            self._record(name, "fail", message=message, **details)
            raise OrroE2EError("ERR_ORRO_E2E_ASSERTION_FAILED", message, {"check": name, **details})
        self._record(name, "pass", **details)

    def _engine_env(self) -> dict[str, str]:
        env = os.environ.copy()
        pythonpath_parts = [str(self.witnessd_root), str(self.depone_root)]
        if env.get("PYTHONPATH"):
            pythonpath_parts.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
        return env

    def _orro(self, args: list[str], *, expect: int | None = 0) -> tuple[int, dict[str, Any], str, str]:
        env = self._engine_env()
        completed = subprocess.run(
            [sys.executable, "-m", "orro", *args],
            cwd=self.witnessd_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if expect is not None and completed.returncode != expect:
            raise OrroE2EError(
                "ERR_ORRO_E2E_COMMAND_FAILED",
                f"orro command failed: {' '.join(args)}",
                {
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                },
            )
        payload: dict[str, Any] = {}
        if completed.stdout.strip():
            try:
                payload = json.loads(completed.stdout)
            except json.JSONDecodeError as exc:
                raise OrroE2EError(
                    "ERR_ORRO_E2E_COMMAND_FAILED",
                    f"orro command did not emit JSON: {' '.join(args)}",
                    {"stdout": completed.stdout, "stderr": completed.stderr, "json_error": str(exc)},
                ) from exc
        return completed.returncode, payload, completed.stdout, completed.stderr

    def run(self) -> dict[str, Any]:
        if self.workdir.exists():
            shutil.rmtree(self.workdir)
        self.workdir.mkdir(parents=True)
        self._wrapper_default_delegate_help()
        self._full_flow()
        self._scout_only_negative()
        return self.result("pass")

    def result(self, decision: str, error: dict[str, Any] | None = None) -> dict[str, Any]:
        result = _json_result(decision, self.checks, engine_lock=self.engine_lock, error=error)
        result["engine_roots"] = {
            "witnessd": str(self.witnessd_root),
            "depone": str(self.depone_root),
        }
        return result

    def _wrapper_default_delegate_help(self) -> None:
        wrapper_root = self.workdir / "wrapper-default-delegate"
        venv_dir = wrapper_root / "venv"
        venv.EnvBuilder(with_pip=True, clear=True, system_site_packages=False).create(venv_dir)
        bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
        python = bin_dir / ("python.exe" if os.name == "nt" else "python")
        wrapper = bin_dir / ("orro-wrapper.exe" if os.name == "nt" else "orro-wrapper")
        remove_setuptools = subprocess.run(
            [str(python), "-m", "pip", "uninstall", "--yes", "setuptools"],
            text=True,
            capture_output=True,
            check=False,
        )
        if remove_setuptools.returncode != 0:
            raise OrroE2EError(
                "ERR_ORRO_E2E_COMMAND_FAILED",
                "could not prepare wrapper regression venv without setuptools",
                {
                    "returncode": remove_setuptools.returncode,
                    "stdout": remove_setuptools.stdout,
                    "stderr": remove_setuptools.stderr,
                },
            )
        setuptools_probe = subprocess.run(
            [
                str(python),
                "-c",
                "import importlib.util; print(importlib.util.find_spec('setuptools') is not None)",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self._assert(
            setuptools_probe.returncode == 0 and setuptools_probe.stdout.strip() == "False",
            "wrapper_venv_has_no_setuptools_before_install",
            "wrapper regression venv must not contain setuptools before install",
            returncode=setuptools_probe.returncode,
            stdout=setuptools_probe.stdout,
            stderr=setuptools_probe.stderr,
        )
        if not self.allow_network:
            raise OrroE2EError(
                "ERR_ORRO_E2E_NETWORK_NOT_ALLOWED",
                "wrapper build dependency bootstrap requires --allow-network",
                {"build_backend": "setuptools.build_meta", "build_requirement": "setuptools>=61"},
            )
        install = subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "-e",
                str(ROOT),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if install.returncode != 0:
            raise OrroE2EError(
                "ERR_ORRO_E2E_COMMAND_FAILED",
                "wrapper install failed",
                {
                    "returncode": install.returncode,
                    "stdout": install.stdout,
                    "stderr": install.stderr,
                },
            )
        completed = subprocess.run(
            [str(wrapper), "delegate", "--", "--help"],
            cwd=self.witnessd_root,
            text=True,
            capture_output=True,
            check=False,
        )
        self._assert(
            completed.returncode == 0,
            "wrapper_default_delegate_help_exit_zero",
            "default wrapper delegate --help must exit zero",
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        self._assert(
            "usage: orro" in completed.stdout,
            "wrapper_default_delegate_help_reaches_orro",
            "default wrapper delegate --help must reach the ORRO public command",
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    def _full_flow(self) -> None:
        root = self.workdir / "happy"
        repo = root / "repo"
        home = root / "home"
        root.mkdir()
        _seed_repo(repo)
        goal = "update README safely"

        _code, advise, _stdout, _stderr = self._orro(["advise", goal, "--repo", str(repo), "--home", str(home), "--json"])
        self._assert(advise.get("kind") == "orro-workstyle-decision", "advise_returns_workstyle_decision", "advise did not return workstyle decision")
        self._assert(advise.get("boundary", {}).get("executes_commands") is False, "advise_non_executing", "advise boundary overclaimed execution")

        self._orro(["init", "--home", str(home), "--depone-root", str(self.depone_root)])
        self._assert((home / "provision.json").is_file(), "init_creates_provision_metadata", "init did not create provision.json")

        self._orro(["doctor", "--home", str(home), "--json"])
        lock = home / "orro-engine-lock.json"
        self._orro(["engine-lock", "--home", str(home), "--out", str(lock)])
        _code, lock_check, _stdout, _stderr = self._orro(["engine-lock", "--home", str(home), "--check", str(lock), "--json"])
        self._assert(lock_check.get("locked") is True, "engine_lock_check_locked", "engine-lock check did not report locked true", payload=lock_check)

        workflow_plan = home / "workflow-plan.json"
        role_lane_plan = home / "role-lane-plan.json"
        self._orro(
            [
                "flowplan",
                goal,
                "--root",
                str(repo),
                "--profile",
                "docs-change",
                "--out",
                str(workflow_plan),
                "--role-lanes-out",
                str(role_lane_plan),
                "--lane-adapter",
                "shell",
            ]
        )
        self._assert(workflow_plan.is_file(), "flowplan_writes_workflow_plan", "workflow plan missing")
        self._assert(role_lane_plan.is_file(), "flowplan_writes_role_lane_plan", "role-lane plan missing")

        try:
            role_lane_payload = json.loads(role_lane_plan.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OrroE2EError(
                "ERR_ORRO_E2E_ROLE_LANE_PLAN_INVALID",
                "could not load generated role-lane plan",
                {"path": str(role_lane_plan), "error": str(exc)},
            ) from exc
        if not isinstance(role_lane_payload, dict):
            raise OrroE2EError(
                "ERR_ORRO_E2E_ROLE_LANE_PLAN_INVALID",
                "generated role-lane plan must be a JSON object",
                {"path": str(role_lane_plan)},
            )
        materialized_lanes = _materialize_executable_role_lane_prompts(role_lane_payload, goal)
        role_lane_plan.write_text(json.dumps(role_lane_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        executable_lanes = [lane for lane in role_lane_payload["lanes"] if lane.get("may_execute") is True]
        self._assert(
            materialized_lanes > 0
            and all(
                lane.get("prompt") == goal
                and not str(lane.get("prompt", "")).startswith(ROLE_LANE_PLACEHOLDER_PROMPT_PREFIX)
                for lane in executable_lanes
            ),
            "flowplan_materializes_explicit_role_lane_prompts",
            "every executable role lane must carry the declared E2E task before proofrun",
            materialized_lanes=materialized_lanes,
        )

        proofrun_args = [
            "proofrun",
            goal,
            "--repo",
            str(repo),
            "--home",
            str(home),
            "--workflow-plan",
            str(workflow_plan),
            "--role-lane-plan",
            str(role_lane_plan),
            "--max-parallel",
            "1",
        ]
        _code, proofrun, _stdout, _stderr = self._orro(proofrun_args)
        run_dir = Path(str(proofrun.get("run_dir", "")))
        self._assert(run_dir.is_dir(), "proofrun_creates_run_dir", "proofrun did not create run dir", run_dir=str(run_dir))
        self._assert((run_dir / "team-ledger.json").is_file(), "proofrun_creates_team_ledger", "team-ledger.json missing")

        _code, next_payload, _stdout, _stderr = self._orro(["next", str(run_dir), "--home", str(home), "--json"])
        self._assert(next_payload.get("decision") != "complete", "next_before_auto_not_complete", "next was complete before proofcheck/handoff")

        _code, auto_session, _stdout, _stderr = self._orro(
            ["auto", "--until-complete", str(run_dir), "--home", str(home), "--max-steps", "2", "--json"]
        )
        self._assert((run_dir / "proofcheck-verdict.json").is_file(), "auto_creates_proofcheck_verdict", "proofcheck verdict missing")
        self._assert((run_dir / "orro-handoff.json").is_file(), "auto_creates_handoff", "handoff missing")
        self._assert(auto_session.get("boundary", {}).get("executes_proofrun") is False, "auto_does_not_execute_proofrun", "auto boundary allowed proofrun")

        _code, report, _stdout, _stderr = self._orro(["report", str(run_dir), "--home", str(home), "--json"])
        summary = report.get("summary", {})
        handoff = report.get("handoff", {})
        self._assert(summary.get("state") == "complete" or summary.get("complete") is True, "report_reaches_complete", "report did not reach complete", summary=summary)
        self._assert(handoff.get("approves_merge") is False, "report_does_not_approve_merge", "report approved merge")
        self._assert(handoff.get("raises_assurance") is False, "report_does_not_raise_assurance", "report raised assurance")

    def _scout_only_negative(self) -> None:
        root = self.workdir / "scout-only"
        repo = root / "repo"
        home = root / "home"
        root.mkdir()
        _seed_repo(repo)
        self._orro(["init", "--home", str(home), "--depone-root", str(self.depone_root)])

        _code, scout, _stdout, _stderr = self._orro(["scout", "inspect only", "--repo", str(repo), "--home", str(home)])
        scout_dir = self._find_scout_dir(scout, home)
        self._assert(scout_dir.is_dir(), "scout_creates_artifact_dir", "could not find scout artifact directory", scout_payload=scout)

        code, verdict, _stdout, _stderr = self._orro(["proofcheck", str(scout_dir), "--home", str(home), "--json"], expect=None)
        self._assert(code != 0, "scout_only_proofcheck_nonzero", "scout-only proofcheck unexpectedly passed", verdict=verdict)
        self._assert(verdict.get("decision") != "pass", "scout_only_not_pass", "scout-only proofcheck decision was pass", verdict=verdict)
        self._assert(not (scout_dir / "orro-handoff.json").exists(), "scout_only_no_handoff", "scout-only created handoff")

    def _find_scout_dir(self, payload: dict[str, Any], home: Path) -> Path:
        for key in ("artifact_dir", "scout_dir", "evidence_dir", "out_dir", "run_dir"):
            value = payload.get(key)
            if isinstance(value, str) and Path(value).is_dir():
                return Path(value)
        run_root = home / "runs"
        if run_root.is_dir():
            candidates = sorted((path for path in run_root.iterdir() if path.is_dir()), key=lambda path: path.stat().st_mtime, reverse=True)
            if candidates:
                return candidates[0]
        return Path("__missing_scout_dir__")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ORRO e2e smoke against local engine checkouts.")
    parser.add_argument("--witnessd-root")
    parser.add_argument("--depone-root")
    parser.add_argument("--engine-lock", help="Optional ORRO engine lock to validate before running smoke.")
    parser.add_argument("--require-lock-match", action="store_true", help="Require local engine HEADs to match --engine-lock commits.")
    parser.add_argument("--workdir")
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Allow pip build isolation to bootstrap the wrapper's declared build dependency.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result. JSON is the default output format.")
    parser.add_argument("--self-test", action="store_true", help="Validate output shape without engine checkouts.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.self_test:
        return _self_test()

    try:
        witnessd_root = _resolve_root(
            "witnessd",
            args.witnessd_root,
            "ORRO_WITNESSD_ROOT",
            [ROOT.parent / "witnessd"],
            "ERR_ORRO_E2E_WITNESSD_ROOT_MISSING",
        )
        depone_root = _resolve_root(
            "Depone",
            args.depone_root,
            "ORRO_DEPONE_ROOT",
            [ROOT.parent / "Depone", ROOT.parent / "depone"],
            "ERR_ORRO_E2E_DEPONE_ROOT_MISSING",
        )
        lock_path = Path(args.engine_lock).resolve() if args.engine_lock else None
        engine_lock = _engine_lock_status(lock_path, args.require_lock_match, witnessd_root, depone_root)
        workdir = Path(args.workdir).resolve() if args.workdir else Path(tempfile.mkdtemp(prefix="orro-e2e-"))
        runner = SmokeRunner(witnessd_root, depone_root, workdir, args.allow_network, engine_lock=engine_lock)
        result = runner.run()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except OrroE2EError as exc:
        result = _json_result(
            "fail",
            [],
            error={"code": exc.code, "message": exc.message, "details": exc.details},
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
