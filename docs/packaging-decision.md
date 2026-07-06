# ORRO Packaging Decision

Depone verifies; witnessd executes; ORRO exposes the workflow.

This document records the v0 packaging decision for the ORRO product repository.
It is product/distribution planning, not proof, not verifier truth, not package
publish, not merge approval, and not assurance. In short: not package publish.

## Decision

ORRO will remain product/distribution/wrapper only while Depone and witnessd
stay separate engine repositories.

Current command source remains the witnessd-hosted `orro` console script.
Published ORRO package remains future work. The canonical packaging rule is:
published ORRO package remains future work.

The next package shape, when implemented, should be a thin wrapper that prepares
or locates pinned engine checkouts and delegates to the existing engine command
surface. It must contain no engine code.

## Allowed Packaging Scope

The ORRO repository may contain:

- pinned engine lock metadata;
- release manifest metadata;
- compatibility matrix metadata;
- bootstrap setup planner;
- e2e smoke runner that calls local engine checkouts;
- marketplace and plugin manifest drafts;
- future thin wrapper code that delegates to engine commands.

The ORRO repository must not contain:

- Depone verifier implementation;
- witnessd runtime implementation;
- proofcheck implementation;
- proofrun implementation;
- scheduler, observer, fan-in, team-lane, or team-ledger engine logic;
- a third engine.

## Phase Model

1. Bootstrap: current phase. `scripts/bootstrap_orro.py` prepares or checks
   local pinned engine checkouts. Bootstrap output is setup metadata, not proof.
2. Thin wrapper: install-smoke phase. `orro-wrapper` may expose product
   onboarding and invoke witnessd-hosted ORRO commands, and local CI verifies
   the editable install and installed console script. It must not implement
   proofrun or proofcheck, must not shadow the witnessd-hosted `orro` command,
   and must not imply package publish.
   The local wheel distribution smoke verifies that the built wheel exposes
   `orro-wrapper`, does not expose or shadow `orro`, and contains no engine
   packages or engine implementation files.
3. Published package: future phase. A package may be published only after
   pinned-engine e2e, boundary checks, bootstrap checks, and release metadata
   remain green.

## Release Gate

Before executable wrapper code is added, a PR must show:

- `engine-lock/orro-e2e-engine-lock.json` is current;
- `release/orro-release-manifest.v0.json` matches the engine lock;
- `docs/compatibility-matrix.md` records the validated engine pair;
- `scripts/check_orro_repo_contract.py` passes;
- `scripts/check_orro_packaging_decision.py` passes;
- pinned-engine e2e remains green;
- wrapper install smoke remains green;
- wrapper distribution smoke remains green;
- no engine code is added.

## Trust Boundary

Package metadata does not verify evidence. Engine-lock match does not prove a
task. Bootstrap receipts do not prove a task. E2E smoke results are test
metadata, not verifier truth.

Depone proofcheck remains the verifier path. witnessd remains the execution
runtime. ORRO exposes the workflow and packaging surface.

Future migration to an ORRO-owned `orro` command requires a separate migration
wave. Until then, the current executable `orro` command remains witnessd-hosted.
