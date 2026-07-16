#!/usr/bin/env python3
"""Validate ORRO's repository-internal published release state."""

from __future__ import annotations

import argparse
import ast
import configparser
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = ROOT / "pyproject.toml"
SETUP_CFG_PATH = ROOT / "setup.cfg"
WRAPPER_PATH = ROOT / "src" / "orro_wrapper" / "cli.py"
ENGINE_LOCK_PATH = ROOT / "engine-lock" / "orro-e2e-engine-lock.json"
RELEASE_MANIFEST_PATH = ROOT / "release" / "orro-release-manifest.v0.json"
PACKAGE_PLAN_PATH = ROOT / "packaging" / "wrapper-package-plan.v0.json"
DOC_PATHS = (
    Path("README.md"),
    Path("docs/install.md"),
    Path("docs/compatibility-matrix.md"),
    Path("docs/packaging-decision.md"),
    Path("docs/repository-strategy.md"),
    Path("docs/bootstrap.md"),
    Path("docs/pinned-engine-fallback.md"),
    Path("docs/wrapper-distribution.md"),
    Path("docs/thin-wrapper-plan.md"),
    Path("docs/thin-wrapper.md"),
)
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
WITNESSD_REQUIREMENT_RE = re.compile(r"^witnessd>=(\d+\.\d+\.\d+)$")
STALE_RELEASE_PHRASES = (
    "0.0.x is live",
    "Until 0.1.0 is published",
    "publishing 0.1.0 is a separate",
    "Publishing 0.1.0 is a separate",
    "Until 0.1.1 is published",
    "publishing 0.1.1 is a separate",
    "Publishing 0.1.1 is a separate",
)
PUBLISHED_PYPI_VERSIONS = ("0.0.1", "0.0.2", "0.0.3", "0.1.0", "0.1.1")


class ReleaseStateError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ReleaseStateError(message)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"could not read {path.relative_to(ROOT)}: {exc}")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def require_match(label: str, pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if match is None:
        fail(f"{label} is missing")
    return match.group(1)


def wrapper_publication_claim(text: str) -> tuple[bool, str]:
    try:
        module = ast.parse(text, filename=str(WRAPPER_PATH))
    except SyntaxError as exc:
        fail(f"could not parse {WRAPPER_PATH.relative_to(ROOT)}: {exc}")
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "wrapper_info":
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Return) or not isinstance(child.value, ast.Dict):
                continue
            published_package: bool | None = None
            published_package_scope: str | None = None
            for key, value in zip(child.value.keys, child.value.values):
                if isinstance(key, ast.Constant) and key.value == "published_package":
                    if isinstance(value, ast.Constant) and isinstance(value.value, bool):
                        published_package = value.value
                        continue
                    fail("wrapper_info published_package must be a literal boolean")
                if isinstance(key, ast.Constant) and key.value == "published_package_scope":
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        published_package_scope = value.value
                        continue
                    fail("wrapper_info published_package_scope must be a literal string")
            if published_package is not None and published_package_scope is not None:
                return published_package, published_package_scope
    fail("wrapper_info must declare published_package and published_package_scope")


def parse_setup_cfg(text: str) -> tuple[str, str]:
    parser = configparser.ConfigParser()
    try:
        parser.read_string(text)
        version = parser["metadata"]["version"].strip()
        requirements = [line.strip() for line in parser["options"]["install_requires"].splitlines() if line.strip()]
    except (configparser.Error, KeyError) as exc:
        fail(f"could not parse setup.cfg release metadata: {exc}")
    witnessd_requirements = [item for item in requirements if item.startswith("witnessd")]
    if len(witnessd_requirements) != 1:
        fail("setup.cfg must declare exactly one witnessd requirement")
    return version, witnessd_requirements[0]


def parse_pyproject(text: str) -> tuple[str, str]:
    version = require_match("pyproject.toml project version", r'^version\s*=\s*"([^"]+)"$', text)
    match = re.search(r"^dependencies\s*=\s*(\[[\s\S]*?\])", text, flags=re.MULTILINE)
    if match is None:
        fail("pyproject.toml project dependencies are missing")
    try:
        dependencies = ast.literal_eval(match.group(1))
    except (SyntaxError, ValueError) as exc:
        fail(f"could not parse pyproject.toml project dependencies: {exc}")
    if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
        fail("pyproject.toml project dependencies must be a list of strings")
    witnessd_requirements = [item for item in dependencies if item.startswith("witnessd")]
    if len(witnessd_requirements) != 1:
        fail("pyproject.toml must declare exactly one witnessd requirement")
    return version, witnessd_requirements[0]


