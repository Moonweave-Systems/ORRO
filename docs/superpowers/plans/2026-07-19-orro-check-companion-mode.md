# `orro check` Companion Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **This project also delegates correctness-critical implementation to Codex (gpt-5.6-sol) with Opus verification** — either path executes the same tasks below.

**Goal:** Add one guided command `orro check` that verifies already-driven work through deterministic shell checks (falsifiable Depone verdict) and reviews it read-only (advisory), sealing a `companion-manifest.json` that honestly labels "the reviewed work was NOT observed-executed", with zero execution-adapter lanes spawned.

**Architecture:** New witnessd CLI module `witnessd/cli/companion.py` (`_cmd_orro_check`), registered as internal `orro-check` and public alias `check`. It orchestrates existing surfaces **in-process** (via `witnessd.__main__.main(argv)` captured by `cli/_output._invoke_cli_capture`) exactly like `cli/flow.py`/`cli/team_go.py`: `flowplan --profile verification-only --check` → `proofrun --adapter shell` → `proofcheck` (Depone verdict), plus an independent `flowplan --profile review-only` → `orro-review` (advisory). It emits the manifest with `cli/_output._write_json_file` + `_hash_file`. **No engine-schema or Depone change** — the manifest is an ORRO orchestration artifact (like `orro-flow-result`), not Depone-contract evidence.

**Tech Stack:** Python stdlib only (witnessd runtime rule). Tests are `unittest.TestCase` driving `witnessd.__main__.main`. CI: `PYTHONPATH=<depone> python3 -m unittest discover -s tests -p 'test_*.py'`.

**Spec:** `docs/superpowers/specs/2026-07-19-orro-check-companion-mode-design.md` (ORRO repo).

**Implementation repo:** `/home/ubuntu/moonweave/witnessd` (dev clone; HEAD `ef0c32c`). Depone dev clone sibling at `/home/ubuntu/moonweave/depone`. Run witnessd tests with `PYTHONPATH=../depone`, `/usr/bin/python3` (avoid the trailofbits shim), `PYTHONDONTWRITEBYTECODE=1`.

---

## File Structure

| File | Responsibility | Create/Modify |
| --- | --- | --- |
| `witnessd/cli/companion.py` | `_cmd_orro_check` orchestrator + manifest emitter + zero-execution invariant | **Create** |
| `witnessd/__main__.py` | Register `orro-check` subparser (`_build_parser`); add `"check": "orro-check"` to `ORRO_COMMAND_MAP` | Modify (`_build_parser` near line 296; map near line 832) |
| `tests/test_orro_check.py` | End-to-end + unit tests (unittest, fake agy) | **Create** |
| `tests/test_orro_check_underlying_path.py` | Task 0 characterization of the raw verification-only path | **Create** (may be folded into `test_orro_check.py`) |
| `witnessd/CLAUDE.md` (Public names table) + `docs/` | Document `orro check` | Modify (Task 8) |

Reused verbatim (no change): `cli/_output.py` (`_invoke_cli_capture:173`, `_structured_error:66`, `_write_json_file:158`, `_hash_file:150`, `_depone_subprocess_env:22`, `_run_depone_json:39`), `cli/flow.py` argv patterns (`flowplan:351`, `proofrun:402`, `proofcheck:447`), `orro_review.run_review_role_lane_plan:48`, `orro_workflow.compile_role_lane_plan` (verification-only branch `272-303`, `_verify_lane_from_role:979`, `_review_lane_from_role:1096`).

---

## Exact in-process argv (grounded in flow.py / team_go.py)

The companion builds these argv lists and dispatches each via
`code, payload, stderr = _invoke_orro_check_phase(argv)` (a thin wrapper over
`_invoke_cli_capture` that JSON-parses stdout, mirroring `flow._invoke_orro_flow_phase:497`).

```python
# PROVISION — required first (Task 0 confirmed: proofrun/proofcheck need a
# provisioned home; `orro flow` does this via its init phase, flow.py:147).
init = ["init", "--home", str(home), "--repo", str(repo)]   # writes home/provision.json

# VERIFY — deterministic shell checks (zero AI adapters)
flowplan_verify = [
    "flowplan", goal, "--root", str(repo),
    "--profile", "verification-only",
    "--out", str(verify_workflow_plan),          # workflow-plan.json
    "--role-lanes-out", str(verify_role_lane_plan),
    "--lane-adapter", "shell",
    *sum((["--check", c] for c in checks), []),   # repeatable
    "--json",
]
proofrun = [
    "proofrun", goal, "--repo", str(repo), "--home", str(home),
    "--workflow-plan", str(verify_workflow_plan),
    "--role-lane-plan", str(verify_role_lane_plan),
    "--adapter", "shell",
    "--runner-sandbox", str(runner_sandbox),
    "--run-dir", str(run_dir),
    "--json",
]
proofcheck = [
    "proofcheck", "--evidence-dir", str(run_dir), "--home", str(home),
    "--out", str(proofcheck_path),                # proofcheck-verdict.json
    "--json",
]

# REVIEW — advisory, read-only (skipped under --no-review)
flowplan_review = [
    "flowplan", goal, "--root", str(repo),
    "--profile", "review-only",
    "--out", str(review_workflow_plan),
    "--role-lanes-out", str(review_role_lane_plan),
    "--lane-adapter", reviewer,                   # agy | gemini | claude
    "--model-policy", "default",
    "--json",
]
orro_review = [
    "orro-review", "--repo", str(repo), "--home", str(home),
    "--role-lane-plan", str(review_role_lane_plan),
    "--run-dir", str(run_dir),
    f"--{reviewer}-binary", reviewer_binary,      # default = reviewer name; overridable
    "--json",
]
```

