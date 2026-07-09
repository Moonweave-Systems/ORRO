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
# Mirrors the strategic-review-corpus artifact vocabulary
# (docs/assurance/strategic-review-corpus.v0.json). Kept in lockstep by
# check_orro_repo_contract.py::check_corpus_lint_coverage.
ALLOWED_ARTIFACTS = {
    "workflow-plan",
    "proofrun",
    "proofcheck-verdict",
    "handoff",
    "report",
    "engine-lock",
    "release-manifest",
    "mcp-tool-result",
    "prompt-profile-hash",
    "integration-policy",
    "mcp-adapter",
}
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
        artifacts=frozenset({"report", "handoff", "workflow-plan"}),
        pattern=re.compile(r"\bignore\s+previous\s+rules\b", re.IGNORECASE),
        reason="prompt injection must not turn a report, handoff, or plan into approval",
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
        id="orro_verifier_overclaim",
        artifacts=frozenset({"report", "handoff"}),
        pattern=re.compile(r"\borro\s+verif(?:ies|ied|y|ying)\b", re.IGNORECASE),
        reason="Depone verifies; witnessd executes; ORRO exposes the workflow",
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
    Rule(
        id="engine_lock_assurance_overclaim",
        artifacts=frozenset({"report", "handoff", "engine-lock"}),
        pattern=re.compile(r"\bengine[\s-]lock\s+raises\s+assurance\b", re.IGNORECASE),
        reason="engine-lock is distribution metadata, not proof",
    ),
    Rule(
        id="long_automation_trust_overclaim",
        artifacts=frozenset({"report", "handoff"}),
        pattern=re.compile(r"\blong\s+automation\b(?:(?!\b(?:not|never|no|nor)\b|n't).){0,40}\btrust\s+is\s+expanded\b", re.IGNORECASE),
        reason="long automation is checkpoint expansion, not trust expansion",
    ),
    Rule(
        id="mcp_tool_result_proof_overclaim",
        artifacts=frozenset({"report", "handoff", "mcp-tool-result"}),
        pattern=re.compile(
            r"\bmcp\s+tool\s+result\b\s+(?:is\s+(?:a\s+)?(?:proofcheck|proofrun|proof|approval|verifier\s+truth|assurance)\b|proves?\b|approves?\b|raises\s+assurance\b)",
            re.IGNORECASE,
        ),
        reason="MCP tool result is not proofrun, proofcheck, approval, verifier truth, or assurance",
    ),
    Rule(
        id="prompt_profile_compliance_overclaim",
        artifacts=frozenset({"report", "handoff", "prompt-profile-hash"}),
        pattern=re.compile(r"\bprompt[\s-]+profile(?:[\s-]+hash)?\b\s+(?:proves?|guarantees?)\b", re.IGNORECASE),
        reason="prompt profile hash is text identity, not model compliance guarantee",
    ),
    Rule(
        id="integration_surface_assurance_overclaim",
        artifacts=frozenset({"report", "handoff", "integration-policy"}),
        pattern=re.compile(
            r"\bintegration\s+(?:policy|surface)\b\s+(?:raises\s+assurance|proves?\b|guarantees?\s+(?:trust|safety|assurance))",
            re.IGNORECASE,
        ),
        reason="integration policy is boundary guidance, not proof, approval, verifier truth, or assurance",
    ),
    Rule(
        id="mcp_connected_trust_overclaim",
        artifacts=frozenset({"report", "handoff", "mcp-adapter"}),
        pattern=re.compile(
            r"\bmcp\b(?:(?!\b(?:not|never|no|nor)\b|n't).){0,40}\b(?:adapter|connected|connection|server)\b(?:(?!\b(?:not|never|no|nor)\b|n't).){0,60}\b(?:long\s+automation\s+is\s+safer|makes\s+long\s+automation\s+safe|expands\s+trust|trust\s+is\s+expanded)\b",
            re.IGNORECASE,
        ),
        reason="long automation is checkpoint expansion, not trust expansion",
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
    # Existing report/handoff overclaims must reject.
    if not lint_text("report", "This report proves completion."):
        fail("self-test expected report proof overclaim violation")
    if not lint_text("handoff", "This handoff approves the merge."):
        fail("self-test expected handoff approval overclaim violation")
    # Strategic-corpus overclaims must reject.
    if not lint_text("report", "ORRO verified the evidence."):
        fail("self-test expected ORRO verifier overclaim violation")
    if not lint_text("engine-lock", "The engine lock raises assurance."):
        fail("self-test expected engine-lock assurance overclaim violation")
    if not lint_text("mcp-tool-result", "The MCP tool result is proofcheck."):
        fail("self-test expected MCP tool result proof overclaim violation")
    if not lint_text("prompt-profile-hash", "The prompt profile hash proves the model followed the rules."):
        fail("self-test expected prompt profile hash compliance overclaim violation")
    if not lint_text("integration-policy", "Using the ORRO integration surface raises assurance."):
        fail("self-test expected integration surface assurance overclaim violation")
    if not lint_text("mcp-adapter", "Because the MCP adapter was connected, long automation is safer."):
        fail("self-test expected MCP-connected trust overclaim violation")
    # Bounded language must pass.
    if lint_text("report", "Report summary with proofcheck path; report is not proof."):
        fail("self-test expected bounded report language to pass")
    if lint_text("handoff", "Handoff is not approval and is for human review."):
        fail("self-test expected bounded handoff language to pass")
    if lint_text("mcp-tool-result", "MCP tool result is bounded adapter output, not proofrun, proofcheck, approval, verifier truth, or assurance."):
        fail("self-test expected bounded MCP tool result language to pass")
    if lint_text("integration-policy", "Integration policy is boundary guidance, not runtime enforcement by itself."):
        fail("self-test expected bounded integration policy language to pass")
    if lint_text("report", "Long automation does not mean trust is expanded."):
        fail("self-test expected negated long-automation wording to pass")
    if lint_text("mcp-adapter", "Connecting the MCP server does not mean long automation is safer."):
        fail("self-test expected negated mcp-connected wording to pass")


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
