#!/usr/bin/env python3
"""Check that this repo stays an ORRO product/distribution wrapper repo."""

from __future__ import annotations

import json
import re
import subprocess
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
    "docs/orro-strategic-review-spec.md": (
        "로컬 `.omx/` 디렉터리는 agent workflow runtime state다",
        "tracked `.omx` 파일은 contract violation",
    ),
    "docs/README.md": (
        "[Assurance Threat Model](assurance/threat-model.md)",
        "[Long-Automation Maturity Gates](assurance/long-automation-maturity.md)",
    ),
}
SECURITY_REQUIRED_PHRASES = (
    INVARIANT,
    "ORRO does not execute commands",
    "ORRO does not verify evidence",
    "ORRO does not approve merges",
    "ORRO does not raise assurance",
    "ORRO does not implement proofrun or proofcheck",
    "ORRO does not own Depone verifier semantics or witnessd runtime semantics",
    "Do not paste secrets",
    "Prefer evidence paths and redacted excerpts",
    "Secret-looking material is not proof",
    "Replay or stale evidence is an unresolved risk",
)
CONTRIBUTING_REQUIRED_PHRASES = (
    INVARIANT,
    "Humans retain judgment",
    "handoff is not approval",
    "report is not proof",
    "Docs, schemas, contract checks, wrapper/distribution metadata, and harness-surface changes are in scope",
    "Engine, verifier, runtime, proofrun, proofcheck, scheduler, observer, fan-in, and package publish changes are out of scope",
    "No new dependencies",
)
INTEGRATION_POLICY_REQUIRED_PHRASES = (
    "MCP is an integration surface, not ORRO's core architecture.",
    "Plugin-first, MCP-optional.",
    "MCP is allowed as an adapter, not as a dependency of ORRO core.",
    "Prompts/resources before tools.",
    "On-demand before always-on.",
    "Long automation is checkpoint expansion, not trust expansion.",
    "Prompt profile hash does not prove model compliance.",
)
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
LOCAL_ARTIFACT_DIRS = {
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
}


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
    artifact_rows: dict[str, str],
    artifact: str,
    required_tokens: tuple[str, ...],
) -> None:
    if artifact not in artifact_rows:
        fail(f"{label} must define artifact semantics for {artifact!r}")
    row_text = artifact_rows[artifact]
    missing = [token for token in required_tokens if token not in row_text]
    if missing:
        fail(f"{label} artifact {artifact!r} missing semantic tokens: {missing}")