`goal` is synthesized from `--base`: `goal = f"Review the changes on HEAD relative to {base} without editing files"` (this is how `--base` shapes the review lane prompt — `_review_lane_from_role:1136` builds `"Review ORRO goal without editing files: {goal}"`). `runner_sandbox`/`run_dir` are created under `home` mirroring `flow.py`. Checks are `sh -c <check>` shell lanes with empty write region (`_verify_lane_from_role:997`, region `[]`).

---

## Task 0: Characterize the raw verification-only path (DE-RISK — do first)

Proves the load-bearing assumption (verification-only shell checks run green through `proofrun → proofcheck → Depone` with **no** `--write-scope` and **no** AI adapter) BEFORE building the wrapper. witnessd/CLAUDE.md documents this path, but we confirm empirically and capture the exact working argv.

**Files:**
- Create: `tests/test_orro_check_underlying_path.py`

- [ ] **Step 1: Write the characterization test**

```python
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from witnessd.__main__ import main


def _depone_root() -> str:
    return os.environ.get("WITNESSD_DEPONE_ROOT", str(Path(__file__).resolve().parents[2] / "depone"))


def _seed_repo(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=repo, check=True)


def _run(argv: list[str]) -> tuple[int, object, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    stdout = out.getvalue()
    try:
        payload = json.loads(stdout) if stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {"_raw": stdout}
    return code, payload, err.getvalue()


class VerificationOnlyPathTest(unittest.TestCase):
    def test_shell_checks_reach_pass_without_write_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            _seed_repo(repo)
            home = root / "home"
            run_dir = root / "run"
            sandbox = root / "sandbox"
            wp = root / "workflow-plan.json"
            rlp = root / "role-lane-plan.json"
            verdict = root / "proofcheck-verdict.json"
            goal = "verify current working tree"

            code, _, err = _run([
                "flowplan", goal, "--root", str(repo),
                "--profile", "verification-only",
                "--out", str(wp), "--role-lanes-out", str(rlp),
                "--lane-adapter", "shell", "--check", "true", "--json",
            ])
            self.assertEqual(code, 0, err)
            plan = json.loads(rlp.read_text())
            # every lane is a shell verification-only lane — NO AI adapter
            for lane in plan["lanes"]:
                self.assertEqual(lane["adapter"], "shell", lane)
                self.assertEqual(lane["lane_intent"], "verification-only", lane)
                self.assertEqual(lane["region"], [], lane)

            code, _, err = _run([
                "proofrun", goal, "--repo", str(repo), "--home", str(home),
                "--workflow-plan", str(wp), "--role-lane-plan", str(rlp),
                "--adapter", "shell", "--runner-sandbox", str(sandbox),
                "--run-dir", str(run_dir), "--json",
            ])
            self.assertEqual(code, 0, err)
            self.assertTrue((run_dir / "team-ledger.json").is_file())

            code, payload, err = _run([
                "proofcheck", "--evidence-dir", str(run_dir), "--home", str(home),
                "--out", str(verdict), "--json",
            ])
            self.assertEqual(code, 0, err)
            self.assertEqual(payload.get("decision"), "pass", payload)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it**

Run: `cd /home/ubuntu/moonweave/witnessd && PYTHONPATH=../depone PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest tests.test_orro_check_underlying_path -v`
Expected: **PASS**. If it FAILS, STOP — the design's "reuse the verification-only path unchanged" assumption is wrong. Record the exact failing argv/error in a `DEVIATIONS.md` and surface it before proceeding (likely fixes: proofrun needs an extra flag, or `--home` must be pre-provisioned via `orro init`).

- [ ] **Step 3: Commit**

```bash
git add tests/test_orro_check_underlying_path.py
git commit -m "test: characterize verification-only shell path reaches Depone pass (#78)"
```

---

## Task 1: Register `orro check` skeleton + no-checks blocker

**Files:**
- Create: `witnessd/cli/companion.py`
- Modify: `witnessd/__main__.py` (subparser near line 296; `ORRO_COMMAND_MAP` near line 832)
- Create: `tests/test_orro_check.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_orro_check.py  (reuse _run/_seed_repo/_depone_root helpers as in Task 0)
class OrroCheckBlockerTest(unittest.TestCase):
    def test_no_checks_declared_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            _seed_repo(repo)
            code, payload, err = _run(["orro", "check", "--repo", str(repo), "--json"])
            self.assertEqual(code, 2, err)
            self.assertNotIn("Traceback", err)
            self.assertEqual(payload["kind"], "orro-companion-result")
            self.assertEqual(payload["decision"], "blocked")
            self.assertEqual(payload["error"]["code"], "ERR_ORRO_CHECK_NO_CHECKS_DECLARED")
            self.assertIn("required_input_or_grant", payload["error"])
            self.assertIn("next_command", payload["error"])
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONPATH=../depone PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest tests.test_orro_check.OrroCheckBlockerTest -v`
Expected: FAIL — `invalid choice: 'orro-check'` (command not registered).

- [ ] **Step 3: Register the command in `__main__.py`**

After the `orro-review` block (line 296), add:

```python
    orro_check = sub.add_parser(
        "orro-check",
        help=argparse.SUPPRESS,
        description=(
            "Companion: verify already-driven work with deterministic checks "
            "(Depone verdict) and review it read-only (advisory). Spawns zero "
            "execution-adapter lanes; does not claim observed execution."
        ),
    )
    orro_check.add_argument("--repo", "--root", dest="repo", default=None)
    orro_check.add_argument("--home", default=None)
    orro_check.add_argument("--run-dir", default=None)
    orro_check.add_argument("--check", action="append", default=None)
    orro_check.add_argument(
        "--reviewer", default="agy", choices=["agy", "gemini", "claude"]
    )
    orro_check.add_argument("--reviewer-binary", default=None)
    orro_check.add_argument("--no-review", action="store_true")
    orro_check.add_argument("--base", default=None)
    orro_check.add_argument("--timeout-seconds", type=int, default=120)
    orro_check.add_argument("--json", action="store_true")
    orro_check.set_defaults(func=_cli_handler("companion", "_cmd_orro_check"))
