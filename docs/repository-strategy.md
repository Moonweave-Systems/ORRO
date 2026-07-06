# Repository Strategy

Current phase:

```text
Depone and witnessd remain separate engine repos.
ORRO repo is product/distribution/wrapper repo.
No engine code moves in this skeleton wave.
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
assurance, and the current executable `orro` command remains witnessd-hosted.

The release manifest and compatibility matrix are product/distribution
metadata. They record which pinned engine pair has passed ORRO e2e CI, but they
are not proof, not verifier truth, not approval, and not assurance. Engine-lock
update process is intentional and PR-reviewed. Published ORRO package remains
future work.

The packaging decision in `docs/packaging-decision.md` and
`packaging/wrapper-package-plan.v0.json` is also product metadata, not package
publish. It keeps the current command source witnessd-hosted and requires any
future wrapper to contain no engine code.

The wrapper distribution smoke builds and installs a local wheel to verify
package boundaries before publish. It is local test metadata, not proof, and not
package publish. It confirms `orro-wrapper` is exposed while the current `orro`
command remains witnessd-hosted. Future migration to an ORRO-owned `orro`
command requires a separate migration wave.

## Deferred Monorepo Conditions

Only consider a monorepo if:

- engine APIs stabilize
- release/version pin costs dominate
- e2e CI needs one repo
- packaging requires atomic multi-engine release

Those are future conditions, not current instructions. This repository must not
be used to merge engines by accident.
