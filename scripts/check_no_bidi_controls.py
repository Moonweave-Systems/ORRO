#!/usr/bin/env python3
"""Reject review-confusing hidden Unicode controls in repository text files."""

from __future__ import annotations

import argparse
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_HIDDEN_CONTROL_CODEPOINTS = {
    0x061C,  # ARABIC LETTER MARK
    0x200B,  # ZERO WIDTH SPACE
    0x200C,  # ZERO WIDTH NON-JOINER
    0x200D,  # ZERO WIDTH JOINER
    0x200E,  # LEFT-TO-RIGHT MARK
    0x200F,  # RIGHT-TO-LEFT MARK
    0x202A,  # LEFT-TO-RIGHT EMBEDDING
    0x202B,  # RIGHT-TO-LEFT EMBEDDING
    0x202C,  # POP DIRECTIONAL FORMATTING
    0x202D,  # LEFT-TO-RIGHT OVERRIDE
    0x202E,  # RIGHT-TO-LEFT OVERRIDE
    0x2060,  # WORD JOINER
    0x2066,  # LEFT-TO-RIGHT ISOLATE
    0x2067,  # RIGHT-TO-LEFT ISOLATE
    0x2068,  # FIRST STRONG ISOLATE
    0x2069,  # POP DIRECTIONAL ISOLATE
    0xFEFF,  # ZERO WIDTH NO-BREAK SPACE
}
FORBIDDEN_HIDDEN_CONTROL_CHARS = {
    chr(codepoint) for codepoint in FORBIDDEN_HIDDEN_CONTROL_CODEPOINTS
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
    name: str
    reason: str


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
            if char in FORBIDDEN_HIDDEN_CONTROL_CHARS:
                findings.append(
                    Finding(
                        path=relative,
                        line=line_number,
                        column=column,
                        codepoint=f"U+{ord(char):04X}",
                        name=unicodedata.name(char, "UNKNOWN"),
                        reason="review-confusing hidden or directional control",
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
            f"forbidden hidden control {finding.codepoint} "
            f"({finding.name}): {finding.reason}",
            file=sys.stderr,
        )


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="orro-bidi-self-test-") as temp:
        root = Path(temp)
        (root / "safe-ascii.txt").write_text("safe ASCII text\n", encoding="utf-8")
        (root / "safe-korean.txt").write_text("안전한 한글 문장입니다.\n", encoding="utf-8")
        unsafe = "unsafe " + chr(0x202E) + " text\n"
        (root / "unsafe.txt").write_text(unsafe, encoding="utf-8")
        controls_dir = root / "controls"
        controls_dir.mkdir()
        for codepoint in sorted(FORBIDDEN_HIDDEN_CONTROL_CODEPOINTS - {0x202E}):
            control_text = "unsafe " + chr(codepoint) + " text\n"
            (controls_dir / f"unsafe-u{codepoint:04x}.txt").write_text(
                control_text,
                encoding="utf-8",
            )
        (root / ".omx").mkdir()
        local_state = "local runtime state is not repository hygiene input " + chr(0x202E) + "\n"
        (root / ".omx" / "runtime-state.txt").write_text(
            local_state,
            encoding="utf-8",
        )
        (root / "binary.bin").write_bytes(b"\xff\xfe\x00\x00")

        findings = scan(root)
        if len(findings) != len(FORBIDDEN_HIDDEN_CONTROL_CODEPOINTS):
            print(
                "self-test failed: expected "
                f"{len(FORBIDDEN_HIDDEN_CONTROL_CODEPOINTS)} findings, got {len(findings)}",
                file=sys.stderr,
            )
            print_findings(findings)
            return 1
        found_codepoints = {int(finding.codepoint[2:], 16) for finding in findings}
        if found_codepoints != FORBIDDEN_HIDDEN_CONTROL_CODEPOINTS:
            print(f"self-test failed: unexpected codepoints {found_codepoints}", file=sys.stderr)
            return 1
        if not any(finding.path == Path("unsafe.txt") and finding.codepoint == "U+202E" for finding in findings):
            print("self-test failed: missing single-file U+202E finding", file=sys.stderr)
            return 1

    print("hidden control scan self-test: pass")
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

    print("hidden control scan: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