```

In `ORRO_COMMAND_MAP` (line 832 area) add: `"check": "orro-check",`.

- [ ] **Step 4: Create `witnessd/cli/companion.py` with the blocker path only**

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from witnessd.cli._output import _structured_error


def _emit_blocker(error: dict[str, object]) -> int:
    print(json.dumps({"kind": "orro-companion-result", "decision": "blocked",
                       "error": error}, sort_keys=True))
    return 2


def _cmd_orro_check(args: argparse.Namespace) -> int:
    checks = list(getattr(args, "check", None) or [])
    if not checks:
        return _emit_blocker(_structured_error(
            code="ERR_ORRO_CHECK_NO_CHECKS_DECLARED",
            message="orro check requires at least one --check command",
            reason="checks define what 'verified' means and cannot be inferred",
            required_input_or_grant="--check '<cmd>' (repeatable)",
            next_command="python3 -m orro check --check '<cmd>' --repo <repo>",
        ))
    raise NotImplementedError  # completed in Task 2
```

- [ ] **Step 5: Run to verify it passes**

Run: `PYTHONPATH=../depone PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest tests.test_orro_check.OrroCheckBlockerTest -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add witnessd/cli/companion.py witnessd/__main__.py tests/test_orro_check.py
git commit -m "feat: register orro check with no-checks blocker (#78)"
```

---

## Task 2: VERIFY half + manifest (`--no-review` path)

Implements verify → proofrun → proofcheck and emits `companion-manifest.json` with the honest labels. Gates exit on the Depone verdict.

**Files:**
- Modify: `witnessd/cli/companion.py`
- Modify: `tests/test_orro_check.py`

- [ ] **Step 1: Write the failing tests**

```python
class OrroCheckVerifyTest(unittest.TestCase):
    def _run_check(self, tmp, checks):
        root = Path(tmp)
        repo = root / "repo"; repo.mkdir(); _seed_repo(repo)
        argv = ["orro", "check", "--repo", str(repo), "--home", str(root / "home"),
                "--run-dir", str(root / "run"), "--no-review", "--json"]
        for c in checks:
            argv += ["--check", c]
        return _run(argv), root

    def test_passing_check_yields_pass_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            (code, payload, err), root = self._run_check(tmp, ["true"])
            self.assertEqual(code, 0, err)
            self.assertNotIn("Traceback", err)
            self.assertEqual(payload["kind"], "orro-companion-manifest")
            self.assertEqual(payload["scope"], "state-verified")
            self.assertIs(payload["reviewed_work_execution_observed"], False)
            self.assertIs(payload["verification_checks_executed_observed"], True)
            self.assertEqual(payload["execution_adapter_lanes_spawned"], 0)
            self.assertEqual(payload["verdict_ref"]["decision"], "pass")
            self.assertNotIn("review_ref", payload)
            manifest = json.loads((root / "run" / "companion-manifest.json").read_text())
            self.assertEqual(manifest["verdict_ref"]["decision"], "pass")

    def test_failing_check_yields_blocked_verdict_exit_2(self):
        # A failing --check is a FIRST-CLASS blocked verdict, NOT an infra blocker:
        # proofrun exits nonzero but STILL seals team-ledger.json, and proofcheck
        # STILL writes proofcheck-verdict.json with decision "blocked-explicit".
        # (Empirically confirmed 2026-07-19; witnessd ef0c32c.)
        with tempfile.TemporaryDirectory() as tmp:
            (code, payload, err), root = self._run_check(tmp, ["false"])
            self.assertEqual(code, 2, err)
            self.assertNotIn("Traceback", err)
            self.assertEqual(payload["kind"], "orro-companion-manifest")  # NOT a blocker
            self.assertIn(payload["verdict_ref"]["decision"], {"blocked", "blocked-explicit"})
            self.assertIs(payload["reviewed_work_execution_observed"], False)
            self.assertTrue((root / "run" / "companion-manifest.json").is_file())
```

- [ ] **Step 2: Run to verify they fail**

Run: `PYTHONPATH=../depone PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest tests.test_orro_check.OrroCheckVerifyTest -v`
Expected: FAIL — `NotImplementedError`.

- [ ] **Step 3: Implement the verify half + manifest**

Replace the `raise NotImplementedError` in `_cmd_orro_check` with the verify pipeline. Full module additions:

