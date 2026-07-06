# ORRO Wrapper Distribution Smoke

Depone verifies; witnessd executes; ORRO exposes the workflow.

The wrapper distribution smoke verifies local wheel packaging before any package
publish. It is product/distribution test metadata, not proof, not verifier
truth, not package publish, not approval, and not assurance.

## Command

```bash
python3 scripts/check_orro_wrapper_distribution.py --json
```

The checker builds a local wheel in a temporary workspace, installs that wheel
into a temporary virtual environment, and verifies the installed `orro-wrapper`
console script.

## Boundary

The distribution smoke verifies:

- the wheel contains `orro_wrapper` wrapper modules;
- the wheel does not contain Depone or witnessd Python packages;
- the wheel does not contain proofrun, proofcheck, scheduler, observer, fan-in,
  team-ledger, or verifier implementation files;
- the wheel exposes `orro-wrapper`;
- the wheel does not expose or shadow `orro`;
- the installed `orro-wrapper` boundary and self-test pass;
- explicit delegation works with a harmless Python command.

The checker does not call Depone or witnessd, does not run proofrun, does not run
proofcheck, does not run handoff, does not call live models, and does not call
MCP.

## Command Ownership

`orro-wrapper` is transitional. The current executable `orro` command remains
witnessd-hosted.

This package must not shadow `orro` yet. A future migration to an ORRO-owned
`orro` command requires a separate migration wave, compatibility plan, and
explicit checks that the witnessd-hosted command remains available during the
transition.

The plan-only migration contract is recorded in
`docs/orro-command-migration.md` and
`packaging/command-migration-plan.v0.json`. Until that future migration is
implemented, distribution smoke must continue to prove that only `orro-wrapper`
is installed by this package.

The command migration dry-run harness is
`scripts/check_orro_command_migration_dry_run.py`. It uses a temporary source
copy to simulate `orro = orro_wrapper.cli:main`, verifies both wrapper command
surfaces, and runs a rollback simulation that reinstalls the current
`orro-wrapper`-only shape. Dry-run metadata is not proof and does not publish or
transfer command ownership.

## Scope

This is local distribution smoke only. It builds and installs a local wheel, but
it does not publish a package, upload artifacts, create a marketplace release,
or claim verifier truth.

Published ORRO package remains future work.
