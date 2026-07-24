"""Thin ORRO product command.

ORRO owns the user-facing command and delegates execution to the pinned
witnessd-hosted ORRO surface. It does not implement engine logic locally.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from typing import Any

from . import VersionMetadataError, get_version


SCHEMA_VERSION = "0.1"
DEFAULT_ENGINE_COMMAND = f"{sys.executable} -m orro"


class WrapperError(RuntimeError):
    def __init__(
        self, code: str, message: str, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def boundary() -> dict[str, Any]:
    return {
        "contains_engine_logic": False,
        "implements_proofrun": False,
        "implements_proofcheck": False,
        "delegates_to_witnessd_hosted_orro": True,
        "owns_orro_command": True,
        "executes_proofrun_itself": False,
        "verifies_evidence_itself": False,
        "approves_merge": False,
        "raises_assurance": False,
        "depone_verifies": True,
        "witnessd_executes": True,
        "orro_exposes_workflow": True,
    }


def wrapper_info() -> dict[str, Any]:
    return {
        "kind": "orro-wrapper-info",
        "schema_version": SCHEMA_VERSION,
        "version": get_version(),
        "current_command_source": "ORRO-owned orro console script",
        "published_package": True,
        "published_package_scope": "product-line",
        "not_proof": True,
        "not_verifier_truth": True,
        "boundary": boundary(),
    }


def error_payload(exc: WrapperError) -> dict[str, Any]:
    return {
        "kind": "orro-wrapper-error",
        "schema_version": SCHEMA_VERSION,
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
        "boundary": boundary(),
    }


def resolve_engine_command(raw: str | None) -> list[str]:
    command = raw or os.environ.get("ORRO_ENGINE_COMMAND") or DEFAULT_ENGINE_COMMAND
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        raise WrapperError(
            "ERR_ORRO_WRAPPER_ENGINE_COMMAND_INVALID",
            "engine command could not be parsed",
            {"command": command},
        ) from exc
    if not parts:
        raise WrapperError(
            "ERR_ORRO_WRAPPER_ENGINE_COMMAND_INVALID",
            "engine command must not be empty",
        )
    return parts


def delegate(engine_command: str | None, delegate_args: list[str]) -> int:
    if delegate_args and delegate_args[0] == "--":
        delegate_args = delegate_args[1:]
    if not delegate_args:
        raise WrapperError(
            "ERR_ORRO_WRAPPER_DELEGATE_ARGS_REQUIRED",
            "delegate requires engine command arguments after --",
        )
    command = [*resolve_engine_command(engine_command), *delegate_args]
    child_env = os.environ.copy()
    child_env["ORRO_WRAPPER_DELEGATION"] = "1"
    completed = subprocess.run(command, check=False, env=child_env)
    return completed.returncode


def self_test() -> int:
    info = wrapper_info()
    assert info["kind"] == "orro-wrapper-info"
    assert info["boundary"]["contains_engine_logic"] is False
    assert info["boundary"]["implements_proofrun"] is False
    assert info["boundary"]["implements_proofcheck"] is False
    assert resolve_engine_command("python3 -m orro") == [
        "python3",
        "-m",
        "orro",
    ]
    try:
        delegate("python3 -m orro", [])
    except WrapperError as exc:
        assert exc.code == "ERR_ORRO_WRAPPER_DELEGATE_ARGS_REQUIRED"
    else:
        raise AssertionError("empty delegate args did not fail")
    print(
        json.dumps(
            {
                "kind": "orro-wrapper-self-test-result",
                "schema_version": SCHEMA_VERSION,
                "decision": "pass",
                "boundary": boundary(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    # This list mirrors the engine's ORRO_COMMAND_MAP public keys; keep it in sync.
    parser = argparse.ArgumentParser(
        description="ORRO product command.",
        epilog="""Workflow commands run directly (e.g. `orro demo`, `orro flow <goal>`);
they are delegated to the pinned witnessd engine, not implemented here.

Start here:
  demo         AI-free 30s guardrail demo: Depone scope-conformance PASS/FAIL
  flow         guided init -> scout -> flowplan -> proofrun -> proofcheck
  check        verify already-driven work (Depone verdict) + read-only review
  doctor       engine/verifier/adapter readiness

Workflow:
  scout, flowplan, proofrun, proofcheck, handoff, review
  advise       routes the goal itself: bug-shaped -> trace advisory, new work -> sketch advisory (--mode overrides)
  ship         push a ship-ready branch and optionally open a PR (evidence-gated); merge approval stays human

Removed aliases (2.27.0): sketch/trace -> advise --mode ..., next -> auto --dry-run, report -> status <run-dir> | --latest

Project legibility:
  status       roadmap items with evidence-bound state + off-plan runs + workspace summary
  tidy         inventory (default) and safe cleanup of run worktrees (--apply)
  task         persistent per-item task worktree lifecycle (begin + optional open hook)

Setup / advanced:
  setup, init, advise, auto, team, engine-lock, lock, advisory-provenance-check

Try it in 30s (no AI adapter):
  orro demo

Run the guided workflow end-to-end (init -> scout -> flowplan -> proofrun -> proofcheck) with:
  orro flow <goal>

Any workflow command can also be run explicitly through the engine with:
  orro delegate -- <command>

Show the authoritative engine command list with:
  orro delegate -- --help

The wrapper delegates execution; it does not implement these workflow commands.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--engine-command",
        help="Pinned witnessd ORRO command to delegate to. Defaults to current Python -m orro.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON for wrapper-owned commands. JSON is the default for boundary/self-test.",
    )
    parser.add_argument(
        "--version", action="store_true", help="Print wrapper version and exit."
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("boundary", help="Print wrapper boundary metadata.")
    subparsers.add_parser(
        "self-test", help="Run wrapper self-test without calling engines."
    )
    delegate_parser = subparsers.add_parser(
        "delegate", help="Delegate explicitly to the witnessd-hosted ORRO command."
    )
    delegate_parser.add_argument("delegate_args", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    raw_args = sys.argv[1:] if argv is None else argv
    local_commands = {"boundary", "self-test", "delegate"}
    if (
        raw_args
        and raw_args[0] not in local_commands
        and not raw_args[0].startswith("-")
    ):
        return delegate(None, raw_args)
    args = parse_args(raw_args)
    try:
        if args.version:
            print(get_version())
            return 0
        if args.command in (None, "boundary"):
            print(json.dumps(wrapper_info(), indent=2, sort_keys=True))
            return 0
        if args.command == "self-test":
            return self_test()
        if args.command == "delegate":
            return delegate(args.engine_command, args.delegate_args)
        raise WrapperError(
            "ERR_ORRO_WRAPPER_COMMAND_UNKNOWN",
            "unknown wrapper command",
            {"command": args.command},
        )
    except WrapperError as exc:
        print(json.dumps(error_payload(exc), indent=2, sort_keys=True), file=sys.stderr)
        return 2
    except VersionMetadataError as exc:
        error = WrapperError(
            "ERR_ORRO_WRAPPER_METADATA_MISSING",
            "package metadata for ORRO wrapper is not installed",
            {"distribution": exc.distribution},
        )
        print(
            json.dumps(error_payload(error), indent=2, sort_keys=True), file=sys.stderr
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