```python
import io
from contextlib import redirect_stdout, redirect_stderr

from witnessd.cli._output import _invoke_cli_capture, _write_json_file, _hash_file


def _invoke_phase(argv: list[str]) -> tuple[int, object, str]:
    try:
        code, stdout, stderr = _invoke_cli_capture(argv)
    except Exception as exc:  # noqa: BLE001 - never leak a phase traceback
        return 1, {}, str(exc)
    try:
        payload = json.loads(stdout) if stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    return code, payload, stderr.strip()


def _resolve_base(repo: Path, base: str | None) -> str:
    if base:
        return base
    try:
        head = _invoke_cli_capture  # placeholder to keep import; see below
    except Exception:
        pass
    import subprocess
    try:
        ref = subprocess.run(
            ["git", "-C", str(repo), "symbolic-ref", "--quiet",
             "refs/remotes/origin/HEAD"],
            capture_output=True, text=True, check=False)
        name = ref.stdout.strip().rsplit("/", 1)[-1]
        return name or "main"
    except Exception:  # noqa: BLE001
        return "main"


def _assert_no_execution_adapter(role_lane_plan_path: Path) -> None:
    plan = json.loads(role_lane_plan_path.read_text(encoding="utf-8"))
    for lane in plan.get("lanes", []):
        if not isinstance(lane, dict):
            continue
        if str(lane.get("adapter")) != "shell":
            raise RuntimeError(
                f"ERR_ORRO_CHECK_EXECUTION_LANE_FORBIDDEN: lane "
                f"{lane.get('lane_id')!r} has non-shell adapter "
                f"{lane.get('adapter')!r}")


def _cmd_orro_check(args: argparse.Namespace) -> int:
    checks = list(getattr(args, "check", None) or [])
    if not checks:
        return _emit_blocker(_structured_error(
            code="ERR_ORRO_CHECK_NO_CHECKS_DECLARED",
            message="orro check requires at least one --check command",
            reason="checks define what 'verified' means and cannot be inferred",
            required_input_or_grant="--check '<cmd>' (repeatable)",
            next_command="python3 -m orro check --check '<cmd>' --repo <repo>",
        ))

    repo = Path(args.repo).resolve(strict=False) if args.repo else Path.cwd()
    home = Path(args.home).resolve(strict=False) if args.home else repo / ".witnessd"
    run_dir = Path(args.run_dir).resolve(strict=False) if args.run_dir else home / "companion-run"
    run_dir.mkdir(parents=True, exist_ok=True)
    sandbox = run_dir / "sandbox"
    base = _resolve_base(repo, args.base)
    goal = f"Review the changes on HEAD relative to {base} without editing files"

    # PROVISION home (Task 0: proofrun/proofcheck require it). Mirror flow.py:147.
    code, _, err = _invoke_phase(["init", "--home", str(home), "--repo", str(repo)])
    if code != 0:
        return _emit_blocker(_structured_error(
            code="ERR_ORRO_CHECK_INIT_BLOCKED",
            message="companion could not provision home", reason=err or "init returned nonzero",
            required_input_or_grant="ensure the pinned Depone is provisionable (see orro init)",
            next_command="python3 -m orro init --home <home> --repo <repo>"))

    verify_wp = run_dir / "verify-workflow-plan.json"
    verify_rlp = run_dir / "verify-role-lane-plan.json"
    verdict_path = run_dir / "proofcheck-verdict.json"

    code, _, err = _invoke_phase([
        "flowplan", goal, "--root", str(repo), "--profile", "verification-only",
        "--out", str(verify_wp), "--role-lanes-out", str(verify_rlp),
        "--lane-adapter", "shell",
        *sum((["--check", c] for c in checks), []), "--json",
    ])
    if code != 0:
        return _emit_blocker(_structured_error(
            code="ERR_ORRO_CHECK_FLOWPLAN_BLOCKED",
            message="verification flowplan failed", reason=err or "flowplan returned nonzero",
            required_input_or_grant="resolve the reported flowplan blocker",
            next_command="python3 -m orro flowplan ... --profile verification-only"))

    _assert_no_execution_adapter(verify_rlp)  # zero-execution invariant (Task 3 hardens tests)

    # CRITICAL (empirically confirmed 2026-07-19): a FAILING --check makes proofrun
    # exit nonzero but it STILL seals team-ledger.json (verdict "blocked-explicit").
    # A failing check is a first-class BLOCKED VERDICT, not an infra blocker — so
    # proofrun's exit code is NOT the discriminator. Only treat it as an infra
    # blocker when NO team-ledger.json was sealed.
    team_ledger = run_dir / "team-ledger.json"
    proofrun_code, _, proofrun_err = _invoke_phase([
        "proofrun", goal, "--repo", str(repo), "--home", str(home),
        "--workflow-plan", str(verify_wp), "--role-lane-plan", str(verify_rlp),
        "--adapter", "shell", "--runner-sandbox", str(sandbox),
        "--run-dir", str(run_dir), "--json",
    ])
    if not team_ledger.is_file():
        return _emit_blocker(_structured_error(
            code="ERR_ORRO_CHECK_PROOFRUN_BLOCKED",
            message="verification proofrun sealed no evidence",
            reason=proofrun_err or "proofrun returned nonzero without sealing team-ledger.json",
            required_input_or_grant="resolve the reported proofrun blocker",
            next_command="python3 -m orro proofrun ..."))

    # proofcheck ALSO exits nonzero for a blocked verdict, but STILL writes
    # proofcheck-verdict.json with a readable decision. Read the decision; only
    # treat it as an infra blocker when Depone produced no usable verdict.
    _, verdict_payload, verdict_err = _invoke_phase([
        "proofcheck", "--evidence-dir", str(run_dir), "--home", str(home),
        "--out", str(verdict_path), "--json",
    ])
    decision = verdict_payload.get("decision") if isinstance(verdict_payload, dict) else None
    if decision not in {"pass", "blocked", "blocked-explicit"} or not verdict_path.is_file():
        return _emit_blocker(_structured_error(
            code="ERR_ORRO_CHECK_PROOFCHECK_BLOCKED",
            message="Depone produced no usable verdict",
            reason=verdict_err or f"proofcheck returned an unusable decision: {decision!r}",
            required_input_or_grant="resolve the reported Depone/proofcheck blocker",
            next_command="python3 -m orro proofcheck ..."))
    # `decision` is Depone's RAW verdict (pass | blocked | blocked-explicit) — kept
    # verbatim in verdict_ref (honest; do not relabel). Companion pass iff "pass".

    review_ref = None  # set in Task 4
    manifest = {
        "kind": "orro-companion-manifest",
        "scope": "state-verified-and-reviewed" if not args.no_review else "state-verified",
        "reviewed_work_execution_observed": False,
        "verification_checks_executed_observed": True,
        "execution_adapter_lanes_spawned": 0,
        "verdict_ref": {
            "path": str(verdict_path), "sha256": _hash_file(verdict_path),
            "decision": decision,
        },
        "boundary": {
            "reviewed_work_execution_observed": False,
            "raises_assurance": False,
            "approves_merge": False,
            "review_is_advisory": True,
        },
    }
    if review_ref is not None:
        manifest["review_ref"] = review_ref
    manifest_path = run_dir / "companion-manifest.json"
    _write_json_file(manifest_path, manifest)

    if args.json:
        print(json.dumps(manifest, sort_keys=True))
    else:
        _print_human_summary(manifest)  # Task 6
    return 0 if decision == "pass" else 2
```