def repository_state() -> dict[str, Any]:
    pyproject = read_text(PYPROJECT_PATH)
    pyproject_version, pyproject_requirement = parse_pyproject(pyproject)
    setup_cfg_version, setup_cfg_requirement = parse_setup_cfg(read_text(SETUP_CFG_PATH))
    engine_lock = read_json(ENGINE_LOCK_PATH)
    manifest = read_json(RELEASE_MANIFEST_PATH)
    package_plan = read_json(PACKAGE_PLAN_PATH)
    witnessd_lock = engine_lock.get("witnessd")
    manifest_engines = manifest.get("engines")
    if not isinstance(witnessd_lock, dict):
        fail("engine-lock witnessd must be an object")
    if not isinstance(manifest_engines, dict) or not isinstance(manifest_engines.get("witnessd"), dict):
        fail("release manifest witnessd engine must be an object")
    witnessd_manifest = manifest_engines["witnessd"]
    published_package, published_package_scope = wrapper_publication_claim(read_text(WRAPPER_PATH))
    return {
        "pyproject_version": pyproject_version,
        "setup_cfg_version": setup_cfg_version,
        "pyproject_requirement": pyproject_requirement,
        "setup_cfg_requirement": setup_cfg_requirement,
        "published_package": published_package,
        "published_package_scope": published_package_scope,
        "engine_lock_witnessd_version": witnessd_lock.get("version"),
        "engine_lock_witnessd_ref": witnessd_lock.get("ref_name"),
        "manifest_witnessd_version": witnessd_manifest.get("version"),
        "package_plan_version": package_plan.get("source_version"),
        "package_plan_status": package_plan.get("status"),
        "package_plan_published_versions": package_plan.get("published_pypi_versions"),
        "package_plan_published_package": package_plan.get("published_package"),
        "package_plan_published_package_scope": package_plan.get("published_package_scope"),
        "docs": {str(path): read_text(ROOT / path) for path in DOC_PATHS},
    }


def version_tuple(label: str, value: Any) -> tuple[int, int, int]:
    if not isinstance(value, str) or VERSION_RE.fullmatch(value) is None:
        fail(f"{label} must be an X.Y.Z version")
    major, minor, patch = value.split(".")
    return int(major), int(minor), int(patch)


def minimum_witnessd_version(label: str, requirement: Any) -> tuple[int, int, int]:
    if not isinstance(requirement, str):
        fail(f"{label} must be a string")
    match = WITNESSD_REQUIREMENT_RE.fullmatch(requirement)
    if match is None:
        fail(f"{label} must be an exact witnessd>=X.Y.Z requirement")
    return version_tuple(label, match.group(1))


def validate_release_state(state: dict[str, Any]) -> None:
    package_version = state.get("pyproject_version")
    version_tuple("pyproject.toml version", package_version)
    if state.get("setup_cfg_version") != package_version:
        fail("setup.cfg version must match pyproject.toml version")
    if state.get("published_package") is not True:
        fail("wrapper_info published_package must be true")
    if state.get("published_package_scope") != "product-line":
        fail("wrapper_info published_package must be scoped to the product line")

    pyproject_minimum = minimum_witnessd_version("pyproject.toml witnessd requirement", state.get("pyproject_requirement"))
    setup_cfg_minimum = minimum_witnessd_version("setup.cfg witnessd requirement", state.get("setup_cfg_requirement"))
    if setup_cfg_minimum != pyproject_minimum:
        fail("setup.cfg witnessd requirement must match pyproject.toml")

    witnessd_version = state.get("engine_lock_witnessd_version")
    locked_witnessd = version_tuple("engine-lock witnessd version", witnessd_version)
    if locked_witnessd < pyproject_minimum:
        fail("engine-lock witnessd version must satisfy the package requirement")
    if state.get("engine_lock_witnessd_ref") != f"v{witnessd_version}":
        fail("engine-lock witnessd ref_name must match its version tag")
    if state.get("manifest_witnessd_version") != witnessd_version:
        fail("release manifest witnessd version must match the engine lock")

    if state.get("package_plan_version") != package_version:
        fail("wrapper package plan source_version must match the packaged version")
    if state.get("package_plan_status") != "release-candidate":
        fail("wrapper package plan status must be release-candidate")
    published_versions = state.get("package_plan_published_versions")
    if not isinstance(published_versions, list) or not published_versions:
        fail("wrapper package plan published_pypi_versions must be a non-empty list")
    for published_version in published_versions:
        version_tuple("wrapper package plan published PyPI version", published_version)
    if len(published_versions) != len(set(published_versions)):
        fail("wrapper package plan published_pypi_versions must not contain duplicates")
    if published_versions != sorted(published_versions, key=lambda value: version_tuple("published version", value)):
        fail("wrapper package plan published_pypi_versions must be ordered by version")
    if package_version in published_versions:
        fail("wrapper package plan must not claim the unreleased source version is published")
    if published_versions != list(PUBLISHED_PYPI_VERSIONS):
        fail("wrapper package plan published_pypi_versions must match the known PyPI release history")
    if state.get("package_plan_published_package") is not True:
        fail("wrapper package plan must record published_package true")
    if state.get("package_plan_published_package_scope") != "product-line":
        fail("wrapper package plan published_package must be scoped to the product line")

    docs = state.get("docs")
    if not isinstance(docs, dict) or not docs:
        fail("release-state docs must be a non-empty mapping")
    release_target_sentence = f"The post-release target state is: `orro` {package_version} is published on PyPI"
    for path, text in docs.items():
        if not isinstance(path, str) or not isinstance(text, str):
            fail("release-state docs must map path strings to text")
        normalized_text = " ".join(text.split())
        if release_target_sentence not in normalized_text:
            fail(f"{path} must state the post-release target {release_target_sentence!r}")
        for phrase in STALE_RELEASE_PHRASES:
            if phrase in text:
                fail(f"{path} contains stale release claim {phrase!r}")


