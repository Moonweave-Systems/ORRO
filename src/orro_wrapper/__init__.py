"""Published ORRO product wrapper.

This package delegates to existing engine commands. It does not implement
Depone verifier logic or witnessd runtime logic.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


DIST_NAME = "orro"


class VersionMetadataError(RuntimeError):
    def __init__(self, distribution: str) -> None:
        super().__init__(f"package metadata for {distribution} is not installed")
        self.distribution = distribution


def get_version() -> str:
    try:
        return version(DIST_NAME)
    except PackageNotFoundError as exc:
        raise VersionMetadataError(DIST_NAME) from exc


def __getattr__(name: str) -> str:
    if name == "__version__":
        return get_version()
    raise AttributeError(name)