(For Task 2, temporarily stub `_print_human_summary` as `def _print_human_summary(m): pass` — Task 6 fills it. `--no-review` is honored here; Task 4 adds the review branch. The `_resolve_base` `head` placeholder line is dead scaffolding — delete it; the real logic is the `subprocess` git call.)

- [ ] **Step 4: Run to verify pass**

Run: `PYTHONPATH=../depone PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest tests.test_orro_check.OrroCheckVerifyTest -v`
Expected: PASS (both tests).

- [ ] **Step 5: Commit**

```bash
git add witnessd/cli/companion.py tests/test_orro_check.py
git commit -m "feat: orro check verify half + companion manifest (#78)"
```

---

## Task 3: Zero-execution invariant has teeth (mutation-proof)

`_assert_no_execution_adapter` already runs in Task 2. This task adds a direct unit test proving it rejects a non-shell adapter, so a future flowplan regression that emits an AI lane is caught.

**Files:**
- Modify: `tests/test_orro_check.py`

- [ ] **Step 1: Write the failing test**

```python
class ZeroExecutionInvariantTest(unittest.TestCase):
    def test_non_shell_adapter_is_rejected(self):
        from witnessd.cli.companion import _assert_no_execution_adapter
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / "rlp.json"
            plan.write_text(json.dumps({"lanes": [
                {"lane_id": "x", "adapter": "codex", "region": ["."]}]}))
            with self.assertRaises(RuntimeError) as ctx:
                _assert_no_execution_adapter(plan)
            self.assertIn("ERR_ORRO_CHECK_EXECUTION_LANE_FORBIDDEN", str(ctx.exception))

    def test_shell_only_plan_passes(self):
        from witnessd.cli.companion import _assert_no_execution_adapter
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / "rlp.json"
            plan.write_text(json.dumps({"lanes": [
                {"lane_id": "x", "adapter": "shell", "region": []}]}))
            _assert_no_execution_adapter(plan)  # no raise
```

- [ ] **Step 2: Run — expect PASS** (function exists from Task 2)

Run: `PYTHONPATH=../depone PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest tests.test_orro_check.ZeroExecutionInvariantTest -v`
Expected: PASS.

- [ ] **Step 3: Mutation check (prove teeth)**

Temporarily change `_assert_no_execution_adapter` to `return` immediately. Re-run Step 2 → `test_non_shell_adapter_is_rejected` must FAIL. Revert the mutation. (Do not commit the mutation.)

- [ ] **Step 4: Commit**

```bash
git add tests/test_orro_check.py
git commit -m "test: zero-execution invariant rejects non-shell adapters (#78)"
```

---

## Task 4: REVIEW half (advisory) + `review_ref`

Adds the read-only review lane and attaches `review_ref` (advisory) to the manifest. Review never changes exit code.

**Files:**
- Modify: `witnessd/cli/companion.py`
- Modify: `tests/test_orro_check.py`

- [ ] **Step 1: Write the failing test (fake agy)**

Copy the `_fake_agy(directory)` helper from `tests/test_orro_review.py:41-78` verbatim into `tests/test_orro_check.py` (it writes an executable `bin/agy` that emits the `WITNESSD_AGY_CONTEXT`/`WITNESSD_AGY_COMPLETE` sentinels and does not write files).

```python
class OrroCheckReviewTest(unittest.TestCase):
    def test_review_attaches_advisory_ref_without_changing_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"; repo.mkdir(); _seed_repo(repo)
            bindir = root / "bin"; bindir.mkdir()
            fake_agy = _fake_agy(bindir)
            code, payload, err = _run([
                "orro", "check", "--repo", str(repo), "--home", str(root / "home"),
                "--run-dir", str(root / "run"), "--check", "true",
                "--reviewer", "agy", "--reviewer-binary", str(fake_agy), "--json",
            ])
            self.assertEqual(code, 0, err)
            self.assertNotIn("Traceback", err)
            self.assertEqual(payload["scope"], "state-verified-and-reviewed")
            self.assertEqual(payload["verdict_ref"]["decision"], "pass")
            self.assertIn("review_ref", payload)
            self.assertIs(payload["review_ref"]["advisory"], True)
            self.assertTrue((root / "run" / "orro-review-summary.json").is_file())
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONPATH=../depone PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest tests.test_orro_check.OrroCheckReviewTest -v`
Expected: FAIL — no `review_ref` (review branch not implemented).

- [ ] **Step 3: Implement the review branch**

Before building the manifest, add:

