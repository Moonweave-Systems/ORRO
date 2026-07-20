#!/usr/bin/env python3
"""Check ORRO wrapper packaging decision metadata.

This checker validates product/distribution planning only. It does not install,
execute engines, verify evidence, approve merge, or raise assurance.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "packaging/wrapper-package-plan.v0.json"
DOC_PATH = ROOT / "docs/packaging-decision.md"
INVARIANT = "Depone verifies; witnessd executes; ORRO exposes the workflow"
WITNESSD_REQUIREMENT = "witnessd>=2.4.0,<3.0.0"


def fail(message: str) -> None:
    print(f"ORRO packaging decision violation: {message}", file=sys.stderr)
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


def require_false(boundary: dict[str, Any], key: str) -> None:
    if boundary.get(key) is not False:
        fail(f"boundary.{key} must be false")


def require_true(boundary: dict[str, Any], key: str) -> None:
    if boundary.get(key) is not True:
        fail(f"boundary.{key} must be true")


def check_plan() -> None:
    plan = load_json(PLAN_PATH)
    if plan.get("kind") != "orro-wrapper-package-plan":
        fail("wrapper package plan kind must be orro-wrapper-package-plan")
    if plan.get("schema_version") != "0.1":
        fail("wrapper package plan schema_version must be 0.1")
    if plan.get("published_package") is not True:
        fail("wrapper package plan must record the published package")
    if plan.get("published_package_scope") != "product-line":
        fail("wrapper package plan published_package must be scoped to the product line")
    if plan.get("status") != "release-candidate":
        fail("wrapper package plan status must be release-candidate")
    if plan.get("distribution_name") != "orro":
        fail("wrapper package plan distribution_name must be orro")
    if plan.get("source_version") != "0.2.15":
        fail("wrapper package plan source_version must be 0.2.15")
    if plan.get("current_command_source") != "ORRO-owned orro console script":
        fail("current command source must be ORRO-owned")

    engines = plan.get("engine_dependencies")
    if not isinstance(engines, dict):
        fail("engine_dependencies must be an object")
    if engines.get("witnessd", {}).get("repository") != "Moonweave-Systems/witnessd":
        fail("witnessd engine dependency must reference Moonweave-Systems/witnessd")
    if engines.get("witnessd", {}).get("package_requirement") != WITNESSD_REQUIREMENT:
        fail(f"witnessd engine dependency must require {WITNESSD_REQUIREMENT}")
    if engines.get("depone", {}).get("repository") != "Moonweave-Systems/Depone":
        fail("Depone engine dependency must reference Moonweave-Systems/Depone")

    phases = plan.get("phases")
    if not isinstance(phases, list) or not phases:
        fail("phases must be a non-empty list")
    phase_names = {phase.get("phase") for phase in phases if isinstance(phase, dict)}
    for required in ("bootstrap", "thin-wrapper", "published-package"):
        if required not in phase_names:
            fail(f"missing wrapper package phase: {required}")
    for phase in phases:
        if not isinstance(phase, dict):
            fail("each phase must be an object")
        if phase.get("contains_engine_logic") is not False:
            fail(f"phase {phase.get('phase')} must not contain engine logic")

    boundary = plan.get("boundary")
    if not isinstance(boundary, dict):
        fail("boundary must be an object")
    for key in (
        "contains_engine_logic",
        "implements_proofrun",
        "implements_proofcheck",
        "creates_third_engine",
        "approves_merge",
        "raises_assurance",
    ):
        require_false(boundary, key)
    for key in ("published_package", "depone_verifies", "witnessd_executes", "orro_exposes_workflow"):
        require_true(boundary, key)

    for key in ("not_proof", "not_verifier_truth", "not_package_publish"):
        if plan.get(key) is not True:
            fail(f"{key} must be true")


def check_docs() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    require_contains("packaging decision doc", text, INVARIANT)
    require_contains("packaging decision doc", text, "not proof")
    require_contains("packaging decision doc", text, "not verifier truth")
    require_contains("packaging decision doc", text, "not package publish")
    require_contains("packaging decision doc", text, "witnessd-hosted")
    require_contains("packaging decision doc", text, "no engine code")
    require_contains("packaging decision doc", text, "`orro` 0.2.15 is published on PyPI")
    require_contains("packaging decision doc", text, WITNESSD_REQUIREMENT)
    require_contains("packaging decision doc", text, "proofrun")
    require_contains("packaging decision doc", text, "proofcheck")


def main() -> int:
    if not PLAN_PATH.is_file():
        fail(f"missing wrapper package plan: {PLAN_PATH.relative_to(ROOT)}")
    if not DOC_PATH.is_file():
        fail(f"missing packaging decision doc: {DOC_PATH.relative_to(ROOT)}")
    check_plan()
    check_docs()
    print("ORRO packaging decision: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
