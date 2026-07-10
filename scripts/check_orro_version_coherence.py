#!/usr/bin/env python3
"""Check ORRO wrapper runtime version comes from package metadata."""

from __future__ import annotations

import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DIST_NAME = "orro-product-wrapper"


class VersionCoherenceError(RuntimeError):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def _metadata_version() -> str:
    try:
        return importlib.metadata.version(DIST_NAME)
    except importlib.metadata.PackageNotFoundError as exc:
        raise VersionCoherenceError(
            "ERR_ORRO_VERSION_METADATA_MISSING",
            "package metadata for ORRO wrapper is not installed",
            {"distribution": DIST_NAME},
        ) from exc


def check_version_coherence() -> dict[str, Any]:
    sys.path.insert(0, str(SRC))
    import orro_wrapper

    runtime_version = getattr(orro_wrapper, "__version__", None)
    metadata_version = _metadata_version()
    if runtime_version != metadata_version:
        raise VersionCoherenceError(
            "ERR_ORRO_VERSION_MISMATCH",
            "runtime version must match importlib.metadata version",
            {
                "runtime_version": runtime_version,
                "metadata_version": metadata_version,
            },
        )
    return {
        "kind": "orro-version-coherence-result",
        "decision": "pass",
        "runtime_version": runtime_version,
        "metadata_version": metadata_version,
        "distribution": DIST_NAME,
    }


def main() -> int:
    try:
        payload = check_version_coherence()
    except VersionCoherenceError as exc:
        print(
            json.dumps(
                {
                    "kind": "orro-version-coherence-result",
                    "decision": "fail",
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "details": exc.details,
                    },
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