```python
    review_ref = None
    if not args.no_review:
        reviewer = args.reviewer
        reviewer_binary = args.reviewer_binary or reviewer
        review_wp = run_dir / "review-workflow-plan.json"
        review_rlp = run_dir / "review-role-lane-plan.json"
        code, _, err = _invoke_phase([
            "flowplan", goal, "--root", str(repo), "--profile", "review-only",
            "--out", str(review_wp), "--role-lanes-out", str(review_rlp),
            "--lane-adapter", reviewer, "--model-policy", "default", "--json",
        ])
        if code != 0:
            return _emit_verdict_with_blocker(  # verdict is known; review could not plan
                manifest_partial(decision, verdict_path),
                _structured_error(
                    code="ERR_ORRO_CHECK_REVIEW_PLAN_BLOCKED",
                    message="review flowplan failed", reason=err or "flowplan nonzero",
                    required_input_or_grant="resolve the reported flowplan blocker",
                    next_command="python3 -m orro check --no-review ..."))
        rc, review_payload, rerr = _invoke_phase([
            "orro-review", "--repo", str(repo), "--home", str(home),
            "--role-lane-plan", str(review_rlp), "--run-dir", str(run_dir),
            f"--{reviewer}-binary", reviewer_binary, "--json",
        ])
        review_summary = run_dir / "orro-review-summary.json"
        if rc != 0 or not review_summary.is_file():
            return _emit_verdict_with_blocker(  # Task 5 defines ERR_ORRO_CHECK_REVIEWER_UNAVAILABLE
                manifest_partial(decision, verdict_path),
                _structured_error(
                    code="ERR_ORRO_CHECK_REVIEWER_UNAVAILABLE",
                    message=f"reviewer '{reviewer}' could not run",
                    reason=rerr or "review adapter returned nonzero or produced no summary",
                    required_input_or_grant=f"install/authenticate {reviewer}, or pass --no-review",
                    next_command="python3 -m orro check --no-review ..."))
        review_ref = {
            "path": str(review_summary), "sha256": _hash_file(review_summary),
            "advisory": True,
        }
```

Add small helpers `manifest_partial(decision, verdict_path)` (returns the verify-only manifest dict) and `_emit_verdict_with_blocker(manifest, error)` (prints `{"kind": "orro-companion-result", "decision": "blocked", "verdict_ref": manifest["verdict_ref"], "error": error}`, returns 2). Refactor the manifest builder from Task 2 into `manifest_partial` so both paths share it.

- [ ] **Step 4: Run to verify pass**

Run: `PYTHONPATH=../depone PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest tests.test_orro_check.OrroCheckReviewTest -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add witnessd/cli/companion.py tests/test_orro_check.py
git commit -m "feat: orro check advisory review half + review_ref (#78)"
```

---

## Task 5: Reviewer-unavailable blocker (honest, not silent skip)

`ERR_ORRO_CHECK_REVIEWER_UNAVAILABLE` is emitted in Task 4. This task adds a pre-check via `shutil.which` for a clean blocker when the reviewer binary is absent, and a test.

**Files:**
- Modify: `witnessd/cli/companion.py`
- Modify: `tests/test_orro_check.py`

- [ ] **Step 1: Write the failing test**

```python
class ReviewerUnavailableTest(unittest.TestCase):
    def test_missing_reviewer_binary_blocks_and_reports_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"; repo.mkdir(); _seed_repo(repo)
            code, payload, err = _run([
                "orro", "check", "--repo", str(repo), "--home", str(root / "home"),
                "--run-dir", str(root / "run"), "--check", "true",
                "--reviewer", "agy",
                "--reviewer-binary", str(root / "does-not-exist-agy"), "--json",
            ])
            self.assertEqual(code, 2, err)
            self.assertNotIn("Traceback", err)
            self.assertEqual(payload["decision"], "blocked")
            self.assertEqual(payload["error"]["code"], "ERR_ORRO_CHECK_REVIEWER_UNAVAILABLE")
            self.assertEqual(payload["verdict_ref"]["decision"], "pass")  # verdict still reported
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONPATH=../depone PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest tests.test_orro_check.ReviewerUnavailableTest -v`
Expected: it may already pass via the Task 4 `rc != 0` path, OR fail if the missing binary raises before the summary check. Add the pre-check to guarantee the clean blocker.

- [ ] **Step 3: Add the `shutil.which` pre-check**

At the top of the review branch (before flowplan review):

```python
        import shutil
        reviewer_binary = args.reviewer_binary or reviewer
        resolved = reviewer_binary if Path(reviewer_binary).exists() else shutil.which(reviewer_binary)
        if not resolved:
            return _emit_verdict_with_blocker(
                manifest_partial(decision, verdict_path),
                _structured_error(
                    code="ERR_ORRO_CHECK_REVIEWER_UNAVAILABLE",
                    message=f"reviewer '{reviewer}' binary not found: {reviewer_binary}",
                    reason="review was requested but the reviewer could not be located; "
                           "silently skipping the review would misrepresent the result",
                    required_input_or_grant=f"install/authenticate {reviewer}, or pass --no-review",
                    next_command="python3 -m orro check --no-review ..."))
```

- [ ] **Step 4: Run to verify pass**

Run: `PYTHONPATH=../depone PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest tests.test_orro_check.ReviewerUnavailableTest -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add witnessd/cli/companion.py tests/test_orro_check.py
git commit -m "feat: orro check reviewer-unavailable blocker (no silent skip) (#78)"
```

---

## Task 6: Human output UX + `--json`

Non-JSON output distinguishes VERIFICATION / REVIEWED / BOUNDARY per spec §5.

**Files:**
- Modify: `witnessd/cli/companion.py`
- Modify: `tests/test_orro_check.py`

- [ ] **Step 1: Write the failing test**

