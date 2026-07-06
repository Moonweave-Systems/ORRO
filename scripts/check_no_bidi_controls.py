#!/usr/bin/env python3
"""Reject hidden bidirectional Unicode controls in repository text files."""

from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BIDI_CONTROL_CHARS = {
    "\u202a",  # LEFT-TO-RIGHT EMBEDDING
    "\u202b",  # RIGHT-TO-LEFT EMBEDDING
    "\u202c",  # POP DIRECTIONAL FORMATTING
    "\u202d",  # LEFT-TO-RIGHT OVERRIDE
    "\u202e",  # RIGHT-TO-LEFT OVERRIDE
    "\u2066",  # LEFT-TO-RIGHT ISOLATE
    "\u2067",  # RIGHT-TO-LEFT ISOLATE
    "\u2068",  # FIRST STRONG ISOLATE
    "\u2069",  # POP DIRECTIONAL ISOLATE
}
SKIP_DIRS = {
    ".git",
    ".omx",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    "node_modules",
}


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    column: int
    codepoint: str


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def scan_file(path: Path, root: Path) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    findings: list[Finding] = []
    relative = path.relative_to(root)
    for line_number, line in enumerate(text.splitlines(), start=1):
        for column, char in enumerate(line, start=1):
            if char in BIDI_CONTROL_CHARS:
                findings.append(
                    Finding(
                        path=relative,
                        line=line_number,
                        column=column,
                        codepoint=f"U+{ord(char):04X}",
                    )
                )
    return findings


def scan(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_files(root):
        findings.extend(scan_file(path, root))
    return findings


def print_findings(findings: list[Finding]) -> None:
    for finding in findings:
        print(
            f"{finding.path}:{finding.line}:{finding.column}: "
            f"forbidden bidi control {finding.codepoint}",
            file=sys.stderr,
        )


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="orro-bidi-self-test-") as temp:
        root = Path(temp)
        (root / "safe.txt").write_text(
            "safe ASCII, Korean 한글, emoji 😀, and accented é text\n",
            encoding="utf-8",
        )
        (root / "unsafe.txt").write_text("unsafe \u202e text\n", encoding="utf-8")
        (root / ".omx").mkdir()
        (root / ".omx" / "runtime-state.txt").write_text(
            "local runtime state is not repository hygiene input \u202e\n",
            encoding="utf-8",
        )
        (root / "binary.bin").write_bytes(b"\xff\xfe\x00\x00")

        findings = scan(root)
        if len(findings) != 1:
            print(
                f"self-test failed: expected 1 finding, got {len(findings)}",
                file=sys.stderr,
            )
            print_findings(findings)
            return 1
        finding = findings[0]
        if finding.path != Path("unsafe.txt") or finding.codepoint != "U+202E":
            print(f"self-test failed: unexpected finding {finding}", file=sys.stderr)
            return 1

    print("bidi control scan self-test: pass")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true", help="run built-in scanner checks")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    findings = scan(ROOT)
    if findings:
        print_findings(findings)
        return 1

    print("bidi control scan: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