def self_test() -> int:
    parsed_version, parsed_requirement = parse_pyproject(
        '[project]\nversion = "0.1.0"\ndependencies = [\n  "example>=1",\n  "witnessd>=2.4.0",\n]\n'
    )
    assert parsed_version == "0.1.0"
    assert parsed_requirement == "witnessd>=2.4.0"
    base: dict[str, Any] = {
        "pyproject_version": "0.2.0",
        "setup_cfg_version": "0.2.0",
        "pyproject_requirement": "witnessd>=2.4.0",
        "setup_cfg_requirement": "witnessd>=2.4.0",
        "published_package": True,
        "published_package_scope": "product-line",
        "engine_lock_witnessd_version": "2.4.0",
        "engine_lock_witnessd_ref": "v2.4.0",
        "manifest_witnessd_version": "2.4.0",
        "package_plan_version": "0.2.0",
        "package_plan_status": "release-candidate",
        "package_plan_published_versions": ["0.0.1", "0.0.2", "0.0.3", "0.1.0", "0.1.1"],
        "package_plan_published_package": True,
        "package_plan_published_package_scope": "product-line",
        "docs": {
            "README.md": (
                "The post-release target state is: `orro` 0.2.0 is published on PyPI. "
                "It becomes true only after Trusted Publishing completes."
            )
        },
    }
    validate_release_state(base)
    for label, key, value in (
        ("package version mismatch", "setup_cfg_version", "0.1.2"),
        ("unpublished wrapper claim", "published_package", False),
        ("ambiguous wrapper publication scope", "published_package_scope", "source-version"),
        ("unsatisfied witnessd lock", "engine_lock_witnessd_version", "2.3.3"),
        ("mutable witnessd ref", "engine_lock_witnessd_ref", "main"),
        ("manifest version mismatch", "manifest_witnessd_version", "2.3.2"),
        ("published package-plan status", "package_plan_status", "published"),
        ("package plan stale version", "package_plan_published_versions", ["0.0.x"]),
        (
            "invented published version",
            "package_plan_published_versions",
            ["0.0.1", "0.0.2", "0.0.3", "0.0.4", "0.1.0", "0.1.1"],
        ),
        ("missing published version", "package_plan_published_versions", ["0.0.1", "0.0.3", "0.1.0", "0.1.1"]),
        (
            "unreleased source listed as published",
            "package_plan_published_versions",
            ["0.0.1", "0.0.2", "0.0.3", "0.1.0", "0.1.1", "0.2.0"],
        ),
        (
            "ambiguous package-plan publication scope",
            "package_plan_published_package_scope",
            "source-version",
        ),
    ):
        forged = copy.deepcopy(base)
        forged[key] = value
        try:
            validate_release_state(forged)
        except ReleaseStateError:
            continue
        fail(f"self-test accepted forgery: {label}")
    forged_docs = copy.deepcopy(base)
    forged_docs["docs"]["README.md"] = "`orro` 0.2.0 is published on PyPI."
    try:
        validate_release_state(forged_docs)
    except ReleaseStateError:
        pass
    else:
        fail("self-test accepted a premature direct publication claim")
    forged_docs = copy.deepcopy(base)
    forged_docs["docs"]["README.md"] = "Only 0.0.x is live."
    try:
        validate_release_state(forged_docs)
    except ReleaseStateError:
        pass
    else:
        fail("self-test accepted stale release documentation")
    print("ORRO release state self-test: pass")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run built-in inconsistency rejection checks")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.self_test:
            return self_test()
        validate_release_state(repository_state())
    except ReleaseStateError as exc:
        print(f"ORRO release state violation: {exc}", file=sys.stderr)
        return 1
    print("ORRO release state: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
