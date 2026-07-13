# ORRO Command Migration

Depone verifies; witnessd executes; ORRO exposes the workflow.

The command migration is now in the `owned-thin-wrapper` phase. The ORRO
package owns the user-facing `orro` console script and keeps `orro-wrapper` as a
compatibility command. Both commands use the same thin wrapper module.

This migration is product/distribution metadata and a command-surface change.
It is not proof, not verifier truth, not package publish, not approval, and not
assurance.
ORRO command ownership does not verify evidence; Depone verifies persisted
evidence bytes.

## Current State

- `orro` is an ORRO-owned console script.
- `orro-wrapper` remains available for compatibility.
- ORRO-owned `orro` delegates to witnessd; it does not implement engine logic.
- Depone remains the verifier.
- witnessd remains the execution engine and owns role-lane scheduling.

## Boundary

The ORRO command may own product config, doctor, report, and workflow command
names. It must delegate engine behavior to witnessd and must not implement
proofrun, proofcheck, scheduler, observer, fan-in, team-ledger, verifier logic,
or any third engine behavior.

The default delegation target is `python -m orro`. Operators may
override that target with `--engine-command` or `ORRO_ENGINE_COMMAND` for
compatibility smoke tests and controlled local installs.

## Compatibility

`orro-wrapper` remains a thin compatibility alias for the same wrapper module.
The wrapper can still run `boundary`, `self-test`, and explicit `delegate`
commands without invoking engine repositories.

The clean install and wheel distribution checks prove command ownership only:
they verify that both `orro` and `orro-wrapper` are installed, that both expose
the non-engine boundary, and that harmless explicit delegation works. They do
not verify evidence and do not publish a package.

## Dry-Run Harness

`scripts/check_orro_command_migration_dry_run.py` remains as the dry-run harness
for historical compatibility coverage from the former plan-only wave. Its
dry-run metadata is not proof. The committed package metadata is now the source
of command ownership truth for this repo.
The historical harness still documents its temporary source copy and rollback simulation behavior so older compatibility evidence remains interpretable.

## Rollback

Rollback must not change Depone verifier semantics or witnessd execution
semantics. If an ORRO-owned command install is faulty, operators can invoke the
witnessd-hosted surface directly with `python -m orro ...` while the
ORRO package metadata is fixed.

Superflow remains historical compatibility context only; it is not an engine
implementation inside ORRO.
