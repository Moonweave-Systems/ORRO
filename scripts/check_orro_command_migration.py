#!/usr/bin/env python3
"""Check ORRO command ownership migration is complete and thin."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "packaging/command-migration-plan.v0.json"
DOC_PATH = ROOT / "docs/orro-command-migration.md"
DRY_RUN_PATH = ROOT / "scripts/check_orro_command_migration_dry_run.py"
INVARIANT = "Depone verifies; witnessd executes; ORRO exposes the workflow"


def fail(message: str) -> None:
    print(f"ORRO command migration violation: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as exc:
        fail(f"could not read {path}: {exc}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON in {path}: {exc}")
    if not isinstance(payload, dict):
        fail(f"{path} must contain a JSON object")
    return payload


def require_contains(label: str, haystack: str, needle: str) -> None:
    if needle not in haystack:
        fail(f"{label} must contain {needle!r}")


def require_false(label: str, value: Any) -> None:
    if value is not False:
        fail(f"{label} must be false")


def require_true(label: str, value: Any) -> None:
    if value is not True:
        fail(f"{label} must be true")


def check_orro_console_script_owned() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    setup_cfg = (ROOT / "setup.cfg").read_text(encoding="utf-8")
    require_contains("pyproject.toml", pyproject, 'orro = "orro_wrapper.cli:main"')
    require_contains("pyproject.toml", pyproject, 'orro-wrapper = "orro_wrapper.cli:main"')
    require_contains("setup.cfg", setup_cfg, "orro = orro_wrapper.cli:main")
    require_contains("setup.cfg", setup_cfg, "orro-wrapper = orro_wrapper.cli:main")


def check_plan() -> None:
    plan = load_json(PLAN_PATH)
    if plan.get("kind") != "orro-command-migration-plan":
        fail("command migration plan kind must be orro-command-migration-plan")
    if plan.get("schema_version") != "0.1":
        fail("command migration plan schema_version must be 0.1")
    if plan.get("status") != "complete":
        fail("command migration status must be complete")
    if plan.get("current_command_source") != "ORRO-owned orro console script":
        fail("current command source must be ORRO-owned")
    if plan.get("current_wrapper_command") != "orro-wrapper":
        fail("current wrapper command must be orro-wrapper")
    if plan.get("target_command") != "orro":
        fail("target command must be orro")
    if plan.get("migration_phase") != "owned-thin-wrapper":
        fail("migration phase must be owned-thin-wrapper")
    require_true("owns_orro_command_now", plan.get("owns_orro_command_now"))
    require_true("adds_orro_console_script", plan.get("adds_orro_console_script"))
    require_false("requires_separate_migration_wave", plan.get("requires_separate_migration_wave"))
    for list_key in ("compatibility_requirements", "required_preconditions", "forbidden_this_phase"):
        value = plan.get(list_key)
        if not isinstance(value, list) or not value:
            fail(f"{list_key} must be a non-empty list")

    boundary = plan.get("boundary")
    if not isinstance(boundary, dict):
        fail("boundary must be an object")
    for key in (
        "contains_engine_logic",
        "implements_proofrun",
        "implements_proofcheck",
        "owns_orro_command_now",
        "approves_merge",
        "raises_assurance",
    ):
        if key == "owns_orro_command_now":
            require_true(f"boundary.{key}", boundary.get(key))
        else:
            require_false(f"boundary.{key}", boundary.get(key))
    for key in ("depone_verifies", "witnessd_executes", "orro_exposes_workflow"):
        require_true(f"boundary.{key}", boundary.get(key))
    for key in ("not_proof", "not_verifier_truth", "not_package_publish"):
        require_true(key, plan.get(key))

    dry_run = plan.get("dry_run_harness")
    if not isinstance(dry_run, dict):
        fail("dry_run_harness must be an object")
    if dry_run.get("script") != "scripts/check_orro_command_migration_dry_run.py":
        fail("dry_run_harness.script must point at the dry-run checker")
    if dry_run.get("simulated_entry_point") != "orro = orro_wrapper.cli:main":
        fail("dry_run_harness.simulated_entry_point must document the temporary orro entry point")
    for key in (
        "temporary_source_copy_only",
        "checks_current_package_first",
        "checks_simulated_migration",
        "checks_rollback",
        "requires_wrapper_thinness",
    ):
        require_true(f"dry_run_harness.{key}", dry_run.get(key))
    require_true("dry_run_harness.changes_committed_package_metadata", dry_run.get("changes_committed_package_metadata"))
    require_false("dry_run_harness.publishes_package", dry_run.get("publishes_package"))
    require_true("dry_run_harness.proves_command_ownership", dry_run.get("proves_command_ownership"))


def check_docs() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    require_contains("command migration doc", text, INVARIANT)
    require_contains("command migration doc", text, "owned-thin-wrapper")
    require_contains("command migration doc", text, "ORRO-owned")
    require_contains("command migration doc", text, "orro-wrapper")
    require_contains("command migration doc", text, "delegates to witnessd")
    require_contains("command migration doc", text, "not proof")
    require_contains("command migration doc", text, "not verifier truth")
    require_contains("command migration doc", text, "not package publish")
    require_contains("command migration doc", text, "does not verify evidence")
    require_contains("command migration doc", text, "Superflow")
    require_contains("command migration doc", text, "dry-run harness")
    require_contains("command migration doc", text, "temporary source copy")
    require_contains("command migration doc", text, "rollback simulation")
    require_contains("command migration doc", text, "dry-run metadata is not proof")
    require_contains("command migration doc", text, "scripts/check_orro_command_migration_dry_run.py")


def main() -> int:
    if not PLAN_PATH.is_file():
        fail(f"missing command migration plan: {PLAN_PATH.relative_to(ROOT)}")
    if not DOC_PATH.is_file():
        fail(f"missing command migration doc: {DOC_PATH.relative_to(ROOT)}")
    if not DRY_RUN_PATH.is_file():
        fail(f"missing command migration dry-run harness: {DRY_RUN_PATH.relative_to(ROOT)}")
    check_plan()
    check_docs()
    check_orro_console_script_owned()
    print("ORRO command migration: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