def strategic_artifact_table_rows(label: str, haystack: str) -> dict[str, str]:
    start_marker = "Artifact meaning table:"
    header = "| Artifact | Means | Does not mean |"
    end_marker = "문서 작성 규칙:"
    start = haystack.find(start_marker)
    if start == -1:
        fail(f"{label} must contain {start_marker!r}")
    table_start = haystack.find(header, start)
    if table_start == -1:
        fail(f"{label} must contain {header!r}")
    table_end = haystack.find(end_marker, table_start)
    if table_end == -1:
        fail(f"{label} must contain {end_marker!r} after artifact table")

    rows: dict[str, str] = {}
    for raw_line in haystack[table_start:table_end].splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        if line == header:
            continue
        cells = [normalize_contract_text(cell) for cell in line.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        if len(cells) != 3:
            fail(f"{label} artifact table row must have exactly three cells: {line!r}")
        artifact = cells[0]
        if artifact in rows:
            fail(f"{label} artifact table must define {artifact!r} exactly once")
        rows[artifact] = " | ".join(cells)
    return rows


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
    workflow_reference = read_text("docs/workflow-reference.md")
    require_contains("docs/workflow-reference.md", workflow_reference, "review-only")
    require_contains("docs/workflow-reference.md", workflow_reference, "Gemini")
    require_contains("docs/workflow-reference.md", workflow_reference, "Antigravity")
    require_contains("docs/workflow-reference.md", workflow_reference, "--lane-adapter agy")
    require_contains("docs/workflow-reference.md", workflow_reference, "read-only review lane")
    require_contains("docs/workflow-reference.md", workflow_reference, "review-receipt")
    require_contains("docs/workflow-reference.md", workflow_reference, "not proofcheck")
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
    artifact_rows = strategic_artifact_table_rows(path, text)
    unexpected_artifacts = sorted(set(artifact_rows) - set(STRATEGIC_REVIEW_ARTIFACT_REQUIREMENTS))
    if unexpected_artifacts:
        fail(f"{path} artifact table contains unexpected artifacts: {unexpected_artifacts}")
    for artifact, required_tokens in STRATEGIC_REVIEW_ARTIFACT_REQUIREMENTS.items():
        require_artifact_semantics(path, artifact_rows, artifact, required_tokens)


def check_assurance_docs() -> None:
    for path, phrases in ASSURANCE_DOC_REQUIRED_PHRASES.items():
        if not (ROOT / path).is_file():
            fail(f"required assurance doc missing: {path}")
        text = read_text(path)
        for phrase in phrases:
            require_contains(path, text, phrase)


def check_security_contribution_docs() -> None:
    required_docs = {
        "SECURITY.md": SECURITY_REQUIRED_PHRASES,
        "CONTRIBUTING.md": CONTRIBUTING_REQUIRED_PHRASES,
    }
    for path, phrases in required_docs.items():
        if not (ROOT / path).is_file():
            fail(f"required boundary doc missing: {path}")
        text = read_text(path)
        for phrase in phrases:
            require_contains_normalized(path, text, phrase)


def check_integration_surface_policy() -> None:
    path = "docs/integrations/integration-surface-policy.md"
    if not (ROOT / path).is_file():
        fail(f"required integration surface policy missing: {path}")
    text = read_text(path)
    for phrase in INTEGRATION_POLICY_REQUIRED_PHRASES:
        require_contains_normalized(path, text, phrase)


def check_strategic_review_corpus() -> None:
    path = "docs/assurance/strategic-review-corpus.v0.json"
    if not (ROOT / path).is_file():
        fail(f"required strategic review corpus missing: {path}")

    data = load_json(path)
    if data.get("kind") != "orro-strategic-review-corpus":
        fail("strategic review corpus kind must be orro-strategic-review-corpus")
    if data.get("schema_version") != "0.1":
        fail("strategic review corpus schema_version must be 0.1")

    boundary = data.get("orro_boundary", {})
    for key in ("approves_merge", "contains_engine_logic", "executes_commands", "raises_assurance", "verifies_evidence"):
        if boundary.get(key) is not False:
            fail(f"strategic review corpus orro_boundary.{key} must be false")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 5:
        fail("strategic review corpus must contain at least five cases")

    allowed_artifacts = {
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
    allowed_rejections = {
        "handoff is not approval",
        "report is not proof",
        INVARIANT,
        "engine-lock is distribution metadata, not proof",
        "long automation is checkpoint expansion, not trust expansion",
        "secret-looking content must not be repeated as proof",
        "replay or stale evidence is unresolved risk, not pass",
        "MCP tool result is not proofrun, proofcheck, approval, verifier truth, or assurance",
        "prompt profile hash is text identity, not model compliance guarantee",
        "integration policy is boundary guidance, not proof, approval, verifier truth, or assurance",
    }
    required_risks = {
        "handoff_approval_confusion",
        "report_proof_confusion",
        "verifier_boundary_confusion",
        "engine_lock_assurance_confusion",
        "long_automation_trust_confusion",
        "prompt_injection_approval_confusion",
        "secret_leakage_confusion",
        "replay_stale_evidence_confusion",
        "mcp_tool_result_proof_confusion",
        "prompt_profile_compliance_confusion",
        "integration_surface_assurance_confusion",
        "mcp_connected_trust_confusion",
    }
    allowed_risks = set(required_risks)
    seen_ids: set[str] = set()
    seen_risks: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            fail(f"strategic review corpus case {index} must be an object")
        for key in ("id", "artifact", "risk", "phrase", "must_reject_as"):
            if not isinstance(case.get(key), str) or not case[key].strip():
                fail(f"strategic review corpus case {index}.{key} must be a non-empty string")

        case_id = case["id"]
        if case_id in seen_ids:
            fail(f"strategic review corpus duplicate case id: {case_id}")
        seen_ids.add(case_id)

        if case["artifact"] not in allowed_artifacts:
            fail(f"strategic review corpus case {index}.artifact is not allowed")
        if case["risk"] not in allowed_risks:
            fail(f"strategic review corpus case {index}.risk is not allowed")
        if case["must_reject_as"] not in allowed_rejections:
            fail(f"strategic review corpus case {index}.must_reject_as is not an allowed doctrine rejection")
        if case["phrase"] == case["must_reject_as"]:
            fail(f"strategic review corpus case {index} phrase must differ from rejection")

        seen_risks.add(case["risk"])

    missing = sorted(required_risks - seen_risks)
    if missing:
        fail(f"strategic review corpus missing required risks: {missing}")


def check_language_boundary_lint() -> None:
    required_paths = [
        "scripts/check_orro_language_boundaries.py",
        "tests/fixtures/language-boundaries/cases.v0.json",
    ]
    for path in required_paths:
        if not (ROOT / path).is_file():
            fail(f"required language boundary lint file missing: {path}")

    result = subprocess.run(
        [sys.executable, "scripts/check_orro_language_boundaries.py"],
        cwd=ROOT,
        check=False,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        fail(
            "language boundary lint must pass bundled fixtures\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )


def check_corpus_lint_coverage() -> None:
    """Couple the strategic-review corpus to the executable language-boundary lint.

    Every corpus negative-case phrase must be rejected by at least one lint rule,
    and every corpus artifact must be recognized by the lint. This stops the wording
    gate from silently falling behind the corpus as new risk classes are added.
    """
    import importlib

    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    lint = importlib.import_module("check_orro_language_boundaries")

    corpus = load_json("docs/assurance/strategic-review-corpus.v0.json")
    for case in corpus["cases"]:
        artifact = case["artifact"]
        phrase = case["phrase"]
        if artifact not in lint.ALLOWED_ARTIFACTS:
            fail(
                f"strategic review corpus artifact {artifact!r} (case {case['id']}) "
                "is not a recognized language-boundary lint artifact"
            )
        if not lint.lint_text(artifact, phrase):
            fail(
                f"strategic review corpus case {case['id']} phrase is not rejected by "
                f"any language-boundary lint rule: {phrase!r}"
            )


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
        "scripts/check_orro_release_state.py",
        "scripts/check_compatibility_matrix.py",
        "scripts/update_orro_engine_lock.py",
        "release/orro-release-manifest.v0.json",
        "release/compatibility-matrix.v0.json",
        "docs/engine-lock-update-process.md",
        "docs/compatibility-matrix.md",
        "docs/os-support.md",
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
    require_contains("release docs", lower_text, "`orro` 0.2.6 is published on pypi")


def check_os_support_matrix() -> None:
    path = ROOT / "docs" / "os-support.md"
    if not path.is_file():
        fail("required OS support matrix missing: docs/os-support.md")
    text = path.read_text(encoding="utf-8")
    lower_text = text.lower()
    require_contains("OS support matrix", text, "Linux")
    require_contains("OS support matrix", lower_text, "required")
    require_contains("OS support matrix", text, "macOS")
    require_contains("OS support matrix", lower_text, "smoke")
    require_contains("OS support matrix", text, "Windows")
    require_contains("OS support matrix", lower_text, "unsupported")
    require_contains("OS support matrix", text, "A2")
    require_contains("OS support matrix", lower_text, "capability-gated")
    require_contains("OS support matrix", lower_text, "posix")


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
    require_contains("packaging decision docs", text, "`orro` 0.2.6 is published on PyPI")
    require_contains("packaging decision docs", text, "witnessd>=2.4.0,<3.0.0")
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
    require_contains("command migration docs", text, "owned-thin-wrapper")
    require_contains("command migration docs", text, "delegates to witnessd")
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
    if plan.get("owns_orro_command_now") is not True:
        fail("command migration plan must claim ORRO owns orro now")
    if plan.get("adds_orro_console_script") is not True:
        fail("command migration plan must add orro console script now")
    dry_run = plan.get("dry_run_harness")
    if not isinstance(dry_run, dict):
        fail("command migration plan must describe the dry-run harness")
    if dry_run.get("script") != "scripts/check_orro_command_migration_dry_run.py":
        fail("command migration dry-run harness script metadata is wrong")
    if dry_run.get("changes_committed_package_metadata") is not True:
        fail("command migration metadata must record committed package metadata change")
    if dry_run.get("proves_command_ownership") is not True:
        fail("command migration metadata must record command ownership proof")


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
        "scripts/orro_build_backend.py",
        "scripts/check_orro_version_coherence.py",
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

    ci_text = read_text(".github/workflows/ci.yml")
    compile_line = next((line for line in ci_text.splitlines() if "python3 -m py_compile" in line), "")
    if "scripts/orro_build_backend.py" not in compile_line:
        fail("CI script compilation must include scripts/orro_build_backend.py")
    require_contains(
        "CI build-backend self-test",
        ci_text,
        "python3 scripts/orro_build_backend.py --self-test",
    )
    for script in (
        "check_orro_wrapper_install.py",
        "check_orro_wrapper_distribution.py",
        "check_orro_command_migration_dry_run.py",
    ):
        require_contains(
            "CI isolated build network gating",
            ci_text,
            f"python3 scripts/{script} --json --allow-network",
        )

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
    require_contains("wrapper docs", text, "ORRO-owned `orro` command")
    require_contains("wrapper docs", text, "compatibility alias")
    require_contains("wrapper docs", text, "witnessd-hosted")
    require_contains("wrapper docs", text, INVARIANT)


def check_no_engine_code() -> None:
    tracked_omx = subprocess.check_output(
        ["git", "ls-files", ".omx"],
        cwd=ROOT,
        encoding="utf-8",
    ).splitlines()
    if tracked_omx:
        fail(f".omx is local workflow runtime state and must not be tracked: {tracked_omx}")

    for path in ROOT.iterdir():
        if path.name in {".git", ".omx"} or path.name in LOCAL_ARTIFACT_DIRS:
            continue
        if path.name.endswith(".egg-info"):
            continue
        if path.is_dir() and path.name in FORBIDDEN_TOP_LEVEL_DIRS:
            fail(f"forbidden engine/runtime directory present: {path.name}")
        if path.is_dir() and path.name not in ALLOWED_TOP_LEVEL_DIRS:
            fail(f"unexpected top-level directory present: {path.name}")

    for path in ROOT.rglob("*"):
        if (
            ".git" in path.parts
            or ".omx" in path.parts
            or any(part in LOCAL_ARTIFACT_DIRS for part in path.parts)
            or any(part.endswith(".egg-info") for part in path.parts)
            or not path.is_file()
        ):
            continue
        relative = path.relative_to(ROOT)
        parts = relative.parts
        if not parts:
            continue
        top = parts[0]
        lower_name = path.name.lower()
        suffix = path.suffix.lower()
        if suffix in {".py", ".sh"} and top not in {"scripts", "src"}:
            fail(f"executable source outside scripts is not allowed: {relative}")
        if top == "src" and (len(parts) < 2 or parts[1] != "orro_wrapper"):
            fail(f"unexpected package source present: {relative}")
        if top == "scripts" and path.name not in {
            "bootstrap_orro.py",
            "check_orro_language_boundaries.py",
            "check_no_bidi_controls.py",
            "check_orro_assurance_contract_fixtures.py",
            "check_orro_fallback_policy.py",
            "check_orro_command_migration.py",
            "check_orro_command_migration_dry_run.py",
            "check_orro_packaging_decision.py",
            "check_orro_repo_contract.py",
            "check_orro_release_manifest.py",
            "check_orro_release_state.py",
            "check_compatibility_matrix.py",
            "check_orro_version_coherence.py",
            "check_orro_wrapper.py",
            "check_orro_wrapper_install.py",
            "check_orro_wrapper_distribution.py",
            "orro_build_backend.py",
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
    check_security_contribution_docs()
    check_integration_surface_policy()
    check_strategic_review_corpus()
    check_language_boundary_lint()
    check_corpus_lint_coverage()
    check_packaging_drafts()
    check_engine_lock_example()
    check_e2e_engine_lock()
    check_e2e_docs()
    check_release_discipline()
    check_os_support_matrix()
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
