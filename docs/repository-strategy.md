# Repository Strategy

Current phase:

```text
Depone and witnessd remain separate engine repos.
ORRO repo is product/distribution/wrapper repo.
No engine code moves into this product/distribution repository.
```

Depone owns verifier semantics. witnessd owns execution runtime behavior. ORRO
owns the user-facing workflow, product docs, examples, distribution planning,
and e2e contracts.

The ORRO repository may contain product checkers, documentation, examples,
packaging drafts, engine-lock examples, local e2e smoke harnesses that call
engine commands through subprocess, and bootstrap setup planners that prepare or
check local engine checkouts. It must not contain Depone verifier logic,
witnessd runtime logic, proofrun/proofcheck implementations, scheduler,
observer, fan-in, team-ledger, or worker execution modules.

The e2e runner is a product smoke harness. It orchestrates local engine
checkouts and records test metadata, but it is not proof and is not an engine.

The bootstrap is setup/distribution orchestration and setup metadata, not proof.
It may help prepare pinned witnessd and Depone checkouts, but it contains no
engine code, does not verify evidence, does not approve merge, does not raise
assurance, and the current executable `orro` command delegates to the
witnessd-hosted engine surface.

The release manifest and compatibility matrix are product/distribution
metadata. They record which pinned engine pair has passed ORRO e2e CI, but they
are not proof, not verifier truth, not approval, and not assurance. Engine-lock
update process is intentional and PR-reviewed. The post-release target state is:
`orro` 0.2.16 is published on PyPI. It becomes true only after `v0.2.16` is tagged
and the Trusted-Publishing workflow completes; until then, PyPI contains the ORRO
product line through 0.2.15. This repository is the canonical 0.2.16 source.

The packaging decision in `docs/packaging-decision.md` and
`packaging/wrapper-package-plan.v0.json` is also product metadata, not package
publish. It keeps the current command source ORRO-owned and subprocess-delegated
to witnessd, declares `witnessd>=2.4.0,<3.0.0`, and requires the wrapper to contain no
engine code.

The wrapper distribution smoke builds and installs a local wheel to verify
package boundaries without publishing a new release. It is local test metadata,
not proof, and not package publish. It confirms both the ORRO-owned `orro`
command and the `orro-wrapper` compatibility alias are exposed.

`docs/orro-command-migration.md` and
`packaging/command-migration-plan.v0.json` record the completed
`owned-thin-wrapper` migration. The ORRO repository owns the `orro` console
script, which remains a thin subprocess delegation surface.

`scripts/check_orro_command_migration_dry_run.py` is allowed as a command
migration dry-run harness. It operates on a temporary source copy, simulates
`orro = orro_wrapper.cli:main`, checks thin wrapper behavior, and performs a
rollback simulation to the historical `orro-wrapper`-only package shape. Dry-run
metadata is not proof, not verifier truth, not package publish, and not actual
ORRO-owned `orro` command migration.

## Deferred Monorepo Conditions

Only consider a monorepo if:

- engine APIs stabilize
- release/version pin costs dominate
- e2e CI needs one repo
- packaging requires atomic multi-engine release

Those are future conditions, not current instructions. This repository must not
be used to merge engines by accident.
