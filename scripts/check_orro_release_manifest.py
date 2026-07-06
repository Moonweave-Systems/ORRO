#!/usr/bin/env python3
"""Validate the ORRO release manifest metadata contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "release" / "orro-release-manifest.v0.json"
ENGINE_LOCK_PATH = ROOT / "engine-lock" / "orro-e2e-engine-lock.json"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
ZERO_COMMIT = "0" * 40
REQUIRED_SURFACES = {
    "advise",
    "flowplan",
    "proofrun",
    "proofcheck",
    "handoff",
    "report",
}


def fail(message: str) -> None:
    print(f"ORRO release manifest violation: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as exc:
        fail(f"could not read {path.relative_to(ROOT)}: {exc}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON in {path.relative_to(ROOT)}: {exc}")


def require_object(label: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    return value


def require_bool_false(label: str, value: Any) -> None:
    if value is not False:
        fail(f"{label} must be false")


def require_bool_true(label: str, value: Any) -> None:
    if value is not True:
        fail(f"{label} must be true")


def require_commit(label: str, value: Any, *, allow_zero: bool = False) -> str:
    if not isinstance(value, str) or not COMMIT_RE.fullmatch(value):
        fail(f"{label} must be a 40-hex commit")
    if not allow_zero and value == ZERO_COMMIT:
        fail(f"{label} must not be the placeholder zero commit")
    return value


def main() -> int:
    manifest = require_object("release manifest", load_json(MANIFEST_PATH))
    engine_lock = require_object("engine lock", load_json(ENGINE_LOCK_PATH))

    if manifest.get("kind") != "orro-release-manifest":
        fail("kind must be orro-release-manifest")
    if manifest.get("schema_version") != "0.1":
        fail("schema_version must be 0.1")

    product = require_object("product", manifest.get("product"))
    if product.get("name") != "ORRO":
        fail("product.name must be ORRO")
    if product.get("full_name") != "Observed Run & Review Orchestrator":
        fail("product.full_name must be Observed Run & Review Orchestrator")
    if product.get("repository") != "Moonweave-Systems/ORRO":
        fail("product.repository must be Moonweave-Systems/ORRO")
    require_commit("product.commit", product.get("commit"), allow_zero=True)

    engines = require_object("engines", manifest.get("engines"))
    expected_repos = {
        "witnessd": ("Moonweave-Systems/witnessd", "execution engine"),
        "depone": ("Moonweave-Systems/Depone", "verifier engine"),
    }
    for key, (repository, role) in expected_repos.items():
        engine = require_object(f"engines.{key}", engines.get(key))
        if engine.get("repository") != repository:
            fail(f"engines.{key}.repository must be {repository}")
        if engine.get("role") != role:
            fail(f"engines.{key}.role must be {role}")
        manifest_commit = require_commit(f"engines.{key}.commit", engine.get("commit"))
        lock_commit = require_object(f"engine_lock.{key}", engine_lock.get(key)).get("commit")
        if manifest_commit != lock_commit:
            fail(f"engines.{key}.commit must match engine-lock/orro-e2e-engine-lock.json")

    release_lock = require_object("engine_lock", manifest.get("engine_lock"))
    if release_lock.get("path") != "engine-lock/orro-e2e-engine-lock.json":
        fail("engine_lock.path must be engine-lock/orro-e2e-engine-lock.json")
    require_bool_true("engine_lock.matched_in_ci", release_lock.get("matched_in_ci"))

    surfaces = manifest.get("validated_surfaces")
    if not isinstance(surfaces, list) or not all(isinstance(surface, str) for surface in surfaces):
        fail("validated_surfaces must be a list of strings")
    missing = sorted(REQUIRED_SURFACES.difference(surfaces))
    if missing:
        fail(f"validated_surfaces missing required entries: {', '.join(missing)}")

    validation = require_object("validation", manifest.get("validation"))
    if validation.get("pinned_engine_e2e") != "pass":
        fail("validation.pinned_engine_e2e must be pass")
    if validation.get("boundary_checker") != "pass":
        fail("validation.boundary_checker must be pass")

    boundary = require_object("boundary", manifest.get("boundary"))
    for key in ("depone_verifies", "witnessd_executes", "orro_exposes_workflow"):
        require_bool_true(f"boundary.{key}", boundary.get(key))
    for key in ("contains_engine_logic", "approves_merge", "raises_assurance"):
        require_bool_false(f"boundary.{key}", boundary.get(key))

    require_bool_true("not_proof", manifest.get("not_proof"))
    require_bool_true("not_verifier_truth", manifest.get("not_verifier_truth"))
    require_bool_true("not_package_publish", manifest.get("not_package_publish"))

    print("ORRO release manifest: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
