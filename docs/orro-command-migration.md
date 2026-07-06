# ORRO Command Migration Plan

Depone verifies; witnessd executes; ORRO exposes the workflow.

This document defines the plan-only boundary for a future migration from the
current witnessd-hosted `orro` command to a future ORRO-owned `orro` command.
It is product/distribution planning, not proof, not verifier truth, not package
publish, not package publish metadata, not approval, and not assurance.

## Current State

- The executable `orro` command remains witnessd-hosted.
- The ORRO repository exposes `orro-wrapper` only.
- The ORRO package must not shadow `orro` in the current phase.
- `orro-wrapper` is transitional and delegates explicitly to the existing engine
  command.
- No ORRO-owned `orro` console script is added in this phase.

## Target State

A future ORRO-owned `orro` command may become the user-facing product command
only after a separate migration wave proves compatibility. That future command
must remain a product/distribution wrapper. It must not implement proofrun,
proofcheck, scheduler, observer, fan-in, team-ledger, verifier logic, or any
third engine behavior.

## Required Preconditions

Before ORRO can own the `orro` command, a migration PR must show:

1. `scripts/check_orro_wrapper_install.py --json` passes.
2. `scripts/check_orro_wrapper_distribution.py --json` passes.
3. Pinned-engine e2e passes.
4. Published-package preflight passes.
5. The release manifest and engine lock name the validated engine pair.
6. witnessd-hosted `orro` compatibility behavior is documented.
7. Rollback behavior is documented.

## Compatibility Requirements

The migration must preserve:

- witnessd as the execution engine;
- Depone as the verifier engine;
- existing ORRO workflow command semantics;
- proofcheck before handoff;
- report as summary, not proof;
- engine-lock as distribution metadata, not proof;
- Superflow as historical compatibility context only.

During migration, the ORRO-owned command must either delegate to the
witnessd-hosted command or preserve a documented compatibility path. It must not
silently replace engine behavior.

## Forbidden In This Phase

This phase must not:

- add `orro = ...` to `pyproject.toml` or `setup.cfg`;
- publish a package;
- shadow witnessd-hosted `orro`;
- move engine code into ORRO;
- implement proofrun;
- implement proofcheck;
- duplicate scheduler, observer, fan-in, team-ledger, or verifier logic;
- create a third engine;
- approve merge or raise assurance.

## Migration Gate

A future migration wave must add explicit tests that prove:

- installed package command ownership is intentional;
- `orro-wrapper` remains available or has a documented compatibility path;
- witnessd-hosted `orro` compatibility remains available during transition;
- pinned-engine e2e passes through the migrated command;
- scout-only and malformed artifact gates remain fail-closed;
- no command output turns reports, handoff, engine-lock, or release metadata into
  proof.

## Dry-Run Harness

`scripts/check_orro_command_migration_dry_run.py` is a dry-run harness for the
next compatibility wave. It builds the current package shape from a temporary
source copy and confirms that `orro-wrapper` exists while `orro` is absent.

The same harness then creates another temporary source copy, adds only the
simulated entry point `orro = orro_wrapper.cli:main`, and verifies that both
`orro` and `orro-wrapper` are thin wrapper surfaces. Both commands must emit
non-engine boundary metadata and pass a harmless delegation smoke.

The dry-run harness finishes with a rollback simulation: it reinstalls the
current package shape and confirms that `orro` is absent again. This is
compatibility metadata only: dry-run metadata is not proof, not verifier truth,
not package publish, and not command ownership.

## Rollback

Rollback must be possible without changing Depone verifier semantics or
witnessd execution semantics. If ORRO-owned `orro` causes command confusion or
engine mismatch, users must be able to return to the witnessd-hosted command and
rerun pinned-engine checks.

The rollback plan is product/distribution metadata only. It is not proof and
does not verify evidence.
