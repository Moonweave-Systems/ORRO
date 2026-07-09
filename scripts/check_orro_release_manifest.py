#!/usr/bin/env python3
"""Validate the ORRO release manifest metadata contract."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
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


def check_product_commit_reachable(commit: str, repo_root: Path) -> None:
    if commit == ZERO_COMMIT:
        return
    if not (repo_root / ".git").exists():
        return
    try:
        shallow = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--is-shallow-repository"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError:
        return
    # A shallow clone (e.g. CI actions/checkout default depth 1) cannot resolve
    # historical commits; skip rather than false-reject a legitimate commit.
    if shallow.returncode != 0 or shallow.stdout.strip() == "true":
        return
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError:
        return
    if completed.returncode != 0:
        fail(f"product.commit {commit} is not a reachable commit in the ORRO repo")


def validate(manifest: dict[str, Any], engine_lock: dict[str, Any], *, repo_root: Path | None) -> None:
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
    product_commit = require_commit("product.commit", product.get("commit"), allow_zero=True)

    if repo_root is not None:
        check_product_commit_reachable(product_commit, repo_root)

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


def _build_fixtures() -> tuple[dict[str, Any], dict[str, Any]]:
    witnessd_commit = "1" * 40
    depone_commit = "2" * 40
    manifest = {
        "kind": "orro-release-manifest",
        "schema_version": "0.1",
        "product": {
            "name": "ORRO",
            "full_name": "Observed Run & Review Orchestrator",
            "repository": "Moonweave-Systems/ORRO",
            "commit": ZERO_COMMIT,
        },
        "engines": {
            "witnessd": {
                "repository": "Moonweave-Systems/witnessd",
                "commit": witnessd_commit,
                "role": "execution engine",
            },
            "depone": {
                "repository": "Moonweave-Systems/Depone",
                "commit": depone_commit,
                "role": "verifier engine",
            },
        },
        "engine_lock": {
            "path": "engine-lock/orro-e2e-engine-lock.json",
            "matched_in_ci": True,
        },
        "validated_surfaces": sorted(REQUIRED_SURFACES),
        "validation": {
            "pinned_engine_e2e": "pass",
            "boundary_checker": "pass",
        },
        "boundary": {
            "depone_verifies": True,
            "witnessd_executes": True,
            "orro_exposes_workflow": True,
            "contains_engine_logic": False,
            "approves_merge": False,
            "raises_assurance": False,
        },
        "not_proof": True,
        "not_verifier_truth": True,
        "not_package_publish": True,
    }
    engine_lock = {
        "kind": "orro-engine-lock",
        "schema_version": "1.0",
        "witnessd": {
            "repository": "Moonweave-Systems/witnessd",
            "commit": witnessd_commit,
            "ref_name": "main",
        },
        "depone": {
            "repository": "Moonweave-Systems/Depone",
            "commit": depone_commit,
            "ref_name": "main",
        },
        "boundary": {
            "approves_merge": False,
            "raises_assurance": False,
            "executes_commands": False,
            "verifies_evidence": False,
        },
    }
    return manifest, engine_lock


def _deep_copy(value: Any) -> Any:
    return json.loads(json.dumps(value))


def self_test() -> int:
    base_manifest, base_lock = _build_fixtures()
    try:
        validate(base_manifest, base_lock, repo_root=None)
    except SystemExit:
        print("self-test failed: base manifest was rejected", file=sys.stderr)
        return 1

    forgeries: list[tuple[str, Any]] = [
        ("engines.witnessd.commit mismatch", lambda m: m["engines"]["witnessd"].__setitem__("commit", "3" * 40)),
        ("validated_surfaces missing proofrun", lambda m: m["validated_surfaces"].remove("proofrun")),
        ("boundary.approves_merge true", lambda m: m["boundary"].__setitem__("approves_merge", True)),
        ("not_proof false", lambda m: m.__setitem__("not_proof", False)),
        ("product.commit non-hex", lambda m: m["product"].__setitem__("commit", "not-a-commit")),
        ("validation.pinned_engine_e2e fail", lambda m: m["validation"].__setitem__("pinned_engine_e2e", "fail")),
        ("engines.depone.role wrong", lambda m: m["engines"]["depone"].__setitem__("role", "not a real role")),
    ]

    for name, mutate in forgeries:
        forged_manifest = _deep_copy(base_manifest)
        mutate(forged_manifest)
        try:
            validate(forged_manifest, base_lock, repo_root=None)
        except SystemExit:
            continue
        print(f"self-test failed: forged manifest ({name}) was accepted", file=sys.stderr)
        return 1

    if shutil.which("git") is not None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()

            def _git(*args: str, cwd: Path) -> str:
                done = subprocess.run(
                    ["git", *args],
                    cwd=str(cwd),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                )
                return done.stdout.strip()

            _git("init", "-q", cwd=repo)
            _git("config", "user.email", "selftest@example.invalid", cwd=repo)
            _git("config", "user.name", "selftest", cwd=repo)
            (repo / "a.txt").write_text("1\n")
            _git("add", "a.txt", cwd=repo)
            _git("commit", "-qm", "one", cwd=repo)
            first_commit = _git("rev-parse", "HEAD", cwd=repo)
            (repo / "a.txt").write_text("2\n")
            _git("add", "a.txt", cwd=repo)
            _git("commit", "-qm", "two", cwd=repo)
            head_commit = _git("rev-parse", "HEAD", cwd=repo)

            # Reachable commits pass; a well-formed but absent commit is rejected.
            check_product_commit_reachable(head_commit, repo)
            check_product_commit_reachable(first_commit, repo)
            try:
                check_product_commit_reachable("d" * 40, repo)
            except SystemExit:
                pass
            else:
                print("self-test failed: fabricated product.commit was accepted", file=sys.stderr)
                return 1

            # A non-git dir and a shallow clone both skip rather than false-reject.
            check_product_commit_reachable(head_commit, Path(tmp))
            shallow = Path(tmp) / "shallow"
            _git("clone", "--depth", "1", "-q", repo.as_uri(), str(shallow), cwd=Path(tmp))
            check_product_commit_reachable(first_commit, shallow)

    print("ORRO release manifest self-test: pass")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true", help="run built-in forgery-rejection checks")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    manifest = require_object("release manifest", load_json(MANIFEST_PATH))
    engine_lock = require_object("engine lock", load_json(ENGINE_LOCK_PATH))
    validate(manifest, engine_lock, repo_root=ROOT)

    print("ORRO release manifest: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
