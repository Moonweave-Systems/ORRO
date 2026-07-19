# Thin Wrapper Plan

The post-release target state is: `orro` 0.2.11 is published on PyPI. It becomes
true only after `v0.2.11` is tagged and the Trusted-Publishing workflow completes;
until then, PyPI contains the ORRO product line through 0.2.10. The ORRO repository
is the canonical 0.2.11 source, whose metadata declares `witnessd>=2.4.0,<3.0.0`.

## Current State

- Depone verifies.
- witnessd executes.
- ORRO exposes the workflow.
- The ORRO-owned `orro` console script is the active command surface.
- `orro-wrapper` is a compatibility alias for the same thin wrapper module.
- The wrapper delegates through a subprocess to the witnessd-hosted engine
  command and contains no engine logic.
- This repository contains package metadata, docs, examples, bootstrap setup,
  locks, and smoke contracts.

## Wrapper Scope

The wrapper may:

- declare compatible witnessd package versions;
- reuse bootstrap setup/distribution orchestration for pinned engine checkouts;
- generate and check `orro-engine-lock.json`;
- expose one user-facing command surface;
- run e2e smoke checks against pinned engines;
- publish marketplace or plugin metadata in separately approved steps.

It must not:

- implement Depone verifier logic;
- implement witnessd runtime logic;
- duplicate proofcheck;
- duplicate proofrun, scheduler, observer, or team-lane execution;
- become a third engine.

The bootstrap is setup/distribution orchestration and setup metadata, not proof.
It contains no engine code, does not implement proofrun or proofcheck, and the
ORRO-owned executable `orro` command delegates to the witnessd-hosted engine
surface.

## Release Gate

Before a new package release, ORRO needs:

1. Stable engine version-lock policy.
2. Cross-engine e2e smoke coverage.
3. Packaging checks for local and pip installs.
4. Clear fallback when a pinned engine is unavailable.

Every release must preserve the engine boundary:

Depone verifies; witnessd executes; ORRO exposes the workflow.

The packaging decision is recorded in `docs/packaging-decision.md` and
`packaging/wrapper-package-plan.v0.json`. It is product metadata, not package
publish. It records the published package reality, the ORRO-owned command, the
`witnessd>=2.4.0,<3.0.0` dependency, and the requirement that the package contain no
engine code.

The pinned-engine fallback is recorded in `docs/pinned-engine-fallback.md` and
`packaging/pinned-engine-fallback-policy.v0.json`. Missing or mismatched engine
commits fail closed. Wrapper work must not silently use latest `main`, select an
alternate engine commit, or rewrite the lock outside an intentional update PR.

The thin package is documented in `docs/thin-wrapper.md`. Both `orro` and
`orro-wrapper` delegate through the same subprocess-based wrapper and do not
implement proofrun or proofcheck.

`scripts/check_orro_wrapper_install.py` installs the source into a temporary
virtual environment and verifies both commands without publishing a package,
calling Depone or witnessd, running proofrun, or running proofcheck. The result
is setup/test metadata, not proof, not verifier truth, not package publish, not
approval, and not assurance.

`scripts/check_orro_wrapper_distribution.py` builds and installs a local wheel,
verifies both command surfaces, and checks that the wheel contains no Depone or
witnessd packages or engine implementation files. The result is local test
metadata, not proof, not verifier truth, not package publish, not approval, and
not assurance.
