#!/usr/bin/env python3
"""Validate immutable ORRO compatibility matrix metadata."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "release" / "compatibility-matrix.v0.json"
ENGINE_LOCK_PATH = ROOT / "engine-lock" / "orro-e2e-engine-lock.json"
RELEASE_MANIFEST_PATH = ROOT / "release" / "orro-release-manifest.v0.json"
DOC_MATRIX_PATH = ROOT / "docs" / "compatibility-matrix.md"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
FORBIDDEN_REFS = {"main", "master", "HEAD"}


def fail(message: str) -> None:
    print(f"ORRO compatibility matrix violation: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"could not read {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def require_commit(label: str, value: Any) -> str:
    if not isinstance(value, str) or not COMMIT_RE.fullmatch(value):
        fail(f"{label} must be a 40-hex commit")
    if value == "0" * 40:
        fail(f"{label} must not be the placeholder zero commit")
    return value


def require_bool_false(label: str, value: Any) -> None:
    if value is not False:
        fail(f"{label} must be false")


def require_bool_true(label: str, value: Any) -> None:
    if value is not True:
        fail(f"{label} must be true")


def git_head(path: Path, label: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        fail(f"{label} git probe failed: {exc}")
    if completed.returncode != 0:
        fail(f"{label} git HEAD unknown: {completed.stderr.strip()}")
    return require_commit(f"{label} HEAD", completed.stdout.strip())


def git_has_commit(path: Path, label: str, commit: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(path), "cat-file", "-e", f"{commit}^{{commit}}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode == 0:
        return True
    if completed.returncode in {1, 128}:
        return False
    fail(f"{label} git commit probe failed: {completed.stderr.strip()}")


def entries_by_id(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = matrix.get("entries")
    if not isinstance(entries, list):
        fail("entries must be a list")
    by_id: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            fail("entries must contain objects")
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not entry_id:
            fail("entry.id must be a non-empty string")
        if entry_id in by_id:
            fail(f"duplicate entry id: {entry_id}")
        by_id[entry_id] = entry
    return by_id


def validate_matrix_shape(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if matrix.get("kind") != "orro-compatibility-matrix":
        fail("kind must be orro-compatibility-matrix")
    if matrix.get("schema_version") != "0.1":
        fail("schema_version must be 0.1")
    require_bool_true("immutable", matrix.get("immutable"))
    for key in ("not_proof", "not_verifier_truth", "not_package_publish"):
        require_bool_true(key, matrix.get(key))
    boundary = matrix.get("boundary")
    if not isinstance(boundary, dict):
        fail("boundary must be an object")
    for key in ("approves_merge", "raises_assurance", "verifies_evidence", "executes_commands"):
        require_bool_false(f"boundary.{key}", boundary.get(key))
    by_id = entries_by_id(matrix)
    required = {
        "depone-n-witnessd-n",
        "depone-n-witnessd-n-1",
        "depone-n-1-witnessd-n",
        "orro-rc-locked-triplet",
    }
    missing = sorted(required.difference(by_id))
    if missing:
        fail(f"missing matrix entries: {', '.join(missing)}")
    for entry_id, entry in by_id.items():
        for key in ("depone_commit", "witnessd_commit"):
            if key in entry:
                require_commit(f"{entry_id}.{key}", entry.get(key))
        if "orro_commit" in entry:
            require_commit(f"{entry_id}.orro_commit", entry.get("orro_commit"))
        if entry.get("status") not in {"pass", "warn"}:
            fail(f"{entry_id}.status must be pass or warn")
    for entry_id in ("depone-n-witnessd-n", "orro-rc-locked-triplet"):
        version = by_id[entry_id].get("witnessd_version")
        if not isinstance(version, str) or VERSION_RE.fullmatch(version) is None:
            fail(f"{entry_id}.witnessd_version must be an X.Y.Z version")
    return by_id


def validate_lock_and_manifest(by_id: dict[str, dict[str, Any]]) -> None:
    current = by_id["depone-n-witnessd-n"]
    triplet = by_id["orro-rc-locked-triplet"]
    lock = load_json(ENGINE_LOCK_PATH)
    manifest = load_json(RELEASE_MANIFEST_PATH)
    for key in ("witnessd", "depone"):
        engine = lock.get(key)
        if not isinstance(engine, dict):
            fail(f"engine-lock.{key} must be an object")
        ref_name = engine.get("ref_name")
        if ref_name in FORBIDDEN_REFS:
            fail(f"engine-lock.{key}.ref_name must not be mutable {ref_name}")
    if lock["witnessd"].get("commit") != current["witnessd_commit"]:
        fail("engine-lock witnessd commit must match depone-n-witnessd-n")
    if lock["depone"].get("commit") != current["depone_commit"]:
        fail("engine-lock Depone commit must match depone-n-witnessd-n")
    if lock["witnessd"].get("version") != current["witnessd_version"]:
        fail("engine-lock witnessd version must match depone-n-witnessd-n")
    if lock["witnessd"].get("ref_name") != f"v{current['witnessd_version']}":
        fail("engine-lock witnessd ref_name must match depone-n-witnessd-n version")
    engines = manifest.get("engines")
    product = manifest.get("product")
    if not isinstance(engines, dict) or not isinstance(product, dict):
        fail("release manifest product and engines must be objects")
    if product.get("commit") != triplet["orro_commit"]:
        fail("release manifest product.commit must match ORRO triplet")
    if engines.get("witnessd", {}).get("commit") != triplet["witnessd_commit"]:
        fail("release manifest witnessd commit must match ORRO triplet")
    if engines.get("witnessd", {}).get("version") != triplet["witnessd_version"]:
        fail("release manifest witnessd version must match ORRO triplet")
    if engines.get("depone", {}).get("commit") != triplet["depone_commit"]:
        fail("release manifest Depone commit must match ORRO triplet")


def validate_doc_matrix(by_id: dict[str, dict[str, Any]]) -> None:
    text = DOC_MATRIX_PATH.read_text(encoding="utf-8")
    for entry_id in (
        "depone-n-witnessd-n",
        "depone-n-witnessd-n-1",
        "depone-n-1-witnessd-n",
        "orro-rc-locked-triplet",
    ):
        entry = by_id[entry_id]
        row = next((line for line in text.splitlines() if line.startswith(f"| {entry_id} |")), None)
        if row is None:
            fail(f"docs compatibility matrix missing {entry_id}")
        for key in ("orro_commit", "witnessd_commit", "witnessd_version", "depone_commit"):
            value = entry.get(key)
            if isinstance(value, str) and value not in row:
                fail(f"docs compatibility matrix missing {entry_id}.{key}")


def validate_local_heads(args: argparse.Namespace, by_id: dict[str, dict[str, Any]]) -> None:
    current = by_id["depone-n-witnessd-n"]
    triplet = by_id["orro-rc-locked-triplet"]
    roots = {
        "witnessd": (args.witnessd_root, current["witnessd_commit"]),
        "depone": (args.depone_root, current["depone_commit"]),
        "orro": (args.orro_root, triplet["orro_commit"]),
    }
    for label, (raw_root, expected) in roots.items():
        if raw_root is None:
            continue
        actual = git_head(Path(raw_root), label)
        if label == "orro" and actual != expected:
            # The compatibility artifact may be committed after the ORRO RC base.
            if not git_has_commit(Path(raw_root), label, expected):
                fail(f"{label} RC base missing from local history: {expected}")
            continue
        if actual != expected:
            fail(f"{label} HEAD mismatch: expected {expected}, got {actual}")


def validate(args: argparse.Namespace) -> None:
    matrix = load_json(MATRIX_PATH)
    by_id = validate_matrix_shape(matrix)
    validate_lock_and_manifest(by_id)
    validate_doc_matrix(by_id)
    if not args.metadata_only:
        validate_local_heads(args, by_id)


def self_test() -> int:
    matrix = {
        "kind": "orro-compatibility-matrix",
        "schema_version": "0.1",
        "immutable": True,
        "not_proof": True,
        "not_verifier_truth": True,
        "not_package_publish": True,
        "entries": [
            {"id": "depone-n-witnessd-n", "depone_commit": "1" * 40, "witnessd_commit": "2" * 40, "witnessd_version": "2.3.3", "status": "pass"},
            {"id": "depone-n-witnessd-n-1", "depone_commit": "1" * 40, "witnessd_commit": "3" * 40, "status": "warn"},
            {"id": "depone-n-1-witnessd-n", "depone_commit": "4" * 40, "witnessd_commit": "2" * 40, "status": "warn"},
            {"id": "orro-rc-locked-triplet", "orro_commit": "5" * 40, "depone_commit": "1" * 40, "witnessd_commit": "2" * 40, "witnessd_version": "2.3.3", "status": "pass"},
        ],
        "boundary": {
            "approves_merge": False,
            "raises_assurance": False,
            "verifies_evidence": False,
            "executes_commands": False,
        },
    }
    validate_matrix_shape(matrix)
    matrix["entries"][0]["witnessd_commit"] = "main"
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            validate_matrix_shape(matrix)
    except SystemExit:
        matrix["entries"][0]["witnessd_commit"] = "2" * 40
    else:
        print("self-test failed: mutable ref was accepted", file=sys.stderr)
        return 1
    matrix["entries"][0]["witnessd_version"] = "latest"
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            validate_matrix_shape(matrix)
    except SystemExit:
        print("ORRO compatibility matrix self-test: pass")
        return 0
    print("self-test failed: invalid witnessd version was accepted", file=sys.stderr)
    return 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate ORRO immutable compatibility matrix.")
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument("--witnessd-root")
    parser.add_argument("--depone-root")
    parser.add_argument("--orro-root")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.self_test:
        return self_test()
    validate(args)
    print("ORRO compatibility matrix: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
