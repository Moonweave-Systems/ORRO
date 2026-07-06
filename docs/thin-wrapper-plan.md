# Thin Wrapper Plan

The current `orro` command is implemented and hosted by witnessd. This ORRO
repository prepares the product and distribution layer that can eventually make
ORRO feel like one install while keeping the engines separate.

## Current State

- Depone verifies.
- witnessd executes.
- ORRO exposes the workflow.
- The witnessd-hosted `orro` console script is the active command surface.
- This repository contains docs, examples, packaging drafts, bootstrap setup
  planning, and smoke-contract planning only.

## Future Wrapper Scope

A future wrapper may:

- install or pin compatible witnessd and Depone versions;
- reuse bootstrap setup/distribution orchestration for pinned engine checkouts;
- generate and check `orro-engine-lock.json`;
- expose one user-facing command surface;
- run e2e smoke checks against pinned engines;
- publish marketplace or plugin metadata.

It must not:

- implement Depone verifier logic;
- implement witnessd runtime logic;
- duplicate proofcheck;
- duplicate proofrun, scheduler, observer, or team-lane execution;
- become a third engine.

The current bootstrap is setup/distribution orchestration and setup metadata,
not proof. It contains no engine code, does not implement proofrun or
proofcheck, and the executable `orro` command remains witnessd-hosted.

## Release Gate

Before adding executable wrapper code here, ORRO needs:

1. Stable engine version-lock policy.
2. Cross-engine e2e smoke runner.
3. Packaging decision for local, pip, and marketplace installs.
4. Clear fallback when a pinned engine is unavailable.

Any wrapper code must preserve the engine boundary:

Depone verifies; witnessd executes; ORRO exposes the workflow.

The v0 packaging decision is now recorded in `docs/packaging-decision.md` and
`packaging/wrapper-package-plan.v0.json`. It is product metadata, not package
publish, and keeps the current command source witnessd-hosted until a future
thin wrapper is explicitly implemented.

The pinned-engine fallback is now recorded in
`docs/pinned-engine-fallback.md` and
`packaging/pinned-engine-fallback-policy.v0.json`. It requires fail-closed
behavior when pinned engine commits are missing or mismatched. Future wrapper
work must not silently use latest `main`, auto-select alternate engine commits,
or rewrite the engine lock outside an intentional engine-lock update PR.
