#!/usr/bin/env python3
"""Update ORRO pinned-engine metadata together.

This script edits ORRO product/distribution metadata only. It does not fetch,
checkout, execute engines, verify evidence, approve merge, or raise assurance.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
ZERO_COMMIT = "0" * 40
ENGINE_LOCK_REL = Path("engine-lock/orro-e2e-engine-lock.json")
RELEASE_MANIFEST_REL = Path("release/orro-release-manifest.v0.json")
COMPAT_MATRIX_REL = Path("docs/compatibility-matrix.md")


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


def update_files(
    root: Path,
    *,
    witnessd_commit: str,
    depone_commit: str,
    witnessd_ref: str,
    depone_ref: str,
    orro_commit: str,
    dry_run: bool,
) -> dict[str, Any]:
    validate_commit("witnessd commit", witnessd_commit)
    validate_commit("Depone commit", depone_commit)
    validate_commit("ORRO commit", orro_commit, allow_zero=True)

    engine_lock_path = root / ENGINE_LOCK_REL
    release_manifest_path = root / RELEASE_MANIFEST_REL
    compatibility_matrix_path = root / COMPAT_MATRIX_REL

    engine_lock = read_json(engine_lock_path)
    engine_lock.update(
        {
            "kind": "orro-engine-lock",
            "schema_version": "1.0",
            "witnessd": {
                "repository": "Moonweave-Systems/witnessd",
                "commit": witnessd_commit,
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
    matrix_text = replace_matrix_row(matrix_text, witnessd_commit, depone_commit, orro_commit)

    changed = {
        "engine_lock": str(ENGINE_LOCK_REL),
        "release_manifest": str(RELEASE_MANIFEST_REL),
        "compatibility_matrix": str(COMPAT_MATRIX_REL),
        "witnessd_commit": witnessd_commit,
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
    return changed


def replace_matrix_row(text: str, witnessd_commit: str, depone_commit: str, orro_commit: str) -> str:
    row_label = "pending release manifest" if orro_commit == ZERO_COMMIT else f"`{orro_commit}`"
    row = (
        f"| {row_label} | `{witnessd_commit}` | `{depone_commit}` | pass | "
        f"Matches `engine-lock/orro-e2e-engine-lock.json` and "
        f"`release/orro-release-manifest.v0.json`. |"
    )
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("| pending release manifest |") or (
            line.startswith("| `") and "engine-lock/orro-e2e-engine-lock.json" in line
        ):
            lines[index] = row
            return "\n".join(lines) + "\n"
    raise UpdateError("could not find compatibility matrix release row")


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="orro-update-lock-self-test-") as raw_tmp:
        tmp = Path(raw_tmp)
        for rel in (ENGINE_LOCK_REL, RELEASE_MANIFEST_REL, COMPAT_MATRIX_REL):
            (tmp / rel.parent).mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, tmp / rel)
        result = update_files(
            tmp,
            witnessd_commit="1" * 40,
            depone_commit="2" * 40,
            witnessd_ref="test-witnessd",
            depone_ref="test-depone",
            orro_commit=ZERO_COMMIT,
            dry_run=False,
        )
        engine_lock = read_json(tmp / ENGINE_LOCK_REL)
        release_manifest = read_json(tmp / RELEASE_MANIFEST_REL)
        matrix = (tmp / COMPAT_MATRIX_REL).read_text(encoding="utf-8")
        assert engine_lock["witnessd"]["commit"] == "1" * 40
        assert engine_lock["depone"]["commit"] == "2" * 40
        assert release_manifest["engines"]["witnessd"]["commit"] == "1" * 40
        assert release_manifest["engines"]["depone"]["commit"] == "2" * 40
        assert "`1111111111111111111111111111111111111111`" in matrix
        assert "`2222222222222222222222222222222222222222`" in matrix
        assert result["boundary"]["contains_engine_logic"] is False
    print("ORRO engine-lock update helper: self-test pass")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update ORRO e2e engine-lock and release metadata together.")
    parser.add_argument("--witnessd-commit")
    parser.add_argument("--depone-commit")
    parser.add_argument("--witnessd-ref", default="main")
    parser.add_argument("--depone-ref", default="main")
    parser.add_argument("--orro-commit", default=ZERO_COMMIT)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.self_test:
        return self_test()
    if not args.witnessd_commit or not args.depone_commit:
        fail("--witnessd-commit and --depone-commit are required")
    try:
        result = update_files(
            Path(args.root).resolve(),
            witnessd_commit=args.witnessd_commit,
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