```python
class OrroCheckHumanOutputTest(unittest.TestCase):
    def test_human_output_labels_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"; repo.mkdir(); _seed_repo(repo)
            out, errbuf = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(errbuf):
                code = main(["orro", "check", "--repo", str(repo),
                             "--home", str(root / "home"), "--run-dir", str(root / "run"),
                             "--check", "true", "--no-review"])
            text = out.getvalue()
            self.assertEqual(code, 0, errbuf.getvalue())
            self.assertIn("VERIFICATION", text)
            self.assertIn("NOT observed-executed", text)
            self.assertIn("0 execution-adapter lanes", text)
```

- [ ] **Step 2: Run to verify it fails** (Task 2 stubbed `_print_human_summary` as `pass`)

Expected: FAIL — assertion on "VERIFICATION" not found.

- [ ] **Step 3: Implement `_print_human_summary`**

```python
def _print_human_summary(manifest: dict[str, object]) -> None:
    verdict = manifest["verdict_ref"]["decision"]
    dot = "● pass" if verdict == "pass" else "● blocked"
    print("orro check — evidence & review for work you already drove\n")
    print(f"  VERIFICATION   (Depone verdict, deterministic)   {dot}")
    if "review_ref" in manifest:
        print("  REVIEWED   (advisory — not part of verdict)")
        print(f"    → {manifest['review_ref']['path']}")
    print("  BOUNDARY")
    print("    reviewed work was NOT observed-executed · "
          "0 execution-adapter lanes · does not approve merge")
    print(f"\n  verdict: {verdict}")
```

- [ ] **Step 4: Run to verify pass**

Run: `PYTHONPATH=../depone PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest tests.test_orro_check.OrroCheckHumanOutputTest -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add witnessd/cli/companion.py tests/test_orro_check.py
git commit -m "feat: orro check human-readable output (#78)"
```

---

## Task 7: Full-suite green + self-test + revalidators

**Files:** none (verification task).

- [ ] **Step 1: Run the whole witnessd suite (clean-ish env)**

