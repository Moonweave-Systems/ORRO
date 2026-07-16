# ORRO Packaging Decision

Depone verifies; witnessd executes; ORRO exposes the workflow.

This document records the v0 packaging decision for the ORRO product repository.
It is product/distribution planning, not proof, not verifier truth, not package
publish, not merge approval, and not assurance. In short: not package publish.

## Decision

ORRO will remain product/distribution/wrapper only while Depone and witnessd
stay separate engine repositories.

Current command source is the ORRO-owned `orro` console script, which delegates
in-process to witnessd. The canonical publishable package is sourced from this
repository and declares `witnessd>=2.3.2`. In release-state terms, published ORRO package remains future work because PyPI upload is a separate step.

The package is a thin wrapper that delegates to the existing witnessd command
surface. It must contain no engine code.

## Allowed Packaging Scope

The ORRO repository may contain:

- pinned engine lock metadata;
- release manifest metadata;
- compatibility matrix metadata;
- bootstrap setup planner;
- e2e smoke runner that calls local engine checkouts;
- marketplace and plugin manifest drafts;
- thin wrapper code that delegates to engine commands.

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
2. Thin wrapper: install-smoke phase. `orro` and `orro-wrapper` may expose
   product onboarding and invoke witnessd-hosted ORRO commands, and local CI
   verifies the editable install and installed console scripts. They must not
   implement proofrun or proofcheck and must not imply package publish.
   The local wheel distribution smoke verifies that the built wheel exposes
   `orro` and `orro-wrapper`, and contains no engine packages or engine
   implementation files.
3. Published package: future phase. A package may be published only after
   pinned-engine e2e, boundary checks, bootstrap checks, and release metadata
   remain green.

4. Command ownership: current phase. `orro = orro_wrapper.cli:main` and
   `orro-wrapper = orro_wrapper.cli:main` are committed package metadata. Both
   command surfaces stay thin. Dry-run harness metadata is historical
   compatibility coverage only; it is not proof and does not publish a package.

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

The ORRO-owned `orro` command migration contract is recorded in
`docs/orro-command-migration.md` and
`packaging/command-migration-plan.v0.json`. The dry-run harness is compatibility
metadata only.
