#!/usr/bin/env python3
"""Check ORRO pinned-engine fallback policy metadata."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "packaging/pinned-engine-fallback-policy.v0.json"
DOC_PATH = ROOT / "docs/pinned-engine-fallback.md"
INVARIANT = "Depone verifies; witnessd executes; ORRO exposes the workflow"


def fail(message: str) -> None:
    print(f"ORRO fallback policy violation: {message}", file=sys.stderr)
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


def check_policy() -> None:
    policy = load_json(POLICY_PATH)
    if policy.get("kind") != "orro-pinned-engine-fallback-policy":
        fail("fallback policy kind must be orro-pinned-engine-fallback-policy")
    if policy.get("schema_version") != "0.1":
        fail("fallback policy schema_version must be 0.1")
    if policy.get("default_behavior") != "fail-closed":
        fail("fallback policy default_behavior must be fail-closed")

    forbidden = policy.get("forbidden_responses")
    if not isinstance(forbidden, list):
        fail("forbidden_responses must be a list")
    rendered_forbidden = "\n".join(str(item) for item in forbidden)
    for phrase in (
        "silently use latest main",
        "rewrite engine lock during bootstrap",
        "run proofrun to test availability",
        "run proofcheck to test availability",
        "treat fallback as proof",
    ):
        require_contains("forbidden_responses", rendered_forbidden, phrase)

    boundary = policy.get("boundary")
    if not isinstance(boundary, dict):
        fail("boundary must be an object")
    for key in (
        "contains_engine_logic",
        "auto_selects_engine_commits",
        "rewrites_engine_lock",
        "executes_proofrun",
        "verifies_evidence",
        "approves_merge",
        "raises_assurance",
    ):
        require_false(boundary, key)
    for key in ("depone_verifies", "witnessd_executes", "orro_exposes_workflow"):
        require_true(boundary, key)
    for key in ("not_proof", "not_verifier_truth", "not_package_publish"):
        if policy.get(key) is not True:
            fail(f"{key} must be true")


def check_docs() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    require_contains("fallback docs", text, INVARIANT)
    require_contains("fallback docs", text, "Fail closed")
    require_contains("fallback docs", text, "not proof")
    require_contains("fallback docs", text, "not verifier truth")
    require_contains("fallback docs", text, "silently use latest `main`")
    require_contains("fallback docs", text, "intentional engine-lock update PR")
    require_contains("fallback docs", text, "proofrun")
    require_contains("fallback docs", text, "proofcheck")
    require_contains("fallback docs", text, "`orro` 0.2.5 is published on PyPI")


def main() -> int:
    if not POLICY_PATH.is_file():
        fail(f"missing fallback policy: {POLICY_PATH.relative_to(ROOT)}")
    if not DOC_PATH.is_file():
        fail(f"missing fallback doc: {DOC_PATH.relative_to(ROOT)}")
    check_policy()
    check_docs()
    print("ORRO fallback policy: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
