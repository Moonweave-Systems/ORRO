#!/usr/bin/env python3
"""Check that this repo stays an ORRO product/distribution wrapper repo."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INVARIANT = "Depone verifies; witnessd executes; ORRO exposes the workflow"
STRATEGIC_REVIEW_REQUIRED_PHRASES = (
    "Verified acceleration, not blind automation",
    INVARIANT,
    "Humans retain judgment",
    "handoff is not approval",
    "report is not proof",
    "long automation is checkpoint expansion, not trust expansion",
)
STRATEGIC_REVIEW_REQUIRED_SECTIONS = (
    "## 1. 총평",
    "## 2. 철학 적합성 점수",
    "## 3. 가장 잘한 점",
    "## 4. 가장 위험한 점",
    "## 5. 작은 설계 리뷰",
    "## 6. 큰 방향 리뷰",
    "## 7. 하네스 설계안",
    "## 8. 품질 하네스",
    "## 9. 효율 측정안",
    "## 10. 긴 자동화 maturity ladder",
    "## 11. 지금 당장 해야 할 P0",
    "## 12. v0.1 전에 해야 할 P1",
    "## 13. 장기 P2/P3",
    "## 14. 문서에 넣을 철학 선언문",
    "## 15. 최종 판단",
)
STRATEGIC_REVIEW_ARTIFACT_REQUIREMENTS = {
    "workflow-plan": ("실행 의도", "proof", "approval", "verifier truth"),
    "proofrun": ("witnessd", "evidence", "proofcheck 통과", "merge approval"),
    "proofcheck-verdict": ("Depone", "verdict", "판단을 포기"),
    "handoff": ("리뷰", "approval", "proof", "release permission"),
    "report": ("요약", "proof", "verifier truth", "approval"),
    "engine-lock": ("pinned engine", "distribution metadata", "assurance", "proof"),
    "release-manifest": ("release candidate metadata", "package publish", "proof", "approval"),
}
ASSURANCE_DOC_REQUIRED_PHRASES = {
    "docs/assurance/threat-model.md": (
        "Prompt Injection",
        "Secret Leakage",
        "Replay or Stale Evidence",
        "Handoff Approval Confusion",
        "Report Proof Confusion",
        "handoff is not approval",
        "report is not proof",
        "Humans retain judgment",
        INVARIANT,
    ),
    "docs/assurance/long-automation-maturity.md": (
        "Long-Automation Maturity Gates",
        "Entry criteria",
        "Exit criteria",
        "Must not mean",
        "Long automation is checkpoint expansion, not trust expansion.",
        "Level 6 continuous operation is intentionally not defined",
        "Humans retain judgment",
    ),
    "docs/README.md": (
        "[Assurance Threat Model](assurance/threat-model.md)",
        "[Long-Automation Maturity Gates](assurance/long-automation-maturity.md)",
    ),
}
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_TOP_LEVEL_DIRS = {
    ".github",
    "docs",
    "engine-lock",
    "examples",
    "packaging",
    "release",
    "scripts",
    "src",
    "tests",
}
FORBIDDEN_TOP_LEVEL_DIRS = {
    "depone",
    "Depone",
    "witnessd",
    "scheduler",
    "observer",
    "fan_in",
    "fanin",
}
FORBIDDEN_IMPLEMENTATION_NAMES = (
    "proofcheck",
    "proofrun",
    "scheduler",
    "observer",
    "fan_in",
    "fanin",
)


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load_json(path: str) -> Any:
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.load(handle)


def fail(message: str) -> None:
    print(f"ORRO repo contract violation: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_contains(label: str, haystack: str, needle: str) -> None:
    if needle not in haystack:
        fail(f"{label} must contain {needle!r}")


def require_any_contains(label: str, haystack: str, needles: tuple[str, ...]) -> None:
    if not any(needle in haystack for needle in needles):
        fail(f"{label} must contain one of {needles!r}")


def normalize_contract_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def require_contains_normalized(label: str, haystack: str, needle: str) -> None:
    normalized_haystack = normalize_contract_text(haystack)
    normalized_needle = normalize_contract_text(needle)
    if normalized_needle not in normalized_haystack:
        fail(f"{label} must contain normalized {needle!r}")


def require_artifact_semantics(
    label: str,
    haystack: str,
    artifact: str,
    required_tokens: tuple[str, ...],
) -> None:
    rows = [
        normalize_contract_text(line)
        for line in haystack.splitlines()
        if line.lstrip().startswith("|") and artifact in line
    ]
    if not rows:
        fail(f"{label} must define artifact semantics for {artifact!r}")
    row_text = " ".join(rows)
    missing = [token for token in required_tokens if token not in row_text]
    if missing:
        fail(f"{label} artifact {artifact!r} missing semantic tokens: {missing}")


def combined_text(paths: list[str]) -> str:
    return "\n".join(read_text(path) for path in paths)


def check_readme() -> None:
    readme = read_text("README.md")
    require_contains("README.md", readme, "ORRO = Observed Run & Review Orchestrator")
    require_contains("README.md", readme, INVARIANT)


def check_docs_and_examples() -> None:
    docs = sorted(str(path.relative_to(ROOT)) for path in (ROOT / "docs").glob("*.md"))
    examples = sorted(str(path.relative_to(ROOT)) for path in (ROOT / "examples").glob("*.md"))
    docs_text = combined_text(docs)
    docs_examples_text = combined_text(docs + examples)

    require_contains("docs", docs_text, "not a verifier engine")
    require_contains("docs", docs_text, "not an execution engine")
    require_contains("docs", docs_text, "not a third engine")
    require_contains("docs", docs_text, "Moonweave-Systems/Depone")
    require_contains("docs", docs_text, "Moonweave-Systems/witnessd")

    require_contains("docs/examples", docs_examples_text, "proofcheck")
    require_contains("docs/examples", docs_examples_text, "handoff")
    require_any_contains(
        "docs/examples",
        docs_examples_text,
        ("proofcheck before handoff", "proofcheck` must pass before formal handoff"),
    )
    require_contains("docs/examples", docs_examples_text, "not approval")
    require_contains("docs/examples", docs_examples_text, "Report is summary, not proof")
    require_contains("docs/examples", docs_examples_text, "Engine-lock is distribution metadata, not proof")


def check_strategic_review_spec() -> None:
    path = "docs/orro-strategic-review-spec.md"
    if not (ROOT / path).is_file():
        fail(f"required strategic review spec missing: {path}")
    text = read_text(path)
    for phrase in STRATEGIC_REVIEW_REQUIRED_PHRASES:
        require_contains(path, text, phrase)
    for section in STRATEGIC_REVIEW_REQUIRED_SECTIONS:
        require_contains_normalized(path, text, section)
    require_contains(path, text, "| Artifact | Means | Does not mean |")
    for artifact, required_tokens in STRATEGIC_REVIEW_ARTIFACT_REQUIREMENTS.items():
        require_artifact_semantics(path, text, artifact, required_tokens)


def check_assurance_docs() -> None:
    for path, phrases in ASSURANCE_DOC_REQUIRED_PHRASES.items():
        if not (ROOT / path).is_file():
            fail(f"required assurance doc missing: {path}")
        text = read_text(path)
        for phrase in phrases:
            require_contains(path, text, phrase)


def check_packaging_drafts() -> None:
    for path in (
        "packaging/marketplace-manifest.draft.json",
        "packaging/plugin-manifest.draft.json",
    ):
        data = load_json(path)
        rendered = json.dumps(data, sort_keys=True)
        require_contains(path, rendered, "Moonweave-Systems/witnessd")
        require_contains(path, rendered, "Moonweave-Systems/Depone")
        require_any_contains(path, rendered, ("boundary", "boundary_warning"))
    if not (ROOT / "packaging/wrapper-package-plan.v0.json").is_file():
        fail("required wrapper package plan missing: packaging/wrapper-package-plan.v0.json")
    if not (ROOT / "packaging/pinned-engine-fallback-policy.v0.json").is_file():
        fail("required pinned engine fallback policy missing: packaging/pinned-engine-fallback-policy.v0.json")


def check_engine_lock_example() -> None:
    data = load_json("engine-lock/orro-engine-lock.example.json")
    if data.get("kind") != "orro-engine-lock":
        fail("engine-lock example kind must be orro-engine-lock")
    if data.get("schema_version") != "1.0":
        fail("engine-lock example schema_version must be 1.0")
    if data.get("witnessd", {}).get("repository") != "Moonweave-Systems/witnessd":
        fail("engine-lock example must reference Moonweave-Systems/witnessd")
    if data.get("depone", {}).get("repository") != "Moonweave-Systems/Depone":
        fail("engine-lock example must reference Moonweave-Systems/Depone")
    boundary = data.get("boundary", {})
    for key in ("approves_merge", "raises_assurance", "executes_commands", "verifies_evidence"):
        if boundary.get(key) is not False:
            fail(f"engine-lock boundary.{key} must be false")


def check_e2e_engine_lock() -> None:
    data = load_json("engine-lock/orro-e2e-engine-lock.json")
    if data.get("kind") != "orro-engine-lock":
        fail("e2e engine lock kind must be orro-engine-lock")
    if data.get("schema_version") != "1.0":
        fail("e2e engine lock schema_version must be 1.0")
    engines = {
        "witnessd": "Moonweave-Systems/witnessd",
        "depone": "Moonweave-Systems/Depone",
    }
    for key, repository in engines.items():
        engine = data.get(key, {})
        if engine.get("repository") != repository:
            fail(f"e2e engine lock {key}.repository must be {repository}")
        commit = engine.get("commit")
        if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
            fail(f"e2e engine lock {key}.commit must be a 40-hex commit")
        if commit == "0" * 40:
            fail(f"e2e engine lock {key}.commit must not be the placeholder zero commit")
    boundary = data.get("boundary", {})
    for key in ("approves_merge", "raises_assurance", "executes_commands", "verifies_evidence"):
        if boundary.get(key) is not False:
            fail(f"e2e engine lock boundary.{key} must be false")


def check_e2e_docs() -> None:
    text = combined_text(
        [
            "README.md",
            "docs/e2e-runner.md",
            "docs/e2e-smoke-contract.md",
            "tests/e2e/README.md",
        ]
    )
    require_contains("e2e docs", text, "pinned")
    require_contains("e2e docs", text, "engine lock")
    require_any_contains("e2e docs", text, ("not proof", "not verifier truth"))


def check_release_discipline() -> None:
    required_paths = [
        "scripts/check_orro_release_manifest.py",
        "scripts/update_orro_engine_lock.py",
        "release/orro-release-manifest.v0.json",
        "docs/engine-lock-update-process.md",
        "docs/compatibility-matrix.md",
        ".github/pull_request_template.md",
    ]
    for path in required_paths:
        if not (ROOT / path).is_file():
            fail(f"required release discipline file missing: {path}")

    text = combined_text(
        [
            "README.md",
            "docs/repository-strategy.md",
            "docs/e2e-runner.md",
            "docs/e2e-smoke-contract.md",
            "docs/install.md",
            "docs/engine-contract.md",
            "docs/engine-lock-update-process.md",
            "docs/compatibility-matrix.md",
        ]
    )
    lower_text = text.lower()
    require_contains("release docs", text, "release manifest")
    require_contains("release docs", lower_text, "engine-lock update")
    require_contains("release docs", text, "not proof")
    require_contains("release docs", text, "not verifier truth")
    require_contains("release docs", lower_text, "published orro")
    require_contains("release docs", lower_text, "package remains future work")


def check_bootstrap_discipline() -> None:
    required_paths = [
        "scripts/bootstrap_orro.py",
        "docs/bootstrap.md",
    ]
    for path in required_paths:
        if not (ROOT / path).is_file():
            fail(f"required bootstrap file missing: {path}")

    text = combined_text(
        [
            "README.md",
            "docs/README.md",
            "docs/bootstrap.md",
            "docs/install.md",
            "docs/repository-strategy.md",
            "docs/thin-wrapper-plan.md",
            "docs/e2e-runner.md",
            "docs/engine-lock-update-process.md",
        ]
    )
    require_contains("bootstrap docs", text, "bootstrap is setup/distribution orchestration")
    require_contains("bootstrap docs", text, "setup metadata, not proof")
    require_contains("bootstrap docs", text, "no engine code")
    require_contains("bootstrap docs", text, "witnessd-hosted")
    require_contains("bootstrap docs", text, INVARIANT)


def check_packaging_decision() -> None:
    required_paths = [
        "scripts/check_orro_packaging_decision.py",
        "scripts/check_orro_command_migration.py",
        "scripts/check_orro_command_migration_dry_run.py",
        "docs/packaging-decision.md",
        "docs/orro-command-migration.md",
        "packaging/wrapper-package-plan.v0.json",
        "packaging/command-migration-plan.v0.json",
    ]
    for path in required_paths:
        if not (ROOT / path).is_file():
            fail(f"required packaging decision file missing: {path}")

    text = combined_text(
        [
            "README.md",
            "docs/README.md",
            "docs/packaging-decision.md",
            "docs/repository-strategy.md",
            "docs/thin-wrapper-plan.md",
            "docs/install.md",
        ]
    )
    require_contains("packaging decision docs", text, "packaging decision")
    require_contains("packaging decision docs", text, "not package publish")
    require_contains("packaging decision docs", text, "published ORRO package remains future work")
    require_contains("packaging decision docs", text, "no engine code")
    require_contains("packaging decision docs", text, "witnessd-hosted")
    require_contains("packaging decision docs", text, INVARIANT)


def check_command_migration() -> None:
    text = combined_text(
        [
            "README.md",
            "docs/README.md",
            "docs/orro-command-migration.md",
            "docs/wrapper-distribution.md",
            "docs/packaging-decision.md",
            "docs/repository-strategy.md",
        ]
    )
    require_contains("command migration docs", text, "ORRO-owned `orro` command")
    require_contains("command migration docs", text, "plan-only")
    require_contains("command migration docs", text, "separate migration wave")
    require_contains("command migration docs", text, "must not shadow `orro`")
    require_contains("command migration docs", text, "witnessd-hosted")
    require_contains("command migration docs", text, "not proof")
    require_contains("command migration docs", text, "not package publish")
    require_contains("command migration docs", text, "dry-run harness")
    require_contains("command migration docs", text, "temporary source copy")
    require_contains("command migration docs", text, "rollback simulation")
    require_contains("command migration docs", text, "dry-run metadata is not proof")
    require_contains("command migration docs", text, INVARIANT)

    plan = load_json("packaging/command-migration-plan.v0.json")
    if plan.get("kind") != "orro-command-migration-plan":
        fail("command migration plan kind must be orro-command-migration-plan")
    if plan.get("owns_orro_command_now") is not False:
        fail("command migration plan must not claim ORRO owns orro now")
    if plan.get("adds_orro_console_script") is not False:
        fail("command migration plan must not add orro console script now")
    dry_run = plan.get("dry_run_harness")
    if not isinstance(dry_run, dict):
        fail("command migration plan must describe the dry-run harness")
    if dry_run.get("script") != "scripts/check_orro_command_migration_dry_run.py":
        fail("command migration dry-run harness script metadata is wrong")
    if dry_run.get("changes_committed_package_metadata") is not False:
        fail("command migration dry-run must not change committed package metadata")
    if dry_run.get("proves_command_ownership") is not False:
        fail("command migration dry-run metadata must not claim proof of ownership")


def check_fallback_policy() -> None:
    required_paths = [
        "scripts/check_orro_fallback_policy.py",
        "docs/pinned-engine-fallback.md",
        "packaging/pinned-engine-fallback-policy.v0.json",
    ]
    for path in required_paths:
        if not (ROOT / path).is_file():
            fail(f"required fallback policy file missing: {path}")

    text = combined_text(
        [
            "README.md",
            "docs/README.md",
            "docs/pinned-engine-fallback.md",
            "docs/thin-wrapper-plan.md",
            "docs/bootstrap.md",
            "docs/engine-lock-update-process.md",
        ]
    )
    require_contains("fallback policy docs", text, "Fail closed")
    require_contains("fallback policy docs", text, "pinned engine")
    require_contains("fallback policy docs", text, "not proof")
    require_contains("fallback policy docs", text, "not verifier truth")
    require_contains("fallback policy docs", text, "intentional engine-lock update PR")
    require_contains("fallback policy docs", text, INVARIANT)


def check_wrapper() -> None:
    required_paths = [
        "pyproject.toml",
        "setup.cfg",
        "scripts/check_orro_wrapper.py",
        "scripts/check_orro_wrapper_install.py",
        "scripts/check_orro_wrapper_distribution.py",
        "scripts/check_orro_command_migration.py",
        "docs/thin-wrapper.md",
        "docs/wrapper-distribution.md",
        "docs/orro-command-migration.md",
        "src/orro_wrapper/__init__.py",
        "src/orro_wrapper/__main__.py",
        "src/orro_wrapper/cli.py",
    ]
    for path in required_paths:
        if not (ROOT / path).is_file():
            fail(f"required wrapper file missing: {path}")

    text = combined_text(
        [
            "README.md",
            "docs/README.md",
            "docs/thin-wrapper.md",
            "docs/thin-wrapper-plan.md",
            "docs/packaging-decision.md",
            "docs/wrapper-distribution.md",
            "docs/install.md",
            "docs/repository-strategy.md",
        ]
    )
    require_contains("wrapper docs", text, "orro-wrapper")
    require_contains("wrapper docs", text, "delegates")
    require_contains("wrapper docs", text, "does not implement proofrun")
    require_contains("wrapper docs", text, "does not implement proofcheck")
    require_contains("wrapper docs", text, "install smoke")
    require_contains("wrapper docs", text, "distribution smoke")
    require_contains("wrapper docs", text, "wheel")
    require_contains("wrapper docs", text, "not proof")
    require_contains("wrapper docs", text, "not package publish")
    require_contains("wrapper docs", text, "does not shadow `orro`")
    require_contains("wrapper docs", text, "future migration")
    require_contains("wrapper docs", text, "witnessd-hosted")
    require_contains("wrapper docs", text, INVARIANT)


def check_no_engine_code() -> None:
    for path in ROOT.iterdir():
        if path.name in {".git", ".omx"}:
            continue
        if path.is_dir() and path.name in FORBIDDEN_TOP_LEVEL_DIRS:
            fail(f"forbidden engine/runtime directory present: {path.name}")
        if path.is_dir() and path.name not in ALLOWED_TOP_LEVEL_DIRS:
            fail(f"unexpected top-level directory present: {path.name}")

    for path in ROOT.rglob("*"):
        if ".git" in path.parts or ".omx" in path.parts or "__pycache__" in path.parts or not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        lower_name = path.name.lower()
        suffix = path.suffix.lower()
        if suffix in {".py", ".sh"} and relative.parts[0] not in {"scripts", "src"}:
            fail(f"executable source outside scripts is not allowed: {relative}")
        if relative.parts[0] == "src" and (len(relative.parts) < 2 or relative.parts[1] != "orro_wrapper"):
            fail(f"unexpected package source present: {relative}")
        if relative.parts[0] == "scripts" and path.name not in {
            "bootstrap_orro.py",
            "check_orro_fallback_policy.py",
            "check_orro_command_migration.py",
            "check_orro_command_migration_dry_run.py",
            "check_orro_packaging_decision.py",
            "check_orro_repo_contract.py",
            "check_orro_release_manifest.py",
            "check_orro_wrapper.py",
            "check_orro_wrapper_install.py",
            "check_orro_wrapper_distribution.py",
            "orro_e2e_smoke.py",
            "update_orro_engine_lock.py",
        }:
            fail(f"unexpected script present: {relative}")
        if suffix in {".py", ".sh"} and any(token in lower_name for token in FORBIDDEN_IMPLEMENTATION_NAMES):
            fail(f"forbidden engine implementation-looking file present: {relative}")


def main() -> int:
    check_readme()
    check_docs_and_examples()
    check_strategic_review_spec()
    check_assurance_docs()
    check_packaging_drafts()
    check_engine_lock_example()
    check_e2e_engine_lock()
    check_e2e_docs()
    check_release_discipline()
    check_bootstrap_discipline()
    check_packaging_decision()
    check_command_migration()
    check_fallback_policy()
    check_wrapper()
    check_no_engine_code()
    print("ORRO repo contract: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