Run:
```bash
cd /home/ubuntu/moonweave/witnessd
PYTHONPATH=../depone PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -p 'test_*.py'
```
**Do NOT expect a clean "OK" locally.** This local multi-repo env has ~7 pre-existing
failures unrelated to this work (packaging/editable-install, portable-export fixtures,
non-repo-cwd, w16 merge — all red on `main` too; see [[cleanenv-verification]]). The gate
is **no NEW failures vs the `main` baseline**: run the identical suite on `main`
(`git checkout main` → run → `git checkout` back), diff the FAIL/ERROR sets, and confirm
the only delta is zero. CI is the true ground truth. (2026-07-19: this caught 2 real
regressions — the command-surface tests in Task 8 — that a `| tail` pipeline had masked
because the pipeline exit code was `tail`'s, not unittest's. Capture the full log and read
unittest's own `Ran N … FAILED/OK` line.)

- [ ] **Step 2: Self-test + revalidators (match CI job 2)**

Run:
```bash
PYTHONPATH=../depone WITNESSD_DEPONE_ROOT=../depone /usr/bin/python3 -m witnessd self-test --all
for s in scripts/revalidate_*.py; do PYTHONPATH=../depone WITNESSD_DEPONE_ROOT=../depone /usr/bin/python3 "$s" || echo "FAIL $s"; done
```
Expected: no failures.

- [ ] **Step 3: Live smoke (real tools, not `true`/`false`)**

Run in a throwaway git repo with a real check:
```bash
python3 -m orro check --check 'python3 -c "print(1)"' --no-review --json --repo <tmp-repo> --home <tmp-home> --run-dir <tmp-run>
```
Expected JSON: `reviewed_work_execution_observed:false`, `verification_checks_executed_observed:true`, `execution_adapter_lanes_spawned:0`, `verdict_ref.decision:"pass"`. Then flip the check to a failing command → exit 2, `decision:"blocked"`.

- [ ] **Step 4: Commit (if any fixes)**

```bash
git add -A && git commit -m "test: full suite + smoke green for orro check (#78)"
```

---

## Task 8: Docs + command-surface sync (CONTRACT — all surfaces must agree)

**CRITICAL (learned 2026-07-19):** ORRO enforces a command-surface contract via two
tests. Adding a command means updating **every** surface, not just CLAUDE.md, or these
fail:
- `tests/test_orro_public_surface_docs.py::test_public_surface_tables_match_skill_and_real_cli` — asserts the ORRO command table in **SKILL.md == CLAUDE.md == README.md**, and that every documented command appears in the **`orro --help`** usage list (`orro/__main__.py` `ORRO_HELP`).
- `tests/test_orro_command_surface.py::test_recognized_commands_keep_existing_normalization` — asserts `ORRO_COMMAND_MAP` equals a hardcoded `expected` dict.

**Files (all required):**
- `witnessd/CLAUDE.md` — Public names table row + one paragraph.
- `SKILL.md` — same table row (insert after the `orro review` row).
- `README.md` — same table row (insert after the `orro review` row).
- `orro/__main__.py` — add `check` to the `ORRO_HELP` usage `{...}` braces (after `review`) **and** a `check` line in the "public commands:" body.
- `tests/test_orro_command_surface.py` — add `"check": "orro-check",` to the `expected` dict.

- [ ] **Step 1: Add the identical Public names row to CLAUDE.md, SKILL.md, README.md**

```
| `orro check` | companion: deterministic verify (Depone verdict) + read-only review (advisory); spawns zero execution-adapter lanes; does not claim observed execution |
```

- [ ] **Step 2: One-paragraph description** in `witnessd/CLAUDE.md` below the table, mirroring the existing `orro review` paragraph: not proof of the reviewed work's execution; `reviewed_work_execution_observed:false`; review is advisory (`review_is_advisory:true`); handoff still requires a passing bound proofcheck verdict.

- [ ] **Step 3: Update `orro/__main__.py` `ORRO_HELP`** — add `check` to the usage braces after `review` (`...,report,review,check,auto,team,doctor,engine-lock}`) and a body line:
```
  check        companion: verify (Depone verdict) + read-only review; not observed execution
```

- [ ] **Step 4: Update the surface test** — add `"check": "orro-check",` to `expected` in `tests/test_orro_command_surface.py`.

- [ ] **Step 5: Verify the two surface tests pass**

Run: `PYTHONPATH=../depone WITNESSD_DEPONE_ROOT=../depone /usr/bin/python3 -m unittest tests.test_orro_command_surface tests.test_orro_public_surface_docs -v`
Expected: OK.

- [ ] **Step 6: Commit**

```bash
git add witnessd/CLAUDE.md SKILL.md README.md orro/__main__.py tests/test_orro_command_surface.py
git commit -m "docs: document orro check across all command surfaces (#78)"
```

---

## Phase 2: Release & ORRO re-pin (post-merge, cross-repo)

Not TDD tasks — the standard release + re-pin sequence, executed after the witnessd PR merges to main.

- [ ] Open the witnessd PR from the feature branch; confirm CI (CI + CodeQL) green.
- [ ] Merge to `main`; bump witnessd version (`setup.py`, 1 line); tag `v<next>` at the full merge SHA (`git rev-parse`); `git push` tag → `release.yml` (SLSA + PyPI Trusted Publishing).
- [ ] Re-pin ORRO to the new witnessd release following the PR #79 diff (~23 files: engine-lock / compat-matrix / release-manifest / packaging + version + docs). Depone pin unchanged (`1932f00`). Pre-delete local `.ruff_cache/`. Verify: CI checkers (16) + `orro_e2e_smoke.py --require-lock-match --allow-network` → `decision:pass, lock matched`.
- [ ] Close ORRO #78 with a keyword (`Closes #78`) in the ORRO re-pin PR.

---

## Self-Review

**1. Spec coverage:**
- One command + structured blockers → Tasks 1, 2, 5 (`_structured_error`, `reason/required_input_or_grant/next_command`). ✓
- Never launches an execution adapter → verification-only shell lanes (Task 2) + `_assert_no_execution_adapter` invariant (Tasks 2/3). ✓
- verify=verdict / review=advisory → verdict from proofcheck (Task 2), `review_ref.advisory:true`, review never changes exit (Task 4). ✓
- Honest labels (`reviewed_work_execution_observed`, `verification_checks_executed_observed`, `execution_adapter_lanes_spawned`) → manifest in Task 2, asserted in tests. ✓
- Output distinguishes state-verified vs execution-observed → Task 6. ✓
- Reviewer-unavailable not silently skipped → Task 5. ✓
- `--base` shapes review prompt (not a computed diff) → `_resolve_base` + synthesized `goal` (Task 2). ✓
- Depone unchanged / witnessd-only + re-pin → Phase 2. ✓
- Testing plan (clean-env, mutation, live smoke) → Tasks 0/3/7. ✓

**2. Placeholder scan:** No "TBD"/"handle edge cases". Every code step shows code; every run step shows the command + expected result. The one forward-reference (`_print_human_summary` stubbed in Task 2, filled in Task 6) is explicitly called out. The `_resolve_base` `head` scaffolding line is flagged for deletion.

**3. Type/name consistency:** `_cmd_orro_check`, `_invoke_phase`, `_assert_no_execution_adapter`, `manifest_partial`, `_emit_verdict_with_blocker`, `_print_human_summary`, `_emit_blocker` — used consistently across tasks. Manifest keys (`kind`, `scope`, `reviewed_work_execution_observed`, `verification_checks_executed_observed`, `execution_adapter_lanes_spawned`, `verdict_ref`, `review_ref`, `boundary`) match the spec §3 verbatim. Error codes (`ERR_ORRO_CHECK_NO_CHECKS_DECLARED`, `_INIT_BLOCKED`, `_FLOWPLAN_BLOCKED`, `_PROOFRUN_BLOCKED` [only when no team-ledger sealed], `_PROOFCHECK_BLOCKED` [only when Depone gives no usable verdict], `_REVIEW_PLAN_BLOCKED`, `_REVIEWER_UNAVAILABLE`, `_EXECUTION_LANE_FORBIDDEN`) are consistent.

**Correction (2026-07-19, after codex STOP on a real contradiction):** a failing `--check` is a first-class BLOCKED VERDICT, not an infra blocker. proofrun/proofcheck both exit nonzero for a blocked check but still seal `team-ledger.json` / write `proofcheck-verdict.json` (decision `blocked-explicit`). The discriminator is artifact existence, not exit code. `verdict_ref.decision` carries Depone's raw decision verbatim; companion exit is `0` iff `pass`. This replaced the original "proofrun nonzero → immediate blocker" logic.

**Task 0 result (done, committed witnessd `12d0300`):** the raw path
`init → flowplan --profile verification-only --check → proofrun --adapter shell → proofcheck`
reaches Depone `decision:pass` with **no `--write-scope`** and **no AI adapter**. The one
finding folded back into this plan: the companion **must run `init` first**
(`["init","--home",home,"--repo",repo]`) to provision home, because
`proofcheck` → `_depone_subprocess_env` → `validate_depone_pin(home)` requires
`home/provision.json`. `orro flow` already does this via its init phase (flow.py:147); the
companion mirrors it (added to the argv section and Task 2). Error code list also includes
`ERR_ORRO_CHECK_INIT_BLOCKED`.
