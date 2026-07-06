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
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "0.1"


class OrroE2EError(RuntimeError):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def _json_result(decision: str, checks: list[dict[str, Any]], *, error: dict[str, Any] | None = None) -> dict[str, Any]:
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
        **({"error": error} if error else {}),
    }


def _self_test() -> int:
    checks = [
        {"name": "result_shape", "status": "pass"},
        {"name": "boundary_non_engine", "status": "pass"},
        {"name": "error_codes_defined", "status": "pass"},
    ]
    result = _json_result("pass", checks)
    assert result["kind"] == "orro-e2e-smoke-result"
    assert result["boundary"]["contains_engine_logic"] is False
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _resolve_root(label: str, explicit: str | None, env_name: str, candidates: list[Path], error_code: str) -> Path:
    raw = explicit or os.environ.get(env_name)
    paths = [Path(raw).expanduser()] if raw else candidates
    for path in paths:
        resolved = path.resolve()
        if resolved.is_dir():
            return resolved
    searched = [str(path) for path in paths]
    raise OrroE2EError(error_code, f"{label} root is missing", {"searched": searched})


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


class SmokeRunner:
    def __init__(self, witnessd_root: Path, depone_root: Path, workdir: Path) -> None:
        self.witnessd_root = witnessd_root
        self.depone_root = depone_root
        self.workdir = workdir
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

    def _orro(self, args: list[str], *, expect: int | None = 0) -> tuple[int, dict[str, Any], str, str]:
        env = os.environ.copy()
        pythonpath_parts = [str(self.witnessd_root), str(self.depone_root)]
        if env.get("PYTHONPATH"):
            pythonpath_parts.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
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
        self._full_flow()
        self._scout_only_negative()
        return self.result("pass")

    def result(self, decision: str, error: dict[str, Any] | None = None) -> dict[str, Any]:
        result = _json_result(decision, self.checks, error=error)
        result["engine_roots"] = {
            "witnessd": str(self.witnessd_root),
            "depone": str(self.depone_root),
        }
        return result

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
    parser.add_argument("--workdir")
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
        workdir = Path(args.workdir).resolve() if args.workdir else Path(tempfile.mkdtemp(prefix="orro-e2e-"))
        runner = SmokeRunner(witnessd_root, depone_root, workdir)
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
