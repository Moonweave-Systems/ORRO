#!/usr/bin/env python3
"""Update ORRO pinned-engine metadata together.

This script edits ORRO product/distribution metadata only. It does not fetch,
checkout, execute engines, verify evidence, approve merge, or raise assurance.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
ZERO_COMMIT = "0" * 40
ENGINE_LOCK_REL = Path("engine-lock/orro-e2e-engine-lock.json")
RELEASE_MANIFEST_REL = Path("release/orro-release-manifest.v0.json")
COMPAT_MATRIX_REL = Path("docs/compatibility-matrix.md")
STRUCTURED_COMPAT_MATRIX_REL = Path("release/compatibility-matrix.v0.json")


class UpdateError(RuntimeError):
    pass


def fail(message: str) -> None:
    print(f"ORRO engine-lock update error: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_commit(label: str, value: str, *, allow_zero: bool = False) -> str:
    if not COMMIT_RE.fullmatch(value):
        raise UpdateError(f"{label} must be a 40-hex commit")
    if not allow_zero and value == ZERO_COMMIT:
        raise UpdateError(f"{label} must not be the placeholder zero commit")
    return value


def read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as exc:
        raise UpdateError(f"could not read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise UpdateError(f"malformed JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise UpdateError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def matrix_entries_by_id(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = matrix.get("entries")
    if not isinstance(entries, list):
        raise UpdateError("structured compatibility matrix entries must be a list")
    by_id: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise UpdateError("structured compatibility matrix entries must be objects with string ids")
        by_id[entry["id"]] = entry
    return by_id


def resolve_ref_name(requested: str | None, engine_lock: dict[str, Any], engine: str) -> str:
    if requested is not None:
        return requested
    current = engine_lock.get(engine)
    if not isinstance(current, dict) or not isinstance(current.get("ref_name"), str):
        raise UpdateError(f"engine-lock {engine}.ref_name must be a string when no replacement ref is supplied")
    return current["ref_name"]


def resolve_witnessd_ref_name(requested: str | None, version: str) -> str:
    version_ref = f"v{version}"
    if requested is None:
        return version_ref
    if requested != version_ref:
        raise UpdateError(f"witnessd ref must be {version_ref} for witnessd version {version}")
    return requested


def update_files(
    root: Path,
    *,
    witnessd_commit: str,
    witnessd_version: str,
    depone_commit: str,
    witnessd_ref: str | None,
    depone_ref: str | None,
    orro_commit: str,
    dry_run: bool,
) -> dict[str, Any]:
    validate_commit("witnessd commit", witnessd_commit)
    if VERSION_RE.fullmatch(witnessd_version) is None:
        raise UpdateError("witnessd version must be an X.Y.Z version")
    validate_commit("Depone commit", depone_commit)
    validate_commit("ORRO commit", orro_commit, allow_zero=True)

    engine_lock_path = root / ENGINE_LOCK_REL
    release_manifest_path = root / RELEASE_MANIFEST_REL
    compatibility_matrix_path = root / COMPAT_MATRIX_REL
    structured_compatibility_matrix_path = root / STRUCTURED_COMPAT_MATRIX_REL

    engine_lock = read_json(engine_lock_path)
    witnessd_ref = resolve_witnessd_ref_name(witnessd_ref, witnessd_version)
    depone_ref = resolve_ref_name(depone_ref, engine_lock, "depone")
    engine_lock.update(
        {
            "kind": "orro-engine-lock",
            "schema_version": "1.0",
            "witnessd": {
                "repository": "Moonweave-Systems/witnessd",
                "commit": witnessd_commit,
                "version": witnessd_version,
                "ref_name": witnessd_ref,
            },
            "depone": {
                "repository": "Moonweave-Systems/Depone",
                "commit": depone_commit,
                "ref_name": depone_ref,
            },
            "boundary": {
                "approves_merge": False,
                "raises_assurance": False,
                "executes_commands": False,
                "verifies_evidence": False,
            },
        }
    )

    release_manifest = read_json(release_manifest_path)
    release_manifest.setdefault("product", {})
    release_manifest["product"].update(
        {
            "name": "ORRO",
            "full_name": "Observed Run & Review Orchestrator",
            "repository": "Moonweave-Systems/ORRO",
            "commit": orro_commit,
        }
    )
    release_manifest["engines"] = {
        "witnessd": {
            "repository": "Moonweave-Systems/witnessd",
            "commit": witnessd_commit,
            "version": witnessd_version,
            "role": "execution engine",
        },
        "depone": {
            "repository": "Moonweave-Systems/Depone",
            "commit": depone_commit,
            "role": "verifier engine",
        },
    }
    release_manifest["engine_lock"] = {
        "path": str(ENGINE_LOCK_REL),
        "matched_in_ci": True,
    }
    release_manifest["boundary"] = {
        "depone_verifies": True,
        "witnessd_executes": True,
        "orro_exposes_workflow": True,
        "contains_engine_logic": False,
        "approves_merge": False,
        "raises_assurance": False,
    }
    release_manifest["not_proof"] = True
    release_manifest["not_verifier_truth"] = True
    release_manifest["not_package_publish"] = True

    matrix_text = compatibility_matrix_path.read_text(encoding="utf-8")
    matrix_text = replace_matrix_row(matrix_text, witnessd_commit, witnessd_version, depone_commit, orro_commit)

    structured_matrix = read_json(structured_compatibility_matrix_path)
    structured_entries = matrix_entries_by_id(structured_matrix)
    try:
        current_entry = structured_entries["depone-n-witnessd-n"]
        triplet_entry = structured_entries["orro-rc-locked-triplet"]
    except KeyError as exc:
        raise UpdateError(f"structured compatibility matrix missing entry: {exc.args[0]}") from exc
    current_entry.update(
        {
            "witnessd_commit": witnessd_commit,
            "witnessd_version": witnessd_version,
            "depone_commit": depone_commit,
        }
    )
    triplet_entry.update(
        {
            "orro_commit": orro_commit,
            "witnessd_commit": witnessd_commit,
            "witnessd_version": witnessd_version,
            "depone_commit": depone_commit,
        }
    )

    changed = {
        "engine_lock": str(ENGINE_LOCK_REL),
        "release_manifest": str(RELEASE_MANIFEST_REL),
        "compatibility_matrix": str(COMPAT_MATRIX_REL),
        "structured_compatibility_matrix": str(STRUCTURED_COMPAT_MATRIX_REL),
        "witnessd_commit": witnessd_commit,
        "witnessd_version": witnessd_version,
        "depone_commit": depone_commit,
        "orro_commit": orro_commit,
        "dry_run": dry_run,
        "boundary": {
            "contains_engine_logic": False,
            "approves_merge": False,
            "raises_assurance": False,
            "depone_verifies": True,
            "witnessd_executes": True,
            "orro_exposes_workflow": True,
        },
    }
    if not dry_run:
        write_json(engine_lock_path, engine_lock)
        write_json(release_manifest_path, release_manifest)
        compatibility_matrix_path.write_text(matrix_text, encoding="utf-8")
        write_json(structured_compatibility_matrix_path, structured_matrix)
    return changed


def replace_matrix_row(
    text: str,
    witnessd_commit: str,
    witnessd_version: str,
    depone_commit: str,
    orro_commit: str,
) -> str:
    # The matrix table now leads with a stable "Matrix entry" label column, so the
    # ORRO repo commit (pending or pinned) lives in the second column, not the first.
    orro_repo_commit = "pending release manifest" if orro_commit == ZERO_COMMIT else f"`{orro_commit}`"
    rows = {
        "depone-n-witnessd-n": (
            f"| depone-n-witnessd-n | n/a | `{witnessd_commit}` | `{depone_commit}` | pass | "
            f"Current locally validated engine pair; witnessd v{witnessd_version}. |"
        ),
        "orro-rc-locked-triplet": (
            f"| orro-rc-locked-triplet | {orro_repo_commit} | `{witnessd_commit}` | `{depone_commit}` | pass | "
            f"Matches witnessd v{witnessd_version}, `engine-lock/orro-e2e-engine-lock.json`, "
            f"`release/orro-release-manifest.v0.json`, and `release/compatibility-matrix.v0.json`. |"
        ),
    }
    lines = text.splitlines()
    found: set[str] = set()
    for index, line in enumerate(lines):
        for entry_id, row in rows.items():
            if line.startswith(f"| {entry_id} |"):
                lines[index] = row
                found.add(entry_id)
    missing = sorted(rows.keys() - found)
    if missing:
        raise UpdateError(f"could not find compatibility matrix rows: {', '.join(missing)}")
    return "\n".join(lines) + "\n"


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="orro-update-lock-self-test-") as raw_tmp:
        tmp = Path(raw_tmp)
        checker_rel = Path("scripts/check_compatibility_matrix.py")
        for rel in (ENGINE_LOCK_REL, RELEASE_MANIFEST_REL, COMPAT_MATRIX_REL, STRUCTURED_COMPAT_MATRIX_REL, checker_rel):
            (tmp / rel.parent).mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, tmp / rel)
        original_lock = read_json(tmp / ENGINE_LOCK_REL)
        with contextlib.redirect_stdout(io.StringIO()):
            status = main(
                [
                    "--root",
                    str(tmp),
                    "--witnessd-commit",
                    "1" * 40,
                    "--witnessd-version",
                    "9.8.7",
                    "--depone-commit",
                    "2" * 40,
                    "--orro-commit",
                    "3" * 40,
                ]
            )
        assert status == 0
        engine_lock = read_json(tmp / ENGINE_LOCK_REL)
        release_manifest = read_json(tmp / RELEASE_MANIFEST_REL)
        structured_matrix = read_json(tmp / STRUCTURED_COMPAT_MATRIX_REL)
        structured_entries = {entry["id"]: entry for entry in structured_matrix["entries"]}
        matrix = (tmp / COMPAT_MATRIX_REL).read_text(encoding="utf-8")
        assert engine_lock["witnessd"]["commit"] == "1" * 40
        assert engine_lock["witnessd"]["version"] == "9.8.7"
        assert engine_lock["depone"]["commit"] == "2" * 40
        assert engine_lock["witnessd"]["ref_name"] == "v9.8.7"
        assert engine_lock["depone"]["ref_name"] == original_lock["depone"]["ref_name"]
        assert release_manifest["engines"]["witnessd"]["commit"] == "1" * 40
        assert release_manifest["engines"]["witnessd"]["version"] == "9.8.7"
        assert release_manifest["engines"]["depone"]["commit"] == "2" * 40
        assert structured_entries["depone-n-witnessd-n"]["witnessd_commit"] == "1" * 40
        assert structured_entries["depone-n-witnessd-n"]["witnessd_version"] == "9.8.7"
        assert structured_entries["depone-n-witnessd-n"]["depone_commit"] == "2" * 40
        assert structured_entries["orro-rc-locked-triplet"]["orro_commit"] == "3" * 40
        assert structured_entries["orro-rc-locked-triplet"]["witnessd_commit"] == "1" * 40
        assert structured_entries["orro-rc-locked-triplet"]["witnessd_version"] == "9.8.7"
        assert structured_entries["orro-rc-locked-triplet"]["depone_commit"] == "2" * 40
        assert "`1111111111111111111111111111111111111111`" in matrix
        assert "`2222222222222222222222222222222222222222`" in matrix
        assert "`3333333333333333333333333333333333333333`" in matrix
        checker = subprocess.run(
            [sys.executable, str(tmp / checker_rel), "--metadata-only"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert checker.returncode == 0, checker.stderr
        try:
            resolve_witnessd_ref_name("main", "9.8.7")
        except UpdateError:
            pass
        else:
            raise AssertionError("mismatched witnessd version ref was accepted")
    print("ORRO engine-lock update helper: self-test pass")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update ORRO e2e engine-lock and release metadata together.")
    parser.add_argument("--witnessd-commit")
    parser.add_argument("--witnessd-version")
    parser.add_argument("--depone-commit")
    parser.add_argument("--witnessd-ref")
    parser.add_argument("--depone-ref")
    parser.add_argument("--orro-commit", default=ZERO_COMMIT)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.self_test:
        return self_test()
    if not args.witnessd_commit or not args.witnessd_version or not args.depone_commit:
        fail("--witnessd-commit, --witnessd-version, and --depone-commit are required")
    try:
        result = update_files(
            Path(args.root).resolve(),
            witnessd_commit=args.witnessd_commit,
            witnessd_version=args.witnessd_version,
            depone_commit=args.depone_commit,
            witnessd_ref=args.witnessd_ref,
            depone_ref=args.depone_ref,
            orro_commit=args.orro_commit,
            dry_run=args.dry_run,
        )
    except UpdateError as exc:
        fail(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
