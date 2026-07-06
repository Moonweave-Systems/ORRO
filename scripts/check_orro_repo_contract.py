#!/usr/bin/env python3
"""Check that this repo stays an ORRO product/distribution wrapper repo."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INVARIANT = "Depone verifies; witnessd executes; ORRO exposes the workflow"
ALLOWED_TOP_LEVEL_DIRS = {
    ".github",
    "docs",
    "engine-lock",
    "examples",
    "packaging",
    "scripts",
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


def check_no_engine_code() -> None:
    for path in ROOT.iterdir():
        if path.name == ".git":
            continue
        if path.is_dir() and path.name in FORBIDDEN_TOP_LEVEL_DIRS:
            fail(f"forbidden engine/runtime directory present: {path.name}")
        if path.is_dir() and path.name not in ALLOWED_TOP_LEVEL_DIRS:
            fail(f"unexpected top-level directory present: {path.name}")

    for path in ROOT.rglob("*"):
        if ".git" in path.parts or "__pycache__" in path.parts or not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        lower_name = path.name.lower()
        suffix = path.suffix.lower()
        if suffix in {".py", ".sh"} and relative.parts[0] != "scripts":
            fail(f"executable source outside scripts is not allowed: {relative}")
        if relative.parts[0] == "scripts" and path.name not in {
            "check_orro_repo_contract.py",
            "orro_e2e_smoke.py",
        }:
            fail(f"unexpected script present: {relative}")
        if suffix in {".py", ".sh"} and any(token in lower_name for token in FORBIDDEN_IMPLEMENTATION_NAMES):
            fail(f"forbidden engine implementation-looking file present: {relative}")


def main() -> int:
    check_readme()
    check_docs_and_examples()
    check_packaging_drafts()
    check_engine_lock_example()
    check_no_engine_code()
    print("ORRO repo contract: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
