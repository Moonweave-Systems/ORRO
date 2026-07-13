# ORRO Wrapper Distribution Smoke

Depone verifies; witnessd executes; ORRO exposes the workflow.

The wrapper distribution smoke verifies local wheel packaging before any package
publish. It is product/distribution test metadata, not proof, not verifier
truth, not package publish, not approval, and not assurance.

## Command

```bash
python3 scripts/check_orro_wrapper_distribution.py --json --allow-network
```

The checker builds a local wheel in a temporary workspace, installs that wheel
into a temporary virtual environment, and verifies the installed `orro` and
`orro-wrapper` console scripts. It creates a separate build environment, removes
any preinstalled `setuptools`, confirms the build backend is absent, and then
uses pip build isolation to provision the declared `setuptools>=61` requirement.
`--allow-network` explicitly authorizes that build-dependency bootstrap; it does
not authorize engine checkout mutation or package publication.

## Boundary

The distribution smoke verifies:

- the wheel contains `orro_wrapper` wrapper modules;
- the wheel does not contain Depone or witnessd Python packages;
- the wheel does not contain proofrun, proofcheck, scheduler, observer, fan-in,
  team-ledger, or verifier implementation files;
- the wheel exposes `orro` and `orro-wrapper`;
- the installed `orro-wrapper` boundary and self-test pass;
- explicit delegation works with a harmless Python command.

The checker does not call Depone or witnessd, does not run proofrun, does not run
proofcheck, does not run handoff, does not call live models, and does not call
MCP.

## Command Ownership

`orro-wrapper` is a compatibility alias. The ORRO-owned `orro` command delegates
to witnessd and must remain a thin wrapper surface.

The command migration contract is recorded in
`docs/orro-command-migration.md` and
`packaging/command-migration-plan.v0.json`. Distribution smoke must continue to
prove that both wrapper commands are installed by this package.

The command migration dry-run harness is
`scripts/check_orro_command_migration_dry_run.py`. It uses a temporary source
copy, verifies both wrapper command surfaces, and records rollback simulation
coverage. Dry-run metadata is not proof and does not publish a package.

## Scope

This is local distribution smoke only. It builds and installs a local wheel, but
it does not publish a package, upload artifacts, create a marketplace release,
or claim verifier truth.

Published ORRO package remains future work.
