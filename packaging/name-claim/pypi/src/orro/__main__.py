"""ORRO command entry point.

Delegates every ORRO command to the installed witnessd runtime. The recognized
command set is sourced from witnessd (single source of truth), so an unknown
command is named honestly here rather than leaking the engine's generic parser
error. This wrapper adds no execution or verification behavior of its own.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        from witnessd.__main__ import ORRO_COMMANDS, main as witnessd_main
    except ImportError:
        print(
            "orro requires the witnessd engine, which is not installed. Install it "
            "from GitHub:\n"
            "  pip install 'witnessd @ git+https://github.com/Moonweave-Systems/witnessd'",
            file=sys.stderr,
        )
        return 1

    if not args or args[0] in {"-h", "--help"}:
        from orro import about

        print(about())
        print("commands: " + ", ".join(sorted(ORRO_COMMANDS)))
        return 0

    command = args[0]
    if command not in ORRO_COMMANDS:
        from difflib import get_close_matches

        print(f"orro: unknown command '{command}'", file=sys.stderr)
        suggestion = get_close_matches(command, sorted(ORRO_COMMANDS), n=1)
        if suggestion:
            print(f"did you mean '{suggestion[0]}'?", file=sys.stderr)
        print("valid commands: " + ", ".join(sorted(ORRO_COMMANDS)), file=sys.stderr)
        return 2

    return witnessd_main(["orro", *args])


if __name__ == "__main__":
    sys.exit(main())
