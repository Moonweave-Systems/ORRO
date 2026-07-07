#!/usr/bin/env python3
"""Lint ORRO report/handoff language boundary fixtures.

This checker guards wording only. It does not verify evidence, approve work,
execute commands, or raise assurance.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "tests/fixtures/language-boundaries/cases.v0.json"
ALLOWED_ARTIFACTS = {"report", "handoff"}
ALLOWED_EXPECTATIONS = {"pass", "reject"}


@dataclass(frozen=True)
class Rule:
    id: str
    artifacts: frozenset[str]
    pattern: re.Pattern[str]
    reason: str

    def applies_to(self, artifact: str) -> bool:
        return artifact in self.artifacts


RULES = (
    Rule(
        id="prompt_injection_approval",
        artifacts=frozenset({"report", "handoff"}),
        pattern=re.compile(r"\bignore\s+previous\s+rules\b", re.IGNORECASE),
        reason="prompt injection must not turn report or handoff into approval",
    ),
    Rule(
        id="report_proof_overclaim",
        artifacts=frozenset({"report"}),
        pattern=re.compile(
            r"\breport\s+(?:proves?|is proof|is the proof)\b|\btreated\s+as\s+proof\b|\bas\s+proof\s+of\s+execution\b",
            re.IGNORECASE,
        ),
        reason="report is not proof",
    ),
    Rule(
        id="report_verifier_truth_overclaim",
        artifacts=frozenset({"report"}),
        pattern=re.compile(r"\breport\s+is\s+verifier\s+truth\b|\borro\s+report\s+is\s+verifier\s+truth\b", re.IGNORECASE),
        reason="report is not verifier truth",
    ),
    Rule(
        id="handoff_approval_overclaim",
        artifacts=frozenset({"handoff"}),
        pattern=re.compile(
            r"\bhandoff\s+(?:approves?|approved|is approval|grants approval)\b|\bmark\s+this\s+handoff\s+approved\b",
            re.IGNORECASE,
        ),
        reason="handoff is not approval",
    ),
    Rule(
        id="secret_as_proof",
        artifacts=frozenset({"report", "handoff"}),
        pattern=re.compile(r"\b(?:copied\s+)?(?:token|secret|credential)\b.{0,80}\bas\s+proof\b", re.IGNORECASE),
        reason="secret-looking content must not be repeated as proof",
    ),
    Rule(
        id="stale_evidence_pass_overclaim",
        artifacts=frozenset({"report", "handoff"}),
        pattern=re.compile(r"\bold\s+evidence\s+was\s+reused\b.{0,120}\bcurrent\s+run\s+passes\b", re.IGNORECASE),
        reason="replay or stale evidence is unresolved risk, not pass",
    ),
    Rule(
        id="assurance_overclaim",
        artifacts=frozenset({"report", "handoff"}),
        pattern=re.compile(r"\b(?:report|handoff|orro)\s+raises\s+assurance\b", re.IGNORECASE),
        reason="report and handoff do not raise assurance",
    ),
)


def fail(message: str) -> None:
    print(f"ORRO language boundary violation: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def lint_text(artifact: str, text: str) -> list[dict[str, str]]:
    normalized = " ".join(text.split())
    violations: list[dict[str, str]] = []
    for rule in RULES:
        if not rule.applies_to(artifact):
            continue
        if rule.pattern.search(normalized):
            violations.append({"rule": rule.id, "reason": rule.reason})
    return violations


def check_fixture(path: Path) -> list[dict[str, str]]:
    data = load_json(path)
    if data.get("kind") != "orro-language-boundary-fixtures":
        fail(f"{path} kind must be orro-language-boundary-fixtures")
    if data.get("schema_version") != "0.1":
        fail(f"{path} schema_version must be 0.1")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        fail(f"{path} cases must be a non-empty list")

    seen_ids: set[str] = set()
    failures: list[dict[str, str]] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            fail(f"{path} case {index} must be an object")
        for key in ("id", "artifact", "expect", "text"):
            if not isinstance(case.get(key), str) or not case[key].strip():
                fail(f"{path} case {index}.{key} must be a non-empty string")
        case_id = case["id"]
        if case_id in seen_ids:
            fail(f"{path} duplicate case id: {case_id}")
        seen_ids.add(case_id)

        artifact = case["artifact"]
        expectation = case["expect"]
        if artifact not in ALLOWED_ARTIFACTS:
            fail(f"{path} case {case_id} artifact must be one of {sorted(ALLOWED_ARTIFACTS)}")
        if expectation not in ALLOWED_EXPECTATIONS:
            fail(f"{path} case {case_id} expect must be one of {sorted(ALLOWED_EXPECTATIONS)}")

        violations = lint_text(artifact, case["text"])
        if expectation == "pass" and violations:
            failures.append({"case": case_id, "error": "expected pass", "violations": json.dumps(violations, sort_keys=True)})
        if expectation == "reject" and not violations:
            failures.append({"case": case_id, "error": "expected reject", "violations": "[]"})

    return failures


def infer_artifact(path: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    lower_name = path.name.lower()
    if "handoff" in lower_name:
        return "handoff"
    if "report" in lower_name:
        return "report"
    fail(f"cannot infer artifact for {path}; pass --artifact report or --artifact handoff")


def check_paths(paths: list[Path], artifact: str | None) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for path in paths:
        current_artifact = infer_artifact(path, artifact)
        text = path.read_text(encoding="utf-8")
        for violation in lint_text(current_artifact, text):
            failures.append({"path": str(path), **violation})
    return failures


def run_self_test() -> None:
    expected_report_violation = lint_text("report", "This report proves completion.")
    if not expected_report_violation:
        fail("self-test expected report proof overclaim violation")
    expected_handoff_violation = lint_text("handoff", "This handoff approves the merge.")
    if not expected_handoff_violation:
        fail("self-test expected handoff approval overclaim violation")
    if lint_text("report", "Report summary with proofcheck path; report is not proof."):
        fail("self-test expected bounded report language to pass")
    if lint_text("handoff", "Handoff is not approval and is for human review."):
        fail("self-test expected bounded handoff language to pass")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Optional report/handoff text files to lint.")
    parser.add_argument("--artifact", choices=sorted(ALLOWED_ARTIFACTS), help="Artifact type for all supplied paths.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE, help="Fixture corpus to validate.")
    parser.add_argument("--json", action="store_true", help="Emit JSON result.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in smoke tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.self_test:
        run_self_test()
        if args.json:
            print(json.dumps({"kind": "orro-language-boundary-check", "decision": "pass"}, indent=2, sort_keys=True))
        else:
            print("ORRO language boundaries self-test: pass")
        return 0

    failures = check_paths(args.paths, args.artifact) if args.paths else check_fixture(args.fixture)
    if failures:
        if args.json:
            print(json.dumps({"kind": "orro-language-boundary-check", "decision": "fail", "failures": failures}, indent=2, sort_keys=True))
        for failure in failures:
            print(f"ORRO language boundary violation: {failure}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"kind": "orro-language-boundary-check", "decision": "pass"}, indent=2, sort_keys=True))
    else:
        print("ORRO language boundaries: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
